"""Pipeline."""
import argparse
import asyncio
import json
import pdb
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
        
        if len(sess.history) > 0 :
            yield sess
            return
        
        # check input
        if sess.query.text is None or len(sess.query.text) < 2:
            sess.code = ErrorCode.QUESTION_TOO_SHORT
            yield sess
            return
        
        #intention && topic analysis
        prompt = PROMPTS['extract_topic_intention'][sess.language].format(input_text=sess.query.text)
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
            sess.fused_reply = Retriever.fuse(replies=sess.retrieve_replies, query=sess.query, resource=self.resource)
            prompt = sess.fused_reply.format(query=real_question, language=sess.language)

        sess.stage = "3_generate"
        yield sess
        
        sess.response = await self.resource.llm.chat(prompt=prompt, history=sess.history)
        yield sess

class PPLCheck:
    def __init__(self, resource: RetrieveResource):
        self.resource = resource

    async def process(self, sess: Session) -> AsyncGenerator[Session, bool]:
        prompt = None
        real_question = sess.query.generation_question if sess.query.generation_question else sess.query.text
        prompt = PROMPTS['perplexsity_check'][sess.language].format(input_query=real_question, input_evidence=str(sess.fused_reply), input_response=sess.response)
        ppl = await self.resource.llm.chat(prompt=prompt, history=sess.history)

        with open('ppl.txt', 'a') as f:
            f.write(f'ppl check\n real_question:{real_question} \n evidence:{sess.fused_reply} \n response:{sess.response} \n ppl:{ppl}')
            f.write('\n' + '@' * 32 + '\n') 
            f.write('\n')
        if 'yes' in ppl.lower():
            return True
        return False

class SerialPipeline:

    def __init__(self, work_dir: str='workdir', config_path: str='config.ini'):
        self.resource = RetrieveResource(config_path)
        self.pool = SharedRetrieverPool(resource=self.resource)
        self.retriever_reason = self.pool.get(work_dir=work_dir, method=RetrieveMethod.REASON)
        self.retriever_knowledge = self.pool.get(work_dir=work_dir, method=RetrieveMethod.KNOWLEDGE)
        self.retriever_web = self.pool.get(work_dir=work_dir, method=RetrieveMethod.WEB)
        self.retriever_bm25 = self.pool.get(work_dir=work_dir, method=RetrieveMethod.BM25)
        self.retriever_inverted = self.pool.get(work_dir=work_dir, method=RetrieveMethod.INVERTED)
        
        self.config_path = config_path
        self.work_dir = work_dir

    async def generate(self,
                 query: Union[Query, str],
                 history: List[Pair]=[],
                 request_id: str='default',
                 language: str='zh_cn'):
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
        async for sess in preproc.process(sess):
            if sess.error in direct_chat_states:
                async for resp in reduce.process(sess):
                    yield resp
                return

        # for expert question, retrieval and response
        sess.stage = "1_search"
        yield sess
        
        run_graphrag = False
        try:
            sess.retrieve_replies = [await self.retriever_reason.explore(query=sess.query)]
            async for sess in reduce.process(sess):
                if sess.response:
                    success = await ppl.process(sess)
                    if success:
                        sess.node = 'retriever_reason'
                        yield sess
                        break
                    run_graphrag = True

        except Exception as e:
            logger.error(str(e) + f"{__file__}")
            run_graphrag = True
        
        if run_graphrag:
            sess.retrieve_replies = [await self.retriever_knowledge.explore(query=sess.query)]
            sess.node = 'retriever_knowledge'
            async for sess in reduce.process(sess):
                yield sess
        return
