"""Web search utils."""
import aiohttp
import json
import types
import pytoml
from bs4 import BeautifulSoup as BS
from loguru import logger
from readability import Document

from ...primitive import Chunk, Query
from ..helper import check_str_useful
from ..prompt import rag_prompts as PROMPT
from .base import Retriever, RetrieveResource, RetrieveReply


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

    async def analyze_url(self, target_link: str, brief: str = ''):
        if not target_link.startswith('http'):
            return None

        logger.info(f'extract: {target_link}')
        async with aiohttp.ClientSession() as session:
            # 发送POST请求
            async with session.get(target_link) as response:
                # 确保请求成功
                response.raise_for_status()
                # 返回响应的文本内容
                content = response.text()
                doc = Document(content)
                content_html = doc.summary()
                title = doc.short_title()
                soup = BS(content_html, 'html.parser')

                content = '{} {}'.format(title, soup.text)
                content = content.replace('\n\n', '\n')
                content = content.replace('\n\n', '\n')
                content = content.replace('  ', ' ')

                if not check_str_useful(content=content):
                    return None

                return [target_link, content]

    async def explore(self, query: Query):
        """Executes a google search based on the provided query.

        Parses the response and extracts the relevant URLs based on the
        priority defined in the configuration file. Performs a GET request on
        these URLs and extracts the title and content of the page. The content
        is cleaned and added to the articles list. Returns a list of articles.
        """
        r = RetrieveReply()
        if query.text is None:
            logger.error(f"{__file__} input text is None")
            return r

        prompt = PROMPT['web_keywords'][query.language].format(
            input_text=query.text)
        web_keywords = await self.llm.chat(prompt)

        async with aiohttp.ClientSession() as session:
            # 发送POST请求
            url = 'https://google.serper.dev/search'
            hl = 'zh-cn' if 'zh' in query.language else 'en'
            payload = json.dumps({'q': f'{web_keywords}', 'hl': hl})
            headers = {
                'X-API-KEY': self.search_config.serper_x_api_key,
                'Content-Type': 'application/json'
            }
            async with session.post(url, data=payload,
                                    headers=headers) as response:
                # 确保请求成功
                response.raise_for_status()
                # 返回响应的文本内容
                json_obj = await response.json()
                logger.debug(json_obj)

                for organic in json_obj['organic']:
                    print(organic)
                    content = '{},{}'.format(organic['title'],
                                             organic['snippet'])
                    c = Chunk(content_or_path=content,
                              metadata={"source": organic['link']})
                    r.add_source(c)
                return r
