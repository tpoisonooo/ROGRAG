"""LLM server proxy."""
import json
import pdb
import os
from .limitter import RPM, TPM
from .utils import always_get_an_event_loop
import asyncio
from typing import Dict, List, Dict, Union, AsyncGenerator
import pytoml
from loguru import logger
from openai import AsyncOpenAI, APIConnectionError, RateLimitError, Timeout, APITimeoutError
from .token import encode_string, decode_tokens
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from functools import wraps
import sqlite3
import uuid
import hashlib

os.environ["TOKENIZERS_PARALLELISM"] = "false"

backend2url = {
    "kimi": "https://api.moonshot.cn/v1",
    "step": "https://api.stepfun.com/v1",
    'xi-api': 'https://api.xi-ai.cn/v1',
    'deepseek': 'https://api.deepseek.com/v1',
    'zhipuai': 'https://open.bigmodel.cn/api/paas/v4/',
    'puyu': 'https://puyu.openxlab.org.cn/puyu/api/v1/',
    'siliconcloud': 'https://api.siliconflow.cn/v1',
    'local': 'http://localhost:8000/v1'
}

backend2model = {
    "kimi": "auto",
    "step": "auto",
    "deepseek": "deepseek-chat",
    "zhipuai": "glm-4",
    "puyu": "internlm2-latest",
    "siliconcloud": "Qwen/Qwen2.5-14B-Instruct"
}


def limit_async_func_call(max_size: int, waitting_time: float = 0.1):
    """Add restriction of maximum async calling times for a async func"""

    def final_decro(func):
        """Not using async.Semaphore to aovid use nest-asyncio"""
        __current_size = 0

        @wraps(func)
        async def wait_func(*args, **kwargs):
            nonlocal __current_size
            while __current_size >= max_size:
                await asyncio.sleep(waitting_time)
            __current_size += 1
            result = await func(*args, **kwargs)
            __current_size -= 1
            return result

        return wait_func

    return final_decro


class Backend:

    def __init__(self, name: str, data: Dict):
        self.api_key = data.get('api_key', '')
        self.max_token_size = data.get('max_token_size', 32000) - 4096
        if self.max_token_size < 0:
            raise Exception(f'{self.max_token_size} < 4096')
        self.rpm = RPM(int(data.get('rpm', 500)))
        self.tpm = TPM(int(data.get('tpm', 20000)))
        self.name = name
        self.port = int(data.get('port', 23333))
        self.model = data.get('model', '')
        self.base_url = data.get('base_url', '')
        if not self.base_url and name in backend2url:
            self.base_url = backend2url[name]

    def jsonify(self):
        return {"api_key": self.name, "model": self.model}

    def __str__(self):
        return json.dumps(self.jsonify())


class ChatCache:

    def __init__(self, file_path: str = '.cache_llm'):
        self.conn = sqlite3.connect(file_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat (
                _hash TEXT PRIMARY KEY,
                query TEXT,
                response TEXT,
                backend TEXT
            )
        ''')
        self.conn.commit()

    def hash(self, content: str) -> str:
        md5 = hashlib.md5()
        if type(content) is str:
            md5.update(content.encode('utf8'))
        else:
            md5.update(content)
        return md5.hexdigest()[0:6]

    def add(self, query: str, response: str, backend:str):
        _hash = self.hash(query)
        self.cursor.execute('''
            INSERT OR IGNORE INTO chat (_hash, query, response, backend)
            VALUES (?, ?, ?, ?)
        ''', (_hash, query, response, backend))
        self.conn.commit()

    def get(self, query: str, backend:str) -> Union[str, None]:
        """Retrieve a chunk by its ID."""
        if not query:
            return None
        _hash = self.hash(query)
        
        self.cursor.execute(
            'SELECT response FROM chat WHERE _hash = ? and backend = ?',
            (_hash, backend))
        r = self.cursor.fetchone()
        if r:
            return r[0]
        return None

    def __del__(self):
        try:
            self.cursor.close()
            self.conn.close()
        except Exception as e:
            logger.error(e)

class LLM:

    def __init__(self, config_path: str):
        """Initialize the LLM with the path of the configuration file."""
        self.config_path = config_path
        self.llm_config = None
        self.backends = dict()
        self.sum_input_token_size = 0
        self.sum_output_token_size = 0
        with open(self.config_path, encoding='utf8') as f:
            config = pytoml.load(f)
            self.llm_config = config['llm']

            for key, value in self.llm_config.items():
                self.backends[key] = Backend(name=key, data=value)
        self.cache = ChatCache()

    def choose_model(self, backend: Backend, token_size: int) -> str:
        if backend.model != None and len(backend.model) > 0:
            return backend.model

        model = ''
        if backend.name == 'kimi':
            if token_size <= 8192 - 1024:
                model = 'moonshot-v1-8k'
            elif token_size <= 32768 - 1024:
                model = 'moonshot-v1-32k'
            elif token_size <= 128000 - 1024:
                model = 'moonshot-v1-128k'
            else:
                raise ValueError('Input token length exceeds 128k')
        elif backend.name == 'step':
            if token_size <= 8192 - 1024:
                model = 'step-1-8k'
            elif token_size <= 32768 - 1024:
                model = 'step-1-32k'
            elif token_size <= 128000 - 1024:
                model = 'step-1-128k'
            elif token_size <= 256000 - 1024:
                model = 'step-1-256k'
            else:
                raise ValueError('Input token length exceeds 256k')
        else:
            model = backend2model[backend.name]
        return model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=30, max=60),
        retry=retry_if_exception_type(
            (RateLimitError, APIConnectionError, Timeout, APITimeoutError)),
    )
    @limit_async_func_call(16)
    async def chat(self,
                   prompt: str,
                   backend: str = 'default',
                   system_prompt=None,
                   history=[],
                   allow_truncate=False,
                   max_tokens=1024,
                   timeout=600,
                   enable_cache:bool=True) -> str:
        
        # choose backend
        # if user not specify model, use first one
        if backend == 'default':
            backend = list(self.backends.keys())[0]
        
        if enable_cache:
            r = self.cache.get(query=prompt, backend=backend)
            if r is not None:
                logger.info('LLM cache hit')
                return r
        
        instance = self.backends[backend]

        # try truncate input prompt
        input_tokens = encode_string(content=prompt)
        input_token_size = len(input_tokens)
        if input_token_size > instance.max_token_size:
            if not allow_truncate:
                raise Exception(
                    f'input token size {input_token_size}, max {instance.max_token_size}'
                )

            tokens = input_tokens[0:instance.max_token_size - input_token_size]
            prompt = decode_tokens(tokens=tokens)
            input_token_size = len(tokens)

        await instance.tpm.wait(token_count=input_token_size)

        # build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        content = ''
        # try:
        model = self.choose_model(backend=instance,
                                  token_size=input_token_size)
        openai_async_client = AsyncOpenAI(base_url=instance.base_url,
                                          api_key=instance.api_key,
                                          timeout=timeout)
        # response = await openai_async_client.chat.completions.create(model=model, messages=messages, max_tokens=8192, temperature=0.7, top_p=0.7, extra_body={'repetition_penalty': 1.05})

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "top_p": 0.7
        }
        if max_tokens:
            kwargs['max_tokens'] = max_tokens

        response = await openai_async_client.chat.completions.create(**kwargs)
        if response.choices is None:
            pass
        logger.info(response.choices[0].message.content)

        content = response.choices[0].message.content
        self.cache.add(query=prompt, response=content, backend=backend)
        
        # except Exception as e:
        #     logger.error( str(e) +' input len {}'.format(len(str(messages))))
        #     raise e
        content_token_size = len(encode_string(content=content))

        if False:
            dump_json = {"messages": messages, "reply": content}
            dump_json_str = json.dumps(dump_json, ensure_ascii=False)
            with open('llm.jsonl', 'w') as f:
                f.write(dump_json_str)
                f.write('\n')

        self.sum_input_token_size += input_token_size
        self.sum_output_token_size += content_token_size

        await instance.tpm.wait(token_count=content_token_size)
        await instance.rpm.wait()
        return content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=30, max=60),
        retry=retry_if_exception_type(
            (RateLimitError, APIConnectionError, Timeout, APITimeoutError)),
    )
    async def chat_stream(self,
                          prompt: str,
                          backend: str = 'default',
                          system_prompt=None,
                          history=[],
                          allow_truncate=False,
                          max_tokens=1024,
                          timeout=600,
                          enable_cache:bool=True) -> AsyncGenerator[str, None]:
    
        if enable_cache:
            r = self.cache.get(query=prompt, backend=backend)
            if r is not None:
                for char in r:
                    yield char
                return
            
        # choose backend
        # if user not specify model, use first one
        if backend == 'default':
            backend = list(self.backends.keys())[0]
        instance = self.backends[backend]

        # try truncate input prompt
        input_tokens = encode_string(content=prompt)
        input_token_size = len(input_tokens)
        if input_token_size > instance.max_token_size:
            if not allow_truncate:
                raise Exception(
                    f'input token size {input_token_size}, max {instance.max_token_size}'
                )

            tokens = input_tokens[0:instance.max_token_size - input_token_size]
            prompt = decode_tokens(tokens=tokens)
            input_token_size = len(tokens)

        await instance.tpm.wait(token_count=input_token_size)

        # build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        content = ''
        try:
            model = self.choose_model(backend=instance,
                                      token_size=input_token_size)
            openai_async_client = AsyncOpenAI(base_url=instance.base_url,
                                              api_key=instance.api_key,
                                              timeout=timeout)

            print(messages)
            stream = await openai_async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                top_p=0.7,
                max_tokens=max_tokens,
                stream=True)

            async for chunk in stream:
                if chunk.choices is None:
                    raise Exception(str(chunk))
                delta = chunk.choices[0].delta
                if delta.content:
                    content += delta.content
                    yield delta.content

        except Exception as e:
            logger.error(str(e) + ' input len {}'.format(len(str(messages))))
            raise e
        content_token_size = len(encode_string(content=content))
        self.cache.add(query=prompt, response=content, backend=backend)

        self.sum_input_token_size += input_token_size
        self.sum_output_token_size += content_token_size

        await instance.tpm.wait(token_count=content_token_size)
        await instance.rpm.wait()
        return

    def chat_sync(self,
                  prompt: str,
                  backend: str = 'default',
                  system_prompt=None,
                  history=[]):
        loop = always_get_an_event_loop()
        return loop.run_until_complete(
            self.chat(prompt=prompt,
                      backend=backend,
                      system_prompt=system_prompt,
                      history=history))

    def default_model_info(self):
        backend = list(self.backends.keys())[0]
        instance = self.backends[backend]
        return instance.jsonify()
