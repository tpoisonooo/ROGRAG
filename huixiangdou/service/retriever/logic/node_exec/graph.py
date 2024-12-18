from ...base import LogicNode, RetrieveResource, RetrieveReply, OpSession, OpExecutor, graph_elems_to_chunks
from .....primitive import Faiss, Direction, Query, Edge
from ....prompt import reason_prompts as PROMPTS
from ....sql import ChunkSQL
from ..node_param import GetSPONode
from ...knowledge import KnowledgeRetriever
from loguru import logger
from typing import List
from functools import partial
from typing import Iterator
import pdb
import json
import os

class GraphExecutor(OpExecutor):
    def __init__(self, resource: RetrieveResource, work_dir: str, chunkDB: ChunkSQL):
        super().__init__(resource)
        self.DENSE_THRESHOLD = 0.2
        self.entityDB = Faiss.load_local(os.path.join(work_dir, 'db_kag_entity'))
        self.relationDB = Faiss.load_local(os.path.join(work_dir, 'db_kag_relation'))
        self.chunkDB = chunkDB

    def is_this_op(self, logic_node: LogicNode) -> bool:
        return isinstance(logic_node, GetSPONode)
    
    def similar_entity(self, entity: str):
        results = self.entityDB.similarity_search(embedder=self.resource.embedder, query=Query(text=entity), threshold=self.DENSE_THRESHOLD)
        if results:
            # {'_hash': '4d68fb', 'content_or_path': '黄新占/丰华占黄新占/丰华占是黄华占的亲本。', 'metadata': {'entity_name': '黄新占/丰华占', 'entity_type': 'EVENT'}, 'modal': 'text'}
            return results[0][0].metadata['entity_name']
        raise Exception(f'similarity search entity fail {entity}')

    def similar_relation(self, relation: str):
        results = self.relationDB.similarity_search(embedder=self.resource.embedder, query=Query(text=relation), threshold=self.DENSE_THRESHOLD)
        if results:
            return results[0][0].content_or_path
        raise Exception(f'similarity search relation fail {relation}')
        
    def filter_edges(self, keyword:str, edge_iter: Iterator[Edge]) -> List[Edge]:
        texts = []
        edges = []
        for edge in edge_iter:
            edges.append(edge)
            texts.append(edge.triplet()[1])
            
        if not keyword:
            return edges
        if not texts:
            return []

        rerank_indexes = self.resource.reranker._sort(texts=texts, query=keyword).tolist()
        keep_edges = []
        
        for index in rerank_indexes:
            score = self.resource.embedder.distance(keyword, texts[index])
            if score < self.DENSE_THRESHOLD:
                break
            keep_edges.append(edges[index])
        return keep_edges

    # def upsert_evidence(self, logic_node: LogicNode, op_sess: OpSession, e: Edge):
    #     # pdb.set_trace()
    #     chunk_ids = e.props.get('source_id').split(GRAPH_FIELD_SEP)
    #     for chunk_id in chunk_ids:
    #         if chunk_id not in op_sess.evidence_chunks:
    #             op_sess.evidence_chunks[chunk_id] = self.chunkDB.get(_hash=chunk_id)
        
    #     op_sess.evidence_strs.append({'sub_query':logic_node.sub_query, 'desc': e.props.get('description')})
    
    async def run(self, logic_node: LogicNode, op_sess: OpSession):
        params = op_sess.param
        # s/o entity query + p relation query
        # 
        # 如果 spo 具备 entity name，查询
        # 如果 spo 只有 symbol，复制

        # setup or fetch subjective
        s_alias = logic_node.s.alias_name
        s_entity = logic_node.s.entity_name
        if s_alias not in op_sess.param and s_entity:
            op_sess.param[s_alias] = s_entity
        elif s_entity is None:
            s_entity = op_sess.param.get(s_alias, None)
            logger.debug(f'load {s_alias} {s_entity}')

        # setup or fetch objective
        o_alias = logic_node.o.alias_name
        o_entity = logic_node.o.entity_name
        if o_alias not in op_sess.param and o_entity:
            op_sess.param[o_alias] = o_entity
        elif o_entity is None:
            o_entity = op_sess.param.get(o_alias, None)
            logger.debug(f'load {o_alias} {o_entity}')
        
        # process alias
        p_type = logic_node.p.get_entity_type_str() if logic_node.p else None
        
        p_alias = logic_node.p.alias_name
        if p_alias not in op_sess.param and p_type:
            op_sess.param[p_alias] = p_type
        elif p_type is None:
            p_type = op_sess.param.get(p_alias, None)
            logger.debug(f'load {p_alias} {p_type}')
            
        if type(p_type) is list or type(s_entity) is list or type(o_entity) is list:
            pdb.set_trace()
            pass
        
        async def upsert(alias:str, refs: List):
            sub_query = logic_node.sub_query.strip()
            root_query = logic_node.root_query.strip()
            sub_answer = None
            # if sub_query.endswith('?') or sub_query.endswith('？'):
            # chat
            chunks = graph_elems_to_chunks(refs, self.chunkDB)
            chunkstr = '\n'.join(c.content_or_path for c in chunks)
            step_text = json.dumps(op_sess.evidence_strs, ensure_ascii=False)
            prompt = PROMPTS['naive_qa']['zh_cn'].format(references=chunkstr, sub_query=sub_query, root_query=root_query, step_text=step_text)
            sub_answer = await self.resource.llm.chat(prompt)
            op_sess.param[alias] = sub_answer
            op_sess.upsert_evidence(sub_query=logic_node.sub_query, alias=alias, sub_answer=sub_answer, items=refs)
        
        graph = self.resource.graph_store
        if s_entity and o_entity:
            # only relation
            # fetch subjective and objective and assign
            s_sim = self.similar_entity(entity=s_entity)
            o_sim = self.similar_entity(entity=o_entity)
            edge_iter = await graph.get_connections(sid=s_sim, tid=o_sim)
            
            edges = self.filter_edges(keyword=p_type, edge_iter=edge_iter)
            if not p_type:
                upsert(alias=p_alias, refs=edges)

        if not s_entity and not o_entity and p_type:
            rel_sim = self.similar_relation(relation=p_type)
            if not rel_sim:
                return None
            
            s_edge, o_edge = await graph.get_nodes_by_edge(edge_name=rel_sim)
            if not s_edge or not o_edge:
                raise Exception(f'spo retrieval fail {rel_sim}')
                return None
            await upsert(alias=s_alias, refs=[s_edge])
            await upsert(alias=o_alias, refs=[o_edge])
            return None
        
   
        node_name = None
        if s_entity:
            node_name = s_entity
        elif o_entity:
            node_name = o_entity
        
        node_sim = self.similar_entity(entity=node_name)
        edge_iter = await graph.get_neighbor_edges(vid=node_sim, direction=Direction.BOTH)
        edges = self.filter_edges(keyword=p_type, edge_iter=edge_iter)
        
        # update params
        alias = s_alias if not s_entity else o_alias
        await upsert(alias=alias, refs=edges)
        return None