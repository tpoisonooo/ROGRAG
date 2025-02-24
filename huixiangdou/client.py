import requests
import json

# 基础 URL
BASE_URL = "http://127.0.0.1:23334"


# 测试 /v2/chat 接口
def test_chat_coref():
    url = f"{BASE_URL}/v2/chat"
    headers = {"Content-Type": "application/json"}

    # 示例请求体
    request_body = {
        "language":
        "en",
        "enable_web_search":
        False,
        "user":
        "它有什么特点？",
        "history": [{
            "user": "蚕豆如何种植？",
            "assistant":
            "本发明提出了一种蚕豆的种植方法，包括选地及整地、选种及处理、播种、肥水管理、植株管理、病虫害防治、适时采收等步骤，通过前期合理施加混合基料和基肥，大大改善了土地的肥沃性，降低了板结度，配合后期科学合理的肥水管理显著提高了蚕豆的出苗率和生长速率，另外，对土地、种子及种植初期的杀菌处理，大大减轻了病虫害的发生率，采用本发明种植方法种植的蚕豆饱满度高、虫害率低，植株长势均匀，且相较于传统的蚕豆种植，亩产量提高了30％左右。",
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


# 测试 /v2/chat 接口
def test_chat_zh():
    url = f"{BASE_URL}/v2/chat"
    headers = {"Content-Type": "application/json"}

    # 示例请求体
    request_body = {
        "language": "zh_CN",
        "enable_web_search": False,
        "user": "OsGL1-1 和OsGL1-11有什么区别",
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
        "language": "zh_CN",
        "enable_web_search": False,
        "user": "汕优63的最佳播期是什么时候？\nA. 7月下旬\nB. 6月下旬\nC. 8月下旬\nD. 9月下旬",
        "history": []
    }

    response = requests.post(url,
                             headers=headers,
                             data=json.dumps(request_body))
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")


# 主函数，运行测试
if __name__ == "__main__":
    test_chat_coref()

    # print("Testing /v2/chat endpoint...")
    # test_chat_zh()

    # print("Testing /v2/chat endpoint...")
    # test_chat_en()

    print("\nTesting /v2/exemplify endpoint...")
    test_exemplify()
