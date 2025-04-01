import re
import os

"""Web search utils."""
from bs4 import BeautifulSoup as BS
from loguru import logger

from ...primitive import Chunk, Query, encode_string
from .base import Retriever, RetrieveResource, RetrieveReply
from .agis import g_agis

class RegularRetriever(Retriever):

    def __init__(self, resource: RetrieveResource, work_dir: str, pattern: str=r"agis_os(\d{2})g(\d{6})", **kwargs) -> None:
        """Initializes the WebSearch object with initialized resource."""
        super().__init__()
        if not pattern:
            logger.error(f'{__file__} pattern is empty')
        self.pattern = pattern
        self.preprocess_dir = os.path.join(work_dir, 'preprocess')

    async def constrait_length(self, content: str, query: Query):
        content_length = len(encode_string(content=content))
        if content_length > query.max_token_for_text_unit:
            return content[0:int(query.max_token_for_text_unit * 1.5)]
        return content

    async def explore(self, query: Query):
        """Executes a regular match."""
        r = RetrieveReply()
        if not query.text:
            logger.error(f"{__file__} input text is None")
            return r
        
        lower_text = query.text.lower()
        match_files = set()
        for k, v in g_agis.items():
            if k.lower() in lower_text:
                agispath = os.path.join(self.preprocess_dir, v)
                if not os.path.exists(agispath):
                    continue

                if v not in match_files:
                    match_files.add(v)

                    with open(agispath) as f:
                        content = f.read()
                        content = await self.constrait_length(content=content, query=query)
                        c = Chunk(content_or_path=content, metadata={"source": agispath})
                        r.nodes.append([id])
                        r.sources.append(c)
        return r
