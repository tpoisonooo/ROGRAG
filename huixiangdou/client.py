import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# 基础 URL
BASE_URL = "http://10.15.1.122:23334"

# 测试 /v2/chat 接口
def test_chat_zh():
    url = f"{BASE_URL}/v2/chat"
    headers = {"Content-Type": "application/json"}

    # 示例请求体
    request_body = {
        "language": "zh_CN",
        "enable_web_search": False,
        # "user": "AGIS_Os05g040410 和  AGIS_Os06g035130 相似的环境响应性有多少种？",
        # "user": "大竹青黄豆标准化生产有啥用？",
        # "user": "AGIS_Os01g063400的基本信息",
        "user": "AGIS_Os01g033640 是一个怎样的QTG？ ",
        "history": []
        # "history": [
        #     {
        #         "user": "今天是几月几号？",
        #         "assistant": "20250221",
        #         "references": []
        #     }
        # ]
    }

    response = requests.post(url,
                             headers=headers,
                             data=json.dumps(request_body))
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8")
            print(decoded_line)

# 测试 /v2/chat 接口
def test_chat_en():
    url = f"{BASE_URL}/v2/chat"
    headers = {"Content-Type": "application/json"}

    # 示例请求体
    request_body = {
        "language":
        "en",
        "enable_web_search":
        False,
        "user":
        "What should I call you?",
        "history": [{
            "user": "what day is today?",
            "assistant": "20250221",
            "references": []
        }]
    }

    response = requests.post(url,
                             headers=headers,
                             data=json.dumps(request_body))
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8")
            print(decoded_line)

# 测试 /v2/exemplify 接口
def test_exemplify():
    url = f"{BASE_URL}/v2/exemplify"
    headers = {"Content-Type": "application/json"}

    # 示例请求体
    request_body = {
        "language": "en",
        "enable_web_search": False,
        "user": "What is NingxiangJing 9",
        "history": []
    }

    response = requests.post(url,
                             headers=headers,
                             data=json.dumps(request_body))
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")


# 并行化测试函数
def parallel_test_chat_coref(num_requests):
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(test_chat_coref) for _ in range(num_requests)]
        for future in as_completed(futures):
            try:
                response = future.result()
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        print(decoded_line)
            except Exception as e:
                print(f"Request failed: {e}")


# 主函数，运行测试
if __name__ == "__main__":
    print("Testing /v2/chat endpoint...")
    test_chat_zh()

    # print("Testing /v2/chat endpoint...")
    # test_chat_en()

    # print("\nTesting /v2/exemplify endpoint...")
    # test_exemplify()

    # 示例：并行发送 5 个请求
    # parallel_test_chat_coref(5)
