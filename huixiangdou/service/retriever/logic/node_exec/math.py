from ...base import LogicNode, RetrieveResource, RetrieveReply, OpSession, OpExecutor
from ..node_param import CountNode, SumNode, CompareNode
from .....primitive import Edge, Vertex
from loguru import logger
from collections.abc import Iterable
from ....prompt import reason_prompts as PROMPTS
from typing import Union, List, Tuple
import pdb
import json


def default_json(obj):
    if isinstance(obj, Vertex):
        return obj.props.get("description", "")
    elif isinstance(obj, Edge):
        return obj.props.get("description", "")
    return obj


class MathExecutor(OpExecutor):

    def __init__(self, resource: RetrieveResource):
        super().__init__(resource)

    def is_this_op(self, logic_node: LogicNode) -> bool:
        return isinstance(logic_node, (CountNode, SumNode, CompareNode))

    async def run(self, logic_node: LogicNode, op_sess: OpSession):
        # logger.warning(logic_node)
        if not logic_node.set:
            raise Exception(f'{__file__} missing param {logic_node}')
        ret = 0

        if isinstance(logic_node, CountNode):
            task = '执行 Count 算子，执行参数列表中的统计任务。统计目标可能是数字，也可能是文字语义。'
        elif isinstance(logic_node, SumNode):
            task = '执行 Sum 算子，完成参数列表中的数数值累加'
        elif isinstance(logic_node, CompareNode):
            task = '执行 Compare 算子，比较参数列表中数字大小'
        else:
            raise Exception(f'{__file__} illegal task')

        # build params
        param_list_str = '参数列表{}\n'.format(
            json.dumps(logic_node.set,
                       ensure_ascii=False,
                       default=default_json))
        _, vars_, _ = self.split(logic_node.set)
        param_dict_str = ''
        for var_ in vars_:
            param_dict_str += '参数内容{}\n'.format(
                json.dumps({var_: op_sess.param.get(var_)},
                           ensure_ascii=False,
                           default=default_json))

        param_text = "{param_list_str}{param_dict_str}".format(
            param_list_str=param_list_str, param_dict_str=param_dict_str)
        step_text = json.dumps(op_sess.evidence_strs, ensure_ascii=False)
        prompt = PROMPTS['math']['zh_cn'].format(
            task=task,
            param_text=param_text,
            step_text=step_text,
            sub_query=logic_node.sub_query,
            root_query=logic_node.root_query)

        ret = await self.resource.llm.chat(prompt)
        op_sess.param[logic_node.alias_name] = str(ret)
        op_sess.upsert_evidence(sub_query=logic_node.sub_query,
                                alias=logic_node.alias_name,
                                items=[],
                                sub_answer=str(ret))
        return None
