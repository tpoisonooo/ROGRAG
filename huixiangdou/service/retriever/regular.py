import re
import os

"""Web search utils."""
from bs4 import BeautifulSoup as BS
from loguru import logger

from ...primitive import Chunk, Query
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
                        c = Chunk(content_or_path=content, metadata={"source": agispath})
                        r.nodes.append([id])
                        r.sources.append(c)
        return r
