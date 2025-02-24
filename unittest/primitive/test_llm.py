import unittest
from unittest.mock import patch, MagicMock
from huixiangdou.primitive import LLM, Backend
import pytoml
import json
import asyncio
import os
from loguru import logger


def load_secret():
    with open('unittest/token.json') as f:
        json_obj = json.load(f)
        return json_obj


class TestLLM(unittest.TestCase):

    def setUp(self):
        config_path = 'config.ini'
        if os.path.exists('unittest/token.json'):
            secrets = load_secret()
            config_proto = 'config.ini'
            with open(config_proto, encoding='utf8') as f:
                config = pytoml.load(f)
                config['llm']['kimi']['api_key'] = secrets['kimi']
                config['llm']['step']['api_key'] = secrets['step']
            config_path = '/tmp/config.ini'
            with open(config_path, 'w', encoding='utf8') as f:
                pytoml.dump(config, f)
                f.flush()

        self.llm = LLM(config_path)

    def test_init(self):
        # 测试初始化是否成功
        self.assertIsNotNone(self.llm.llm_config)
        self.assertIsInstance(self.llm.backends, dict)

    def test_choose_model(self):
        # 测试模型选择逻辑
        messages = ["Hello, world!"]
        backend = Backend(name='kimi', data={})
        model = self.llm.choose_model(backend=backend, token_size=20)
        self.assertEqual(model, 'moonshot-v1-8k')

        # 测试超出最大长度的情况
        with self.assertRaises(ValueError):
            self.llm.choose_model(backend=backend, token_size=128001)

    async def test_real_chat(self):
        await self.llm.chat(prompt='hi')

    @patch('huixiangdou.primitive.llm.AsyncOpenAI')
    async def test_chat(self, mock_async_openai):
        # 测试聊天功能
        mock_response = MagicMock()
        mock_response.choices = [{'message': {'content': 'Test response'}}]
        mock_async_openai.return_value.chat.completions.create.return_value = mock_response

        response = await self.llm.chat('Test prompt', 'kimi')
        self.assertEqual(response, 'Test response')

    @patch('huixiangdou.primitive.llm.AsyncOpenAI')
    async def test_chat_timeout(self, mock_async_openai):
        # 测试超时异常处理
        mock_async_openai.return_value.chat.completions.create.side_effect = Timeout

        with self.assertRaises(Timeout):
            await self.llm.chat('Test prompt', 'kimi')


def always_get_an_event_loop() -> asyncio.AbstractEventLoop:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


if __name__ == '__main__':
    handler = TestLLM()
    handler.setUp()
    handler.test_choose_model()
    loop = always_get_an_event_loop()
    loop.run_until_complete(handler.test_real_chat())
    # unittest.main()
