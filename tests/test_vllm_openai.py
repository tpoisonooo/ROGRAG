from openai import OpenAI, AsyncOpenAI
import asyncio
import pdb

from loguru import logger
# Set OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "EMPTY"
openai_api_base = "http://localhost:8000/v1"

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)


def always_get_an_event_loop() -> asyncio.AbstractEventLoop:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.info("Creating a new event loop in a sub-thread.")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

async def airun():
    pdb.set_trace()

    inst = AsyncOpenAI(base_url=openai_api_base, api_key=openai_api_key)
    response = await inst.chat.completions.create(model="internlm2_5-7b-chat", messages=[{"role": "user", "content": "hello"}])
    print(response.choices[0].message.content)

loop = always_get_an_event_loop()
loop.run_until_complete(airun())

chat_response = client.chat.completions.create(
    model="internlm2_5-7b-chat",
    messages=[
        {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."},
        {"role": "user", "content": "Tell me something about large language models."},
    ],
    temperature=0.7,
    top_p=0.8,
    max_tokens=512,
    extra_body={
        "repetition_penalty": 1.05,
    },
)
print("Chat response:", chat_response)