from huixiangdou.primitive import Query
from ..service import ErrorCode
import os
import json
from time import time
from enum import Enum
from loguru import logger
from typing import List, Dict
from texttable import Texttable

class Session:
    
    def create_logger(self, module):
        log_file = f"logs/{module}.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        return logger.add(log_file, format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", filter=lambda record: record["extra"].get("module") == module)
    
    def __init__(self,
                 query: Query,
                 history: List[Dict],
                 request_id: str = 'default',
                 group_chats: Dict = {},
                 language: str = 'zh_cn'):
        # retriever inputs
        self.query = query
        self.history = history
        self.group_chats = group_chats
        self.language = language
        
        # retriever outputs
        self.retrieve_replies = []
        self.fused_reply = None
        
        # chat reply
        self.delta = ''
        self.response = ''
        self.code = ErrorCode.SUCCESS
        self.stage = ""

        # logger for every request
        self.logger = logger.bind(module=request_id)
        self._log_handler = self.create_logger(request_id)
        self.node = ""
        self.debug = dict()

    def visible_str(self, txt):
        return txt.replace('\n', '\\n').replace('\t', '\\t')

    def format(self, max_len:int=-1):
        refs = list(set([os.path.basename(c.metadata["source"]) for c in self.fused_reply.sources] if self.fused_reply is not None else []))
        
        table = Texttable()
        table.set_cols_valign(['t', 't', 't', 't'])
        table.header(['Query', 'State', 'Response', 'References'])
        if max_len > 0:
            table.add_row([self.visible_str(self.query.text), str(self.code), self.visible_str(self.response[0:max_len] + '..'), ','.join(refs)])
        else:
            table.add_row([self.visible_str(self.query.text), str(self.code), self.visible_str(self.response), ','.join(refs)])
        return table.draw()

    def __del__(self):
        self.logger = None
        try:
            logger.remove(self._log_handler)
        except:
            pass