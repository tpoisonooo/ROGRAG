import json
import os
import tempfile
import time

import pytoml
from loguru import logger

import unittest
from unittest.mock import patch, MagicMock
from huixiangdou.service import WebRetriever, RetrieveResource, RetrieveReply  # 确保从你的模块导入相应的类
from huixiangdou.primitive import Query


def load_secret():
    kimi_token = ''
    serper_token = ''
    with open('unittest/token.json') as f:
        json_obj = json.load(f)
        kimi_token = json_obj['kimi']
        serper_token = json_obj['serper']
    return kimi_token, serper_token


class TestWebRetriever(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        kimi_token, serper_token = load_secret()
        config = None
        with open('config.ini') as f:
            config = pytoml.load(f)
            config['web_search']['engine'] = 'serper'
            config['web_search']['serper_x_api_key'] = serper_token
            config['llm']['kimi']['api_key'] = kimi_token
        self.config_path = '/tmp/config.ini'
        with open(self.config_path, 'w', encoding='utf8') as f:
            pytoml.dump(config, f)
            f.flush()

        self.resource = RetrieveResource(
            config_path=self.config_path)  # 假设这个类有一个默认的构造函数
        self.web_retriever = WebRetriever(resource=self.resource,
                                          config_path=self.config_path)

    async def test_explore(self):
        # 测试explore方法
        query = Query(text='test query')
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                'organic': [{
                    'link':
                    'https://baike.baidu.com/item/%E5%A4%A7%E7%B1%B3/22607'
                }, {
                    'link':
                    'https://baike.baidu.com/item/%E5%B0%8F%E9%BA%A6/10237'
                }]
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_get_response = MagicMock()
                mock_get_response.raise_for_status.return_value = None
                mock_get_response.text.return_value = '<title>Test Page</title><p>Test content</p>'
                mock_get.return_value.__aenter__.return_value = mock_get_response

                result = await self.web_retriever.explore(query)
                self.assertIsInstance(result, RetrieveReply)
                self.assertEqual(len(result.text_units), 2)

    async def test_analyze_url(self):
        # 测试analyze_url方法
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.text.return_value = '<title>Test Page</title><p>Test content</p>'
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await self.web_retriever.analyze_url('https://example.com'
                                                          )
            self.assertIsNotNone(result)
            self.assertEqual(result[0], '')
            self.assertIn('Test content', result[1])

    async def asyncTearDown(self):
        # 清理测试环境
        os.remove(self.config_path)


if __name__ == '__main__':
    unittest.main()
