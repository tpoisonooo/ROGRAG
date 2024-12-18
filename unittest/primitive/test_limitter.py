import pytest
import asyncio
from huixiangdou.primitive import RPM, TPM  # 替换 your_module 为你的模块名
from datetime import datetime, timedelta
from loguru import logger
# 测试 RPM 类
@pytest.mark.asyncio
async def test_rpm():
    rpm_instance = RPM(rpm=1)
    await rpm_instance.wait()
    assert rpm_instance.record['counter'] == 1

# 测试 RPM 类的速率限制
@pytest.mark.asyncio
async def test_rpm_rate_limit():
    rpm_instance = RPM(rpm=1)
    await rpm_instance.wait()
    # 立即再次调用 wait 应该会导致等待下一分钟后才增加计数
    start_time = datetime.now()
    await rpm_instance.wait()
    end_time = datetime.now()
    assert (end_time - start_time) <= timedelta(minutes=1)
    assert rpm_instance.record['counter'] == 1

# 测试 TPM 类
@pytest.mark.asyncio
async def test_tpm():
    tpm_instance = TPM(tpm=2)
    await tpm_instance.wait(1)
    await tpm_instance.wait(1)
    assert tpm_instance.record['counter'] <= 2
    await tpm_instance.wait(1)
    assert tpm_instance.record['counter'] == 1
    
# 测试 TPM 类的速率限制
@pytest.mark.asyncio
async def test_tpm_rate_limit():
    tpm_instance = TPM(tpm=1)
    # 立即再次调用 wait 应该会导致等待直到计数重置
    start_time = datetime.now()
    await tpm_instance.wait(1)
    end_time = datetime.now()
    assert (end_time - start_time) <= timedelta(minutes=1)
    assert tpm_instance.record['counter'] == 1

# 测试 TPM 类的 token_count 参数
@pytest.mark.asyncio
async def test_tpm_token_count():
    tpm_instance = TPM(tpm=10)
    await tpm_instance.wait(5)
    assert tpm_instance.record['counter'] == 5
    await tpm_instance.wait(6)  # 这应该超过限制并等待
    assert tpm_instance.record['counter'] == 6


def always_get_an_event_loop() -> asyncio.AbstractEventLoop:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.info("Creating a new event loop in a sub-thread.")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

if __name__ == '__main__':
    loop = always_get_an_event_loop()
    # loop.run_until_complete(test_rpm())
    # loop.run_until_complete(test_rpm_rate_limit())
    loop.run_until_complete(test_tpm())
    loop.run_until_complete(test_tpm_rate_limit())
    loop.run_until_complete(test_tpm_token_count())
    
    
