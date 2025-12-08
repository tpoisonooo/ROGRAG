"""Web search utils."""
import aiohttp
import json
import types
import pytoml
from bs4 import BeautifulSoup as BS
from loguru import logger
from readability import Document

from ...primitive import Chunk, Query, Pair
from ..helper import check_str_useful
from ..prompt import rag_prompts as PROMPT
from .base import Retriever, RetrieveResource, RetrieveReply
from typing import List
from alibabacloud_tea_openapi.models import Config
from alibabacloud_searchplat20240529.client import Client
from alibabacloud_searchplat20240529.models import GetWebSearchRequest,GetWebSearchRequestHistory


class WebRetriever(Retriever):
    """This class provides functionality to perform web search operations.

    Attributes:
        resource (RetrieveResource): Initialized Resource.
    """

    def __init__(self, resource: RetrieveResource, **kwargs) -> None:
        """Initializes the WebSearch object with initialized resource."""

        super().__init__()
        self.search_config = None
        self.max_url_count = 3
        self.llm = resource.llm
        with open(resource.config_path, encoding='utf8') as f:
            config = pytoml.load(f)
            self.search_config = types.SimpleNamespace(**config['web_search'])
            webconfig = Config(bearer_token=self.search_config.aliyun_api_key, endpoint="default-b9kf.platform-cn-shanghai.opensearch.aliyuncs.com", protocol="http")
        self.client = Client(config=webconfig)

    async def explore(self, query: Query, history: List[Pair]=[]):
        r = RetrieveReply()
        if query.text is None:
            logger.error(f"{__file__} input text is None")
            return r

        messages = []
        for p in history:
            messages += [GetWebSearchRequestHistory(content=p.user, role="user"), GetWebSearchRequestHistory(content=p.assistant, role="assistant")]
        request = GetWebSearchRequest(query=query.text, history=messages, content_type="summary")

        try:
            response = self.client.get_web_search("default", "ops-web-search-001", request)
            for search_chunk in response.body.result.search_result:
                r.add_source(Chunk(content_or_path=search_chunk['content']))
        except Exception as e:
            logger.error(f'{__file__} {str(e)}')
        return r
