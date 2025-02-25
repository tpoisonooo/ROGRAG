"""Pipeline."""
import asyncio
import json
import pytoml
import pdb
from typing import List, Union, AsyncGenerator
from ..primitive import Query, Pair
from .session import Session
from ..service import SharedRetrieverPool, Retriever, RetrieveResource, ErrorCode
from ..service.retriever import RetrieveMethod
from ..service.prompt import rag_prompts as PROMPTS


class PreprocNode:

    def __init__(self, resource: RetrieveResource):
        self.resource = resource

    async def process(self, sess: Session) -> AsyncGenerator[Session, Session]:

        assert isinstance(sess.history, list), "sess.history 数据结构错误"

        if len(sess.history) > 0:
            yield sess
            return

        # check input
        if sess.query.text is None or len(sess.query.text) < 2:
            sess.code = ErrorCode.QUESTION_TOO_SHORT
            yield sess
            return

        #intention && topic analysis
        prompt = PROMPTS['extract_topic_intention'][sess.language].format(
            input_text=sess.query.text)
        json_str = await self.resource.llm.chat(prompt=prompt)
        sess.logger.info(f'{__file__} {json_str}')
        try:
            if json_str.startswith('```json'):
                json_str = json_str[len('```json'):]

            if json_str.endswith('```'):
                json_str = json_str[0:-3]

            json_obj = json.loads(json_str)
            intention = json_obj['intention']
            if intention is not None:
                intention = intention.lower()
            else:
                intention = 'undefine'
            topic = json_obj['topic']
            if topic is not None:
                topic = topic.lower()
            else:
                topic = 'undefine'

            for block_intention in ['问候', 'greeting', 'undefine']:
                if block_intention in intention:
                    sess.code = ErrorCode.NOT_A_QUESTION
                    yield sess
                    return

            for block_topic in ['身份', 'identity', 'undefine']:
                if block_topic in topic:
                    sess.code = ErrorCode.NOT_A_QUESTION
                    yield sess
                    return

        except Exception as e:
            sess.logger.error(str(e))


class ReduceGenerate:

    def __init__(self, resource: RetrieveResource):
        self.resource = resource

    async def process(self, sess: Session) -> AsyncGenerator[Session, Session]:
        prompt = None
        real_question = sess.query.generation_question if sess.query.generation_question else sess.query.text

        if len(sess.retrieve_replies) < 1:
            # direct chat
            prompt = real_question
        else:
            sess.stage = "2_rerank"
            yield sess
            sess.fused_reply = Retriever.fuse(replies=sess.retrieve_replies,
                                              query=sess.query,
                                              resource=self.resource)

            prompt = sess.fused_reply.format_prompt(query=real_question,
                                                    language=sess.language)

        sess.stage = "3_generate"
        yield sess

        response = ""
        if sess.response_type == 'stream':
            async for delta in self.resource.llm.chat_stream(
                    prompt=prompt,
                    history=sess.history,
                    system_prompt=sess.response_system):
                sess.delta = delta
                response += delta
                yield sess
            sess.response = response
            sess.delta = ''
            yield sess
        else:
            sess.response = await self.resource.llm.chat(prompt=prompt,
                                                         history=sess.history)
            yield sess
        print(real_question)
        print(response)


class ParallelPipeline:

    def __init__(self,
                 work_dir: str = 'workdir',
                 config_path: str = 'config.ini'):
        self.resource = RetrieveResource(config_path)
        self.pool = SharedRetrieverPool(resource=self.resource)
        self.retriever_knowledge = self.pool.get(
            work_dir=work_dir, method=RetrieveMethod.KNOWLEDGE)
        self.retriever_web = self.pool.get(work_dir=work_dir,
                                           method=RetrieveMethod.WEB)
        self.config_path = config_path
        self.work_dir = work_dir
        
        with open(config_path) as f:
            self.threshold = pytoml.load(f)['store']['reject_threshold']

    async def generate(self,
                       query: Union[Query, str],
                       history: List[Pair] = [],
                       request_id: str = 'default',
                       language: str = 'zh_cn'):
        if type(query) is str:
            query = Query(text=query)

        # build input session
        sess = Session(query=query,
                       history=history,
                       request_id=request_id,
                       language=language)
        sess.stage = "0_parse"
        yield sess

        # build pipeline
        preproc = PreprocNode(self.resource)
        reduce = ReduceGenerate(self.resource)

        direct_chat_states = [
            ErrorCode.QUESTION_TOO_SHORT, ErrorCode.NOT_A_QUESTION
        ]

        # if not a good question, return
        direct_chat = False
        async for sess in preproc.process(sess):
            if sess.code in direct_chat_states:
                direct_chat = True
                break
            
        score = await self.retriever_knowledge.similarity_score(query=query)
        sess.logger.info('simliarity score {}'.format(score))
        if score < self.threshold:
            direct_chat = True

        if direct_chat:
            async for resp in reduce.process(sess):
                yield resp
            return

        sess.stage = "1_search"
        yield sess

        # parallel run text2vec, websearch and codesearch
        tasks = [self.retriever_knowledge.explore(query=sess.query)]
        if query.enable_web_search:
            tasks.append(self.retriever_web.explore(query=sess.query))

        sess.retrieve_replies = await asyncio.gather(*tasks,
                                                     return_exceptions=True)
        async for sess in reduce.process(sess):
            yield sess
