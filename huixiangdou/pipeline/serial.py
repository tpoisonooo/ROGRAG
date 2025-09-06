"""Pipeline."""
import asyncio
import json
import pdb
import pytoml
from typing import List, Union, AsyncGenerator

from loguru import logger

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

    async def process(self, sess: Session,
                      node: str) -> AsyncGenerator[Session, Session]:
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

        if sess.response_type == 'stream':
            response = ""
            async for delta in self.resource.llm.chat_stream(
                    prompt=prompt,
                    history=sess.history,
                    system_prompt=sess.response_system):
                sess.delta = delta
                response += delta
                yield sess
            sess.delta = ''
            sess.response = response
            yield sess
        else:
            sess.response = await self.resource.llm.chat(prompt=prompt,
                                                         history=sess.history)
            yield sess

        # sess.debug[node] = {
        #     "prompt": prompt,
        #     "token_len": len(encode_string(prompt)),
        #     "response": sess.response
        # }
        print(real_question)
        print(response)
        yield sess


class PPLCheck:

    def __init__(self, resource: RetrieveResource):
        self.resource = resource

    async def process(self,
                      sess: Session,
                      mode='following') -> AsyncGenerator[Session, bool]:
        prompt = None

        if 'following' == mode:
            prompt = PROMPTS['perplexsity_check_following'][
                sess.language].format(
                    input_query=sess.query.text,
                    input_evidence=sess.fused_reply.format_prompt(
                        language=sess.language),
                    input_response=sess.response)
        else:
            prompt = PROMPTS['perplexsity_check_preceding'][
                sess.language].format(
                    input_query=sess.query.text,
                    input_evidence=sess.fused_reply.format_evidence(
                        language=sess.language))

        ppl = await self.resource.llm.chat(prompt=prompt, history=sess.history)

        # with open('ppl.txt', 'a') as f:
        #     f.write(f'ppl check\n query.text:{sess.query.text} \n evidence:{sess.fused_reply} \n response:{sess.response} \n ppl:{ppl}')
        #     f.write('\n' + '@' * 32 + '\n')
        #     f.write('\n')
        # if not 'YES' in ppl:
        #     pdb.set_trace()
        #     pass
        sess.debug['ppl'] = ppl
        if 'YES' in ppl:
            return True
        return False


class SerialPipeline:

    def __init__(self,
                 work_dir: str = 'workdir',
                 config_path: str = 'config.ini'):
        self.resource = RetrieveResource(config_path)
        self.pool = SharedRetrieverPool(resource=self.resource)
        self.retriever_reason = self.pool.get(work_dir=work_dir,
                                              method=RetrieveMethod.REASON)
        self.retriever_knowledge = self.pool.get(
            work_dir=work_dir, method=RetrieveMethod.KNOWLEDGE)
        self.retriever_web = self.pool.get(work_dir=work_dir,
                                           method=RetrieveMethod.WEB)
        # self.retriever_bm25 = self.pool.get(work_dir=work_dir, method=RetrieveMethod.BM25)
        # self.retriever_inverted = self.pool.get(work_dir=work_dir, method=RetrieveMethod.INVERTED)

        self.config_path = config_path
        self.work_dir = work_dir
        
        # utf-8
        with open(config_path,'r', encoding='utf-8') as f:
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
        ppl = PPLCheck(self.resource)

        direct_chat_states = [
            ErrorCode.QUESTION_TOO_SHORT, ErrorCode.NOT_A_QUESTION
        ]

        # if not a good simple question, return
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
                async for resp in reduce.process(sess,
                                                 node='retriever_direct'):
                    yield resp
                return

        # for expert question, retrieval and response
        sess.stage = "1_search"
        yield sess

        run_graphrag = False
        try:
            sess.retrieve_replies = [
                await self.retriever_reason.explore(query=sess.query)
            ]
            sess.fused_reply = Retriever.fuse(replies=sess.retrieve_replies,
                                              query=sess.query,
                                              resource=self.resource)

            success = await ppl.process(sess, mode='preceding')
            if success:
                async for _sess in reduce.process(sess,
                                                  node='retriever_reason'):
                    yield _sess

        except Exception as e:
            logger.error(str(e) + f"{__file__}")
            run_graphrag = True

        if run_graphrag:
            tasks = [self.retriever_knowledge.explore(query=sess.query)]
            if query.enable_web_search:
                tasks.append(self.retriever_web.explore(query=sess.query))
            sess.retrieve_replies = await asyncio.gather(
                *tasks, return_exceptions=True)

            async for sess in reduce.process(sess, node='retriever_knowledge'):
                yield sess
        return
