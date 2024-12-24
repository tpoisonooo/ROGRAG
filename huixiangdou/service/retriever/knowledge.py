from ...primitive import Faiss, Query, Chunk, MemoryGraph, Direction
from ..graph_store import GraphStore
from loguru import logger
from typing import List, Union, Any, Tuple
from ..sql import ChunkSQL
from .base import Retriever, RetrieveResource, RetrieveReply
from ..prompt import graph_prompts as PROMPTS 
from ..prompt import GRAPH_FIELD_SEP
from ..nlu import split_string_by_multi_markers, truncate_list_by_token_size

import os
import json
import asyncio
import pdb

class KnowledgeRetriever(Retriever):
    def __init__(self, resource:RetrieveResource, work_dir: str) -> None:
        super().__init__()
        """Init with model device type and config."""
        self.embedder = resource.embedder
        self.llm = resource.llm
        self.work_dir = work_dir
        self.entityDB = Faiss.load_local(os.path.join(work_dir, 'db_kag_entity'))
        self.relationDB = Faiss.load_local(os.path.join(work_dir, 'db_kag_relation'))
        self.DENSE_THRESHOLD = 0.2
        self.HIGHLEVEL_DENSE_TOPK = 5
        self.LOWLEVEL_DENSE_TOPK = 6
        self.chunkDB = ChunkSQL(file_dir=os.path.join(work_dir, 'db_chunk'))
        self.graph_store = resource.graph_store

        if not os.path.exists(work_dir):
            logger.warning('!!!warning, workdir not exist.!!!')
            return

    def combine_contexts(self, high_level_context: RetrieveReply, low_level_context: RetrieveReply) -> RetrieveReply:
        # Function to extract entities, relationships, and sources from context strings
        
        def process_combine_contexts(hl: List[Any], ll: List[Any], hash_func:callable) -> List[List[str]]:
            keys = set()
            rets = []
            for item in hl:
                key = hash_func(item)
                if key in keys:
                    continue
                keys.add(key)
                rets.append(item)
                
            for item in ll:
                key = hash_func(item)
                if key in keys:
                    continue
                keys.add(key)
                rets.append(item)
            return rets
        
        nodes = process_combine_contexts(hl=high_level_context.nodes, ll=low_level_context.nodes, hash_func=lambda x:x[0])
        relations = process_combine_contexts(hl=high_level_context.relations, ll=low_level_context.relations, hash_func=lambda x:x[0]+x[1])
        sources = process_combine_contexts(hl=high_level_context.sources, ll=low_level_context.sources, hash_func=lambda x:x._hash)
        r = RetrieveReply(nodes=nodes, relations=relations, sources=sources)
        return r
    
    async def _find_most_related_text_unit_from_entities(
        self,
        node_datas: list[dict],
        query_param: Query,
        text_chunks_db: ChunkSQL,
        knowledge_graph_inst: MemoryGraph,
    ):
        text_units = [
            split_string_by_multi_markers(dp["source_id"], [GRAPH_FIELD_SEP])
            for dp in node_datas
        ]
        edges = await asyncio.gather(
            *[knowledge_graph_inst.get_neighbor_edges(dp["entity_name"]) for dp in node_datas]
        )
        all_one_hop_nodes = set()
        for this_edges in edges:
            if not this_edges:
                continue
            all_one_hop_nodes.update([e._tid for e in this_edges])
        all_one_hop_nodes = list(all_one_hop_nodes)
        all_one_hop_nodes_data = [knowledge_graph_inst.get_node(e) for e in all_one_hop_nodes]
        
        all_one_hop_text_units_lookup = {
            k: set(split_string_by_multi_markers(v.props.get('source_id'), [GRAPH_FIELD_SEP]))
            for k, v in zip(all_one_hop_nodes, all_one_hop_nodes_data)
            if v is not None
        }
        all_text_units_lookup = {}
        for index, (this_text_units, this_edges) in enumerate(zip(text_units, edges)):
            for c_id in this_text_units:
                if c_id in all_text_units_lookup:
                    continue
                relation_counts = 0
                for e in this_edges:
                    if (
                        e._tid in all_one_hop_text_units_lookup
                        and c_id in all_one_hop_text_units_lookup[e._tid]
                    ):
                        relation_counts += 1
                all_text_units_lookup[c_id] = {
                    "data": text_chunks_db.get(_hash=c_id),
                    "order": index,
                    "relation_counts": relation_counts,
                }
        if any([v is None for v in all_text_units_lookup.values()]):
            logger.warning("Text chunks are missing, maybe the storage is damaged")
        all_text_units = [
            {"id": k, **v} for k, v in all_text_units_lookup.items() if v is not None
        ]
        all_text_units = sorted(
            all_text_units, key=lambda x: (x["order"], -x["relation_counts"])
        )
        all_text_units = truncate_list_by_token_size(
            all_text_units,
            key=lambda x: x["data"].content_or_path,
            max_token_size=query_param.max_token_for_text_unit,
        )
        all_text_units: list[Chunk] = [t["data"] for t in all_text_units]
        return all_text_units

    async def _find_most_related_edges_from_entities(
        self,
        node_datas: list[dict],
        query_param: Query,
        knowledge_graph_inst: MemoryGraph,
    ):
        all_related_edges = await asyncio.gather(
            *[knowledge_graph_inst.get_neighbor_edges(dp["entity_name"], direction=Direction.BOTH) for dp in node_datas]
        )
        all_edges = set()
        for this_edges in all_related_edges:
            for e in this_edges:
                all_edges.add(e)
        all_edges = list(all_edges)
        all_edges_pack = [knowledge_graph_inst.get_edge(e._sid, e._tid) for e in all_edges]
        all_edges_pack = [list(edge_data)[0] for edge_data in all_edges_pack]
        
        # all_edges_pack = await asyncio.gather(
        #     *[knowledge_graph_inst.get_edge(e._sid, e._tid) for e in all_edges]
        # )

        all_edges_degree = await asyncio.gather(
            *[knowledge_graph_inst.edge_degree(e._sid, e._tid) for e in all_edges]
        )
        all_edges_data = [
            {"src_tgt": k, "rank": d, **v.props}
            for k, v, d in zip(all_edges, all_edges_pack, all_edges_degree)
            if v is not None
        ]
        all_edges_data = sorted(
            all_edges_data, key=lambda x: (x["rank"], x["weight"]), reverse=True
        )
        all_edges_data = truncate_list_by_token_size(
            all_edges_data,
            key=lambda x: x["description"],
            max_token_size=query_param.max_token_for_global_context,
        )
        
        return all_edges_data
    
    def merge_query_to_keywords(self, query: Query):
        text = query.text
        try:
            words = text.split(",")
            words = [w.strip() for w in words]
            unique_words = list(set(words))
            unique_words.sort(key=len, reverse=True)
            
            final_words = []
            for word in unique_words:
                if not any(word in other_word for other_word in final_words):
                    final_words.append(word)
            
            return final_words
        except Exception as e:
            logger.warning(str(e), text)
            return [text]

    async def _build_local_query_context(
        self,
        query: Query,
        knowledge_graph_inst: GraphStore,
        entities_vdb: Faiss,
        text_chunks_db: ChunkSQL,
        chunks: List[Chunk]
    ) -> RetrieveReply:
        # if False:
        #     entity_results = []
        #     for entity in query.text.split(','):
        #         entity_similars = entities_vdb.similarity_search(embedder=self.embedder, query=Query(text=entity), threshold=self.DENSE_THRESHOLD)
        #         if entity_similars:
        #             entity_results.append(entity_similars[0][0])
        #             results = entity_results
        # if True:
        #     results = entities_vdb.similarity_search(embedder=self.embedder, query=query, threshold=self.DENSE_THRESHOLD)
        #     results = [r[0] for r in results[0:self.LOWLEVEL_DENSE_TOPK]]
        # else:
        #     keywords = self.merge_query_to_keywords(query=query)
        #     entity_results = []
        #     all_similars = []
        #     for keword in keywords:
        #         entity_similars = entities_vdb.similarity_search(embedder=self.embedder, query=Query(text=keword), threshold=self.DENSE_THRESHOLD)
        #         if entity_similars:
        #             all_similars += entity_similars
        #     all_similars.sort(key=lambda x: x[1], reverse=True)
        #     pdb.set_trace()
        #     results =  [r[0] for r in all_similars[0:self.LOWLEVEL_DENSE_TOPK]]

        if not chunks:
            return RetrieveReply()
        
        node_datas = [knowledge_graph_inst.get_node(c.metadata["entity_name"]) for c in chunks]
        
        if not all([n is not None for n in node_datas]):
            logger.warning("Some nodes are missing, maybe the storage is damaged")

        node_degrees = await asyncio.gather(
            *[knowledge_graph_inst.node_degree(c.metadata["entity_name"]) for c in chunks]
        )

        node_datas = [
            {**n.props, "entity_name": k.metadata["entity_name"], "rank": d}
            for k, n, d in zip(chunks, node_datas, node_degrees)
            if n is not None
        ]

        use_text_units = await self._find_most_related_text_unit_from_entities(
            node_datas, query, text_chunks_db, knowledge_graph_inst
        )
        use_relations = await self._find_most_related_edges_from_entities(
            node_datas, query, knowledge_graph_inst
        )
        logger.info(
            f"Local query uses {len(node_datas)} entites, {len(use_relations)} relations, {len(use_text_units)} text units"
        )
        
        entites_section_list = [["entity", "type", "description", "rank"]]
        for i, n in enumerate(node_datas):
            entites_section_list.append(
                [
                    n["entity_name"],
                    n.get("type", "UNKNOWN"),
                    n.get("description", "UNKNOWN"),
                    n["rank"],
                ]
            )

        relations_section_list = [
            ["source", "target", "description", "keywords", "weight", "rank"]
        ]
        for i, e in enumerate(use_relations):
            relations_section_list.append(
                [
                    e["src_tgt"].sid,
                    e["src_tgt"].tid,
                    e["description"],
                    e["src_tgt"].name,
                    e["weight"],
                    e["rank"],
                ]
            )

        r = RetrieveReply(nodes=entites_section_list, relations=relations_section_list, sources=use_text_units)
        return r
    
    async def _find_most_related_entities_from_relationships(
        self,
        edge_datas: list[dict],
        query_param: Query,
        knowledge_graph_inst: GraphStore,
    ):
        entity_names = set()
        for e in edge_datas:
            entity_names.add(e["src_id"])
            entity_names.add(e["tgt_id"])

        node_datas = [knowledge_graph_inst.get_node(entity_name) for entity_name in entity_names]

        node_degrees = await asyncio.gather(
            *[knowledge_graph_inst.node_degree(entity_name) for entity_name in entity_names]
        )
        node_datas = [
            {**n.props, "entity_name": k, "rank": d}
            for k, n, d in zip(entity_names, node_datas, node_degrees)
        ]

        node_datas = truncate_list_by_token_size(
            node_datas,
            key=lambda x: x["description"],
            max_token_size=query_param.max_token_for_local_context,
        )
        return node_datas

    async def _find_related_text_unit_from_relationships(
        self,
        edge_datas: list[dict],
        query_param: Query,
        text_chunks_db: ChunkSQL,
        knowledge_graph_inst: GraphStore,
    ):

        text_units = [
            split_string_by_multi_markers(dp["source_id"], [GRAPH_FIELD_SEP])
            for dp in edge_datas
        ]

        all_text_units_lookup = {}

        for index, unit_list in enumerate(text_units):
            for c_id in unit_list:
                if c_id not in all_text_units_lookup:
                    all_text_units_lookup[c_id] = {
                        "data": text_chunks_db.get(c_id),
                        "order": index,
                    }
        if any([v is None for v in all_text_units_lookup.values()]):
            logger.warning("Text chunks are missing, maybe the storage is damaged")
        all_text_units = [
            {"id": k, **v} for k, v in all_text_units_lookup.items() if v is not None
        ]
        all_text_units = sorted(all_text_units, key=lambda x: x["order"])
        all_text_units = truncate_list_by_token_size(
            all_text_units,
            key=lambda x: x["data"].content_or_path,
            max_token_size=query_param.max_token_for_text_unit,
        )
        all_text_units: list[Chunk] = [t["data"] for t in all_text_units]
        return all_text_units


    async def _build_global_query_context(
        self,
        query_param: Query,
        knowledge_graph_inst: GraphStore,
        relationships_vdb: Faiss,
        text_chunks_db: ChunkSQL,
        chunks: List[Chunk]
    ) -> RetrieveReply:
        if not chunks:
            return RetrieveReply()
        
        edge_datas = [knowledge_graph_inst.get_edge(c.metadata["src_id"], c.metadata["tgt_id"]) for c in chunks]
        
        # edge_datas = await asyncio.gather(
        #     *[knowledge_graph_inst.get_edge(r.metadata["src_id"], r.metadata["tgt_id"]) for r in results]
        # )

        if not all([n is not None for n in edge_datas]):
            logger.warning("Some edges are missing, maybe the storage is damaged")
            
        edge_datas = [list(edge_data)[0] for edge_data in edge_datas]
        edge_degree = await asyncio.gather(
            *[knowledge_graph_inst.edge_degree(c.metadata["src_id"], c.metadata["tgt_id"]) for c in chunks]
        )
        edge_datas = [
            {"src_id": v.sid, "tgt_id": v.tid, "rank": d, **v.props, "keywords": v.name}
            for v, d in zip(edge_datas, edge_degree)
            if v is not None
        ]
        edge_datas = sorted(
            edge_datas, key=lambda x: (x["rank"], x["weight"]), reverse=True
        )
        edge_datas = truncate_list_by_token_size(
            edge_datas,
            key=lambda x: x["description"],
            max_token_size=query_param.max_token_for_global_context,
        )

        use_entities = await self._find_most_related_entities_from_relationships(
            edge_datas, query_param, knowledge_graph_inst
        )
        use_text_units = await self._find_related_text_unit_from_relationships(
            edge_datas, query_param, text_chunks_db, knowledge_graph_inst
        )
        logger.info(
            f"Global query uses {len(use_entities)} entites, {len(edge_datas)} relations, {len(use_text_units)} text units"
        )
        relations_section_list = [
            ["source", "target", "description", "keywords", "weight", "rank"]
        ]

        for e in edge_datas:
            relations_section_list.append(
                [
                    e["src_id"],
                    e["tgt_id"],
                    e["description"],
                    e["keywords"],
                    e["weight"],
                    e["rank"],
                ]
            )

        entites_section_list = [["entity", "type", "description", "rank"]]
        for n in use_entities:
            entites_section_list.append(
                [
                    n["entity_name"],
                    n.get("entity_type", "UNKNOWN"),
                    n.get("description", "UNKNOWN"),
                    n["rank"],
                ]
            )


        r = RetrieveReply(nodes=entites_section_list, relations=relations_section_list, sources=use_text_units)
        return r
    
    async def decompose_to_keywords(self, query: Query) -> Tuple[str, str]:
        kw_prompt_temp = PROMPTS["keywords_extraction"][query.language]
        kw_prompt = kw_prompt_temp.format(query=query.text)

        hl_keywords = []
        ll_keywords = []
        result = await self.llm.chat(kw_prompt)
        try:
            keywords_data = json.loads(result)
            hl_keywords = keywords_data.get("high_level_keywords", [])
            ll_keywords = keywords_data.get("low_level_keywords", [])
            hl_keywords = ", ".join(hl_keywords)
            ll_keywords = ", ".join(ll_keywords)
        except json.JSONDecodeError:
            try:
                result = (
                    result.replace(kw_prompt[:-1], "")
                    .replace("user", "")
                    .replace("model", "")
                    .strip()
                )
                result = "{" + result.split("{")[1].split("}")[0] + "}"

                keywords_data = json.loads(result)
                hl_keywords = keywords_data.get("high_level_keywords", [])
                ll_keywords = keywords_data.get("low_level_keywords", [])
                hl_keywords = ", ".join(hl_keywords)
                ll_keywords = ", ".join(ll_keywords)
            # Handle parsing error
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}, input {result}")
                return [], []
        
        return hl_keywords, ll_keywords

    async def explore(self, query: Query) -> RetrieveReply:
        hl_keywords, ll_keywords = await self.decompose_to_keywords(query=query)
        ll_keywords = '{}, {}'.format(hl_keywords, ll_keywords)
        
        low_level_context = RetrieveReply()
        high_level_context = RetrieveReply()

        if ll_keywords:
            results = self.entityDB.similarity_search(embedder=self.embedder, query=query, threshold=self.DENSE_THRESHOLD)
            if results:
                chunks = [r[0] for r in results[0:self.LOWLEVEL_DENSE_TOPK]]
                low_level_context = await self._build_local_query_context(
                    query=Query(text=ll_keywords),
                    knowledge_graph_inst=self.graph_store,
                    entities_vdb=self.entityDB,
                    text_chunks_db=self.chunkDB,
                    chunks=chunks
                )

        if hl_keywords:
            results = self.relationDB.similarity_search(embedder=self.embedder, query=query, threshold=self.DENSE_THRESHOLD)
            if results:
                chunks = [r[0] for r in results[0:self.HIGHLEVEL_DENSE_TOPK]]
                high_level_context = await self._build_global_query_context(
                    query_param=Query(text=hl_keywords),
                    knowledge_graph_inst=self.graph_store,
                    relationships_vdb=self.relationDB,
                    text_chunks_db=self.chunkDB,
                    chunks=chunks
                )
        for r in high_level_context.sources:
            logger.warning(r.metadata)
        for r in low_level_context.sources:
            logger.warning(r.metadata)
        r =  self.combine_contexts(high_level_context, low_level_context)
        return r

    async def similarity_score(self, query: Union[Query, str]) -> float:
        """Is input query relative with knowledge base. Return true or false, and the maximum score"""
        if type(query) is str:
            query = Query(text=query)

        hl_keywords, ll_keywords = await self.decompose_to_keywords(query=query)

        entity_pairs = self.entityDB.similarity_search(self.embedder, query=Query(text=ll_keywords), threshold=0.0)
        entity_max_score = 0.0
        if len(entity_pairs) > 0:
            entity_max_score = entity_pairs[0][1]
        
        relation_pairs = self.relationDB.similarity_search(self.embedder, query=Query(text=hl_keywords), threshold=0.0)
        relation_max_score = 0.0
        if len(relation_pairs) > 0:
            relation_max_score = relation_pairs[0][1]

        return max(entity_max_score, relation_max_score)
