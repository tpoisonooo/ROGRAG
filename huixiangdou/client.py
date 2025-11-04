import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# 基础 URL
BASE_URL = "http://127.0.0.1:23333"

# 测试 /v2/chat 接口
def test_chat_coref(db_name=None):
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
    
    # 如果指定了数据库名称，添加到请求体
    if db_name:
        request_body["db_name"] = db_name

    print(f"Testing /v2/chat endpoint with db_name: {db_name or 'default'}")
    response = requests.post(url,
                             headers=headers,
                             data=json.dumps(request_body))
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8")
            print(decoded_line)

# 测试 /v2/chat 接口
def test_chat_zh(db_name=None):
    url = f"{BASE_URL}/v2/chat"
    headers = {"Content-Type": "application/json"}

    # 示例请求体
    request_body = {
        "language": "zh_CN",
        "enable_web_search": False,
        "user": "OsGL1-1 和OsGL1-11有什么区别",
        "history": []
    }
    
    # 如果指定了数据库名称，添加到请求体
    if db_name:
        request_body["db_name"] = db_name

    print(f"Testing /v2/chat endpoint (Chinese) with db_name: {db_name or 'default'}")
    response = requests.post(url,
                             headers=headers,
                             data=json.dumps(request_body))
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8")
            print(decoded_line)

# 测试 /v2/chat 接口
def test_chat_en(db_name=None):
    url = f"{BASE_URL}/v2/chat"
    headers = {"Content-Type": "application/json"}

    # 示例请求体
    request_body = {
        "language": "en",
        "enable_web_search": False,
        "user": "What should I call you?",
        "history": [{
            "user": "what day is today?",
            "assistant": "20250221",
            "references": []
        }]
    }
    
    # 如果指定了数据库名称，添加到请求体
    if db_name:
        request_body["db_name"] = db_name

    print(f"Testing /v2/chat endpoint (English) with db_name: {db_name or 'default'}")
    response = requests.post(url,
                             headers=headers,
                             data=json.dumps(request_body))
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8")
            print(decoded_line)

# 测试 /v2/exemplify 接口
def test_exemplify(db_name=None):
    url = f"{BASE_URL}/v2/exemplify"
    headers = {"Content-Type": "application/json"}

    # 示例请求体
    request_body = {
        "language": "zh_CN",
        "enable_web_search": False,
        "user": "汕优63的最佳播期是什么时候？\nA. 7月下旬\nB. 6月下旬\nC. 8月下旬\nD. 9月下旬",
        "history": []
    }
    
    # 如果指定了数据库名称，添加到请求体
    if db_name:
        request_body["db_name"] = db_name

    print(f"Testing /v2/exemplify endpoint with db_name: {db_name or 'default'}")
    response = requests.post(url,
                             headers=headers,
                             data=json.dumps(request_body))
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

# 测试 /v2/list_file 接口
def test_list_files(db_name=None):
    """测试列出文件功能"""
    url = f"{BASE_URL}/v2/list_file"
    params = {}
    if db_name:
        params["db_name"] = db_name
    
    print(f"Testing /v2/list_file endpoint with db_name: {db_name or 'default'}")
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        files = response.json()
        print(f"Files in database: {files}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# 测试 /v2/list_db 接口
def test_list_databases():
    """测试列出数据库功能"""
    url = f"{BASE_URL}/v2/list_db"
    
    print("Testing /v2/list_db endpoint")
    response = requests.post(url)
    
    if response.status_code == 200:
        databases = response.json()
        print(f"Available databases: {databases}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# 测试 /v2/add_files 接口
def test_add_files(file_list, db_name=None):
    """测试添加文件功能"""
    url = f"{BASE_URL}/v2/add_files"
    headers = {"Content-Type": "application/json"}
    
    request_body = {
        "file_list": file_list
    }
    if db_name:
        request_body["db_name"] = db_name
    
    print(f"Testing /v2/add_files endpoint with db_name: {db_name or 'default'}")
    print(f"Files to add: {file_list}")
    
    response = requests.post(url, headers=headers, data=json.dumps(request_body), stream=True)
    
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                if decoded_line.startswith("data:"):
                    try:
                        data = json.loads(decoded_line[5:])
                        if 'data' in data:
                            progress = data['data'].get('progress', 0)
                            message = data['data'].get('message', '')
                            print(f"Progress: {progress*100:.1f}% - {message}")
                    except:
                        print(decoded_line)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# 测试 /v2/drop_db 接口
def test_drop_db(db_name=None):
    """测试清空数据库功能"""
    url = f"{BASE_URL}/v2/drop_db"
    headers = {"Content-Type": "application/json"}
    
    request_body = {}
    if db_name:
        request_body["db_name"] = db_name
    
    print(f"Testing /v2/drop_db endpoint with db_name: {db_name or 'default'}")
    response = requests.post(url, headers=headers, data=json.dumps(request_body))
    
    if response.status_code == 200:
        result = response.text
        print(f"Drop database result: {result}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# 并行化测试函数
def parallel_test_chat_coref(num_requests, db_name=None):
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(test_chat_coref, db_name) for _ in range(num_requests)]
        for future in as_completed(futures):
            try:
                response = future.result()
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        print(decoded_line)
            except Exception as e:
                print(f"Request failed: {e}")

# 测试多数据库切换功能
def test_multi_database_support():
    """测试多数据库支持功能"""
    print("\n=== 多数据库支持测试 ===")
    
    # 测试数据库名称
    test_dbs = ["HuixiangDou", "TestDB1", "TestDB2"]
    
    # 1. 测试不同数据库的聊天功能
    print("\n1. 测试不同数据库的聊天功能:")
    for db_name in test_dbs:
        print(f"\n--- 测试数据库: {db_name} ---")
        test_chat_zh(db_name=db_name)
    
    # 2. 测试文件列表功能
    print("\n\n2. 测试文件列表功能:")
    for db_name in test_dbs:
        print(f"\n--- 数据库文件列表: {db_name} ---")
        test_list_files(db_name=db_name)
    
    # 3. 测试列出所有数据库
    print("\n\n3. 测试列出所有数据库:")
    test_list_databases()

# 测试数据库切换的一致性
def test_db_consistency():
    """测试数据库切换的一致性"""
    print("\n=== 数据库切换一致性测试 ===")
    
    # 在同一个会话中切换不同的数据库
    questions = [
        ("HuixiangDou", "什么是机器学习？"),
        ("TestDB", "什么是深度学习？"),
        ("HuixiangDou", "刚才我们聊到了什么？")  # 回到默认数据库
    ]
    
    for db_name, question in questions:
        print(f"\n--- 数据库: {db_name}, 问题: {question} ---")
        test_single_chat(question, "zh_CN", db_name)

# 单次聊天测试函数
def test_single_chat(question, language="zh_CN", db_name=None):
    """单次聊天测试"""
    url = f"{BASE_URL}/v2/chat"
    headers = {"Content-Type": "application/json"}
    
    request_body = {
        "language": language,
        "enable_web_search": False,
        "user": question,
        "history": []
    }
    
    if db_name:
        request_body["db_name"] = db_name
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(request_body), timeout=30)
        result_lines = []
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                result_lines.append(decoded_line)
        return result_lines
    except Exception as e:
        print(f"Error: {e}")
        return []

# 导出图谱测试函数
def test_export_graph(db_name=None):
    """测试图谱导出功能"""
    url = f"{BASE_URL}/v2/export_graph"
    params = {}
    if db_name:
        params["db_name"] = db_name
    
    print(f"Testing /v2/export_graph endpoint with db_name: {db_name or 'default'}")
    response = requests.post(url, params=params)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('status', {}).get('code') == 0:
            print(f"✅ Export successful!")
            print(f"📊 Export path: {result['data']['export_path']}")
            print(f"📦 File size: {result['data']['file_size']} bytes")
            print(f"🔑 Download token: {result['data']['download_url'].split('/')[-1]}")
            return result['data']['download_url'].split('/')[-1]
        else:
            print(f"❌ Export failed: {result.get('status', {}).get('error', 'Unknown error')}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    return None

# 下载导出文件测试函数
def test_download_export(download_token, save_path=None):
    """测试下载导出文件功能"""
    url = f"{BASE_URL}/v2/download_export/{download_token}"
    
    print(f"Testing /v2/download_export endpoint with token: {download_token}")
    
    try:
        response = requests.get(url, stream=True)
        
        if response.status_code == 200:
            # 从响应头获取文件名
            content_disposition = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[-1].strip('"')
            else:
                filename = f"export_{download_token}.zip"
            
            # 使用指定的保存路径或默认文件名
            if save_path:
                filename = save_path
            
            print(f"📁 Saving file: {filename}")
            
            # 流式下载文件
            total_bytes = 0
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_bytes += len(chunk)
                        print(f"\r📥 Downloaded: {total_bytes} bytes", end='', flush=True)
            
            print(f"\n✅ Download complete: {total_bytes} bytes")
            print(f"📂 Saved to: {os.path.abspath(filename)}")
            return filename
            
        else:
            print(f"❌ Download failed: HTTP {response.status_code}")
            error_detail = response.text
            if error_detail:
                print(f"Error details: {error_detail}")
            return None
            
    except Exception as e:
        print(f"❌ Download request failed: {str(e)}")
        return None

# 测试完整的导出工作流程
def test_export_workflow():
    """测试完整的导出和下载工作流程"""
    print("=== 测试完整导出工作流程 ===")
    print("步骤:")
    print("1. 导出图谱数据")
    print("2. 下载导出的文件")
    print()
    
    # 第一步：导出图谱
    print("第一步：导出图谱数据...")
    download_token = test_export_graph()
    
    if download_token:
        # 第二步：下载文件
        print("\n第二步：下载导出的文件...")
        downloaded_file = test_download_export(download_token)
        
        if downloaded_file:
            print(f"\n🎉 完整工作流程测试成功！")
            print(f"📁 下载文件: {downloaded_file}")
            
            # 清理测试文件
            try:
                os.remove(downloaded_file)
                print(f"🗑️  已清理测试文件: {downloaded_file}")
            except Exception as e:
                print(f"⚠️  清理失败: {e}")
            
            return True
        else:
            print("❌ 下载失败")
    else:
        print("❌ 导出失败")
    
    return False

# 打印使用说明
def print_usage():
    print("""
用法: python client.py [选项] [参数]

选项:
  chat [db_name]              - 运行聊天测试（可选指定数据库）
  zh [db_name]                - 运行中文聊天测试
  en [db_name]                - 运行英文聊天测试  
  exemplify [db_name]         - 运行exemplify测试
  list_files [db_name]        - 列出数据库文件
  list_db                     - 列出所有数据库
  add_files <file1,file2> [db_name] - 添加文件到数据库
  drop_db [db_name]           - 清空数据库
  export [db_name]            - 导出图谱数据
  download <token> [save_path] - 下载导出文件
  export_workflow [db_name]   - 运行完整导出流程测试
  multi_db                    - 运行多数据库支持测试
  consistency                 - 运行数据库切换一致性测试
  parallel <num> [db_name]    - 运行并行测试
  all                         - 运行所有测试
  help                        - 显示帮助信息

示例:
  python client.py chat                    # 运行聊天测试（默认数据库）
  python client.py chat TestDB             # 在TestDB数据库上运行聊天测试
  python client.py add_files /path/file.pdf # 添加单个文件
  python client.py add_files file1.pdf,file2.txt TestDB  # 添加多个文件到指定数据库
  python client.py export TestDB           # 导出TestDB的图谱
  python client.py download abc123         # 下载令牌为abc123的文件
  python client.py parallel 5              # 运行5个并行请求
""")

# 主函数
def main():
    import sys
    
    if len(sys.argv) < 2:
        print_usage()
        return
    
    option = sys.argv[1].lower()
    
    if option == "help":
        print_usage()
    
    elif option == "chat":
        db_name = sys.argv[2] if len(sys.argv) > 2 else None
        print(f"=== 运行聊天测试 (数据库: {db_name or 'default'}) ===")
        test_chat_coref(db_name)
    
    elif option == "zh":
        db_name = sys.argv[2] if len(sys.argv) > 2 else None
        print(f"=== 运行中文聊天测试 (数据库: {db_name or 'default'}) ===")
        test_chat_zh(db_name)
    
    elif option == "en":
        db_name = sys.argv[2] if len(sys.argv) > 2 else None
        print(f"=== 运行英文聊天测试 (数据库: {db_name or 'default'}) ===")
        test_chat_en(db_name)
    
    elif option == "exemplify":
        db_name = sys.argv[2] if len(sys.argv) > 2 else None
        print(f"=== 运行Exemplify测试 (数据库: {db_name or 'default'}) ===")
        test_exemplify(db_name)
    
    elif option == "list_files":
        db_name = sys.argv[2] if len(sys.argv) > 2 else None
        print(f"=== 列出数据库文件 (数据库: {db_name or 'default'}) ===")
        test_list_files(db_name)
    
    elif option == "list_db":
        print("=== 列出所有数据库 ===")
        test_list_databases()
    
    elif option == "add_files":
        if len(sys.argv) < 3:
            print("❌ 请提供文件路径")
            print("用法: python client.py add_files <file1,file2> [db_name]")
            return
        
        file_paths = sys.argv[2].split(',')
        db_name = sys.argv[3] if len(sys.argv) > 3 else None
        
        print(f"=== 添加文件到数据库 (数据库: {db_name or 'default'}) ===")
        test_add_files(file_paths, db_name)
    
    elif option == "drop_db":
        db_name = sys.argv[2] if len(sys.argv) > 2 else None
        print(f"=== 清空数据库 (数据库: {db_name or 'default'}) ===")
        test_drop_db(db_name)
    
    elif option == "export":
        db_name = sys.argv[2] if len(sys.argv) > 2 else None
        print(f"=== 导出图谱数据 (数据库: {db_name or 'default'}) ===")
        test_export_graph(db_name)
    
    elif option == "download":
        if len(sys.argv) < 3:
            print("❌ 请提供下载令牌")
            print("用法: python client.py download <token> [save_path]")
            return
        
        download_token = sys.argv[2]
        save_path = sys.argv[3] if len(sys.argv) > 3 else None
        
        print(f"=== 下载导出文件 ===")
        test_download_export(download_token, save_path)
    
    elif option == "export_workflow":
        db_name = sys.argv[2] if len(sys.argv) > 2 else None
        print(f"=== 测试完整导出工作流程 (数据库: {db_name or 'default'}) ===")
        test_export_workflow()
    
    elif option == "multi_db":
        print("=== 运行多数据库支持测试 ===")
        test_multi_database_support()
    
    elif option == "consistency":
        print("=== 运行数据库切换一致性测试 ===")
        test_db_consistency()
    
    elif option == "parallel":
        if len(sys.argv) < 3:
            print("❌ 请提供并行请求数量")
            print("用法: python client.py parallel <num> [db_name]")
            return
        
        try:
            num_requests = int(sys.argv[2])
        except ValueError:
            print("❌ 并行请求数量必须是整数")
            return
        
        db_name = sys.argv[3] if len(sys.argv) > 3 else None
        
        print(f"=== 运行并行测试 ({num_requests} 个请求, 数据库: {db_name or 'default'}) ===")
        parallel_test_chat_coref(num_requests, db_name)
    
    elif option == "all":
        print("=== 运行所有测试 ===")
        
        # 基础功能测试
        print("\n1. 基础聊天测试")
        test_chat_coref()
        
        print("\n2. 中文聊天测试")
        test_chat_zh()
        
        print("\n3. 英文聊天测试")
        test_chat_en()
        
        print("\n4. Exemplify测试")
        test_exemplify()
        
        print("\n5. 文件列表测试")
        test_list_files()
        
        print("\n6. 数据库列表测试")
        test_list_databases()
        
        print("\n7. 多数据库支持测试")
        test_multi_database_support()
        
        print("\n8. 数据库切换一致性测试")
        test_db_consistency()
        
        print("\n9. 并行测试 (3个请求)")
        parallel_test_chat_coref(3)
        
        print("\n10. 图谱导出测试")
        test_export_graph()
    
    else:
        print(f"未知选项: {option}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()