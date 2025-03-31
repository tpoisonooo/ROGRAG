import re
import os

"""Web search utils."""
from bs4 import BeautifulSoup as BS
from loguru import logger

from ...primitive import Chunk, Query
from .base import Retriever, RetrieveResource, RetrieveReply

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

        matches = re.findall(self.pattern, query.text.lower())
        if not matches:
            return r
        
        for match in matches:
            try:
                two_digits = match[0]
                six_digits = match[1]
                id = f'AGIS_Os{two_digits}g{six_digits}'
                agispath = os.path.join(self.preprocess_dir, f'{id}.txt')
                if not os.path.exists(agispath):
                    continue

                with open(agispath) as f:
                    content = f.read()
                    c = Chunk(content_or_path=content, metadata={"source": agispath})
                    r.sources.append(c)
            except Exception as e:
                logger.error(e)
        return r
