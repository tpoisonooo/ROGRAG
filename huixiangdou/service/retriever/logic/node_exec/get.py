from typing import Union
from ...base import LogicNode, RetrieveResource, RetrieveReply, OpSession, OpExecutor
from ..node_param import GetNode
from loguru import logger
import pdb

class GetExecutor(OpExecutor):
    def __init__(self, resource: RetrieveResource):
        super().__init__(resource)
        
    def is_this_op(self, logic_node: LogicNode) -> bool:
        return isinstance(logic_node, GetNode)

    async def run(self, logic_node: LogicNode, op_sess: OpSession):
        op_sess.mask_vars(logic_node.alias_name_set)
