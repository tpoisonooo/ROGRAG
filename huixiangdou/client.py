import requests
import json

# 基础 URL
# BASE_URL = "http://127.0.0.1:23333"
BASE_URL = "http://101.133.161.204:7001/"

# 测试 /v2/chat 接口
def test_chat():
    url = f"{BASE_URL}/v2/chat"
    headers = {"Content-Type": "application/json"}

    # 示例请求体
    request_body = {
        "language": "zh_CN",
        "enable_web_search": True,
        "user": "Using available resources (e.g., the internet or your own database, such as a knowledge graph), what do we currently know about Os09g0472900?",
        "history": [
            {
                "user": "今天天气怎样",
                "assistant": "上海晴天",
                "references": []
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(request_body))
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
        "language": "zh_CN",
        "enable_web_search": False,
        "user": "浙辐802是哪里产的？",
        "history": []
    }

    response = requests.post(url, headers=headers, data=json.dumps(request_body))
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

# 主函数，运行测试
if __name__ == "__main__":
    print("Testing /v2/chat endpoint...")
    test_chat()

    print("\nTesting /v2/exemplify endpoint...")
    # test_exemplify()
