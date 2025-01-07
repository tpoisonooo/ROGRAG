"""LLM server proxy."""
import json
import pdb
import os
import asyncio
from typing import Dict
import pytoml
from loguru import logger
from openai import AsyncOpenAI, APIConnectionError, RateLimitError, Timeout, APITimeoutError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from functools import wraps
import asyncio
from loguru import logger


def always_get_an_event_loop() -> asyncio.AbstractEventLoop:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.info("Creating a new event loop in a sub-thread.")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=30, max=60),
    retry=retry_if_exception_type(
        (RateLimitError, APIConnectionError, Timeout, APITimeoutError)),
)
async def chat() -> str:
    openai_async_client = AsyncOpenAI(base_url='https://api.siliconflow.cn/v1',
                                        api_key='sk-ntcafwkzmaawsuxmvufxqiahedyhekqvyaqetgtikdowkjbz')
    stream = await openai_async_client.chat.completions.create(
        model='Qwen/Qwen2.5-32B-Instruct', messages=[{"role":"user", "content": "hello"}], temperature=0.7, top_p=0.7, stream=True)
    pdb.set_trace()
    
    async for chunk in stream:
        if chunk.choices is None:
            raise Exception(str(chunk))
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
    
async def forward():
    async for x in chat():
        print(x, end="")

loop = always_get_an_event_loop()
loop.run_until_complete(forward())