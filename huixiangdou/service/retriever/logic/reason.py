from ....primitive import Faiss, Query, Chunk, MemoryGraph, Direction, always_get_an_event_loop
from ...graph_store import GraphStore
from loguru import logger
from typing import List, Union, Any, Tuple
from ..base import Retriever, RetrieveResource, RetrieveReply, OpSession, LogicNode
from .node_param import GetNode, CompareNode, SumNode, CountNode, GetSPONode
from .node_exec import MathExecutor, GetExecutor, GraphExecutor
from ...prompt import reason_prompts as PROMPTS
from ...nlu import split_string_by_multi_markers, truncate_list_by_token_size
from ...sql import ChunkSQL
from collections import defaultdict

import re
import os
import json
import asyncio
import pdb
import time


# Heavily modified from KAG
class LFPlanResult:

    def __init__(self, query: str, lf_nodes: List[LogicNode]):
        self.query: str = query
        self.lf_nodes: List[LogicNode] = lf_nodes

    def __repr__(self):
        data = {'query': self.query, 'lf_nodes': str(self.lf_nodes)}
        data_str = json.dumps(data, ensure_ascii=False, indent=2)
        return data_str


class ReasonRetriever(Retriever):

    def __init__(self, resource: RetrieveResource, work_dir: str) -> None:
        super().__init__()
        """Init with model device type and config."""
        self.resource = resource
        self.chunkDB = ChunkSQL(file_dir=os.path.join(work_dir, 'db_chunk'))
        if not os.path.exists(work_dir):
            logger.warning('!!!warning, workdir not exist.!!!')

        self.math_executor = MathExecutor(resource)
        self.graph_executor = GraphExecutor(resource, work_dir, self.chunkDB)
        self.get_executor = GetExecutor(resource)
        self.executors = [
            self.math_executor, self.graph_executor, self.get_executor
        ]

    def parse_logic_form(self,
                         input_str: str,
                         parsed_entity_set={},
                         sub_query=None,
                         query=None) -> LogicNode:
        match = re.match(r'(\w+)[\(\（](.*)[\)\）](->)?(.*)?', input_str.strip())
        if not match:
            raise RuntimeError(f"parse logic form error {input_str}")
        if len(match.groups()) == 4:
            operator, args_str, _, output_name = match.groups()
        else:
            operator, args_str = match.groups()
            output_name = None
        low_operator = operator.lower()
        if low_operator == "get":
            node: GetNode = GetNode.parse_node(args_str=args_str)
            if node.alias_name in parsed_entity_set.keys():
                s = parsed_entity_set[node.alias_name]
                node.s = s
        elif low_operator in ["get_spo", "retrieval"]:
            node: GetSPONode = GetSPONode.parse_node(args_str)
        elif low_operator in ["count"]:
            node: CountNode = CountNode.parse_node(args_str, output_name)
        elif low_operator in ["sum"]:
            node: SumNode = SumNode.parse_node(input_str)
        elif low_operator in ["sort"]:
            node: SortNode = SortNode.parse_node(args_str)
        elif low_operator in ["compare"]:
            node: SortNode = CompareNode.parse_node(args_str)
        else:
            raise NotImplementedError(f"not impl {input_str}")

        node.to_std({"sub_query": sub_query, "root_query": query})
        return node

    def split_sub_query(self,
                        logic_nodes: List[LogicNode]) -> List[LFPlanResult]:
        query_lf_map = {}
        for n in logic_nodes:
            if n.sub_query in query_lf_map.keys():
                query_lf_map[n.sub_query] = query_lf_map[n.sub_query] + [n]
            else:
                query_lf_map[n.sub_query] = [n]
        plan_result = []
        for k, v in query_lf_map.items():
            plan_result.append(LFPlanResult(query=k, lf_nodes=v))
        return plan_result

    def parse_lf(self, question: str, response: str) -> List[LFPlanResult]:
        parsed_node = []
        parsed_cached_map = {}

        try:
            logger.debug(f"logic form:{response}")
            _output_string = response.replace("：", ":")
            _output_string = response.strip()

            json_forms = json.loads(_output_string)
            for form in json_forms:
                sub_query = form['step']
                input_str = form['action']
                logic_node = self.parse_logic_form(input_str,
                                                   parsed_cached_map,
                                                   sub_query=sub_query,
                                                   query=question)
                parsed_node.append(logic_node)
        except Exception as e:
            logger.warning(f"{response} parse logic form faied {e}",
                           exc_info=True)
            return []

        return self.split_sub_query(parsed_node)

    async def execute_lf(self, plan_nodes: List[LFPlanResult]) -> OpSession:
        op_sess = OpSession()
        # Execute graph retrieval operations.
        for plan in plan_nodes:
            for node in plan.lf_nodes:
                run = False
                for executor in self.executors:
                    if executor.is_this_op(node):
                        logger.info(
                            f"begin run logic node {str(plan)} at {type(executor)}"
                        )
                        await executor.run(node, op_sess)
                        run = True
                        break
                if not run:
                    logger.warning(f"unknown node: {node}")
        return op_sess

    async def explore(self, query: Query) -> RetrieveReply:
        prompt = PROMPTS['format_input'][query.language].format(
            input_text=query.text)
        response = await self.resource.llm.chat(prompt)

        # convert raw string to string list
        plan_nodes = self.parse_lf(question=query.text, response=response)
        op_sess = await self.execute_lf(plan_nodes=plan_nodes)
        r = op_sess.to_reply(self.chunkDB)
        return r
