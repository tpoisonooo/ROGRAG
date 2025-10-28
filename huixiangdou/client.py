import requests
import json
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
        # "history": [
        #     {
        #         "user": "今天是几月几号？",
        #         "assistant": "20250221",
        #         "references": []
        #     }
        # ]
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
    
    # 2. 测试文件添加到不同数据库
    print("\n\n2. 测试文件添加功能:")
    test_add_files_with_db()
    
    # 3. 测试清空不同数据库
    print("\n\n3. 测试清空数据库功能:")
    test_drop_db_with_db()


# 测试添加文件到指定数据库
def test_add_files_with_db():
    """测试添加文件到指定数据库"""
    url = f"{BASE_URL}/v2/add_files"
    headers = {"Content-Type": "application/json"}
    
    # 模拟文件列表（实际使用时需要真实文件路径）
    test_files = ["/path/to/test1.pdf", "/path/to/test2.txt"]
    
    # 测试添加到默认数据库
    request_body_default = {
        "file_list": test_files,
        "db_name": "HuixiangDou"
    }
    
    # 测试添加到自定义数据库
    request_body_custom = {
        "file_list": test_files,
        "db_name": "CustomDB"
    }
    
    print("\n测试添加文件到默认数据库:")
    print(f"Request: {json.dumps(request_body_default, ensure_ascii=False, indent=2)}")
    # response = requests.post(url, headers=headers, data=json.dumps(request_body_default))
    # print(f"Response: {response.text}")
    
    print("\n测试添加文件到自定义数据库:")
    print(f"Request: {json.dumps(request_body_custom, ensure_ascii=False, indent=2)}")
    # response = requests.post(url, headers=headers, data=json.dumps(request_body_custom))
    # print(f"Response: {response.text}")


# 测试清空指定数据库
def test_drop_db_with_db():
    """测试清空指定数据库"""
    url = f"{BASE_URL}/v2/drop_db"
    headers = {"Content-Type": "application/json"}
    
    # 测试清空默认数据库
    request_body_default = {
        "db_name": "HuixiangDou"
    }
    
    # 测试清空自定义数据库
    request_body_custom = {
        "db_name": "CustomDB"
    }
    
    print("\n测试清空默认数据库:")
    print(f"Request: {json.dumps(request_body_default, ensure_ascii=False, indent=2)}")
    # response = requests.post(url, headers=headers, data=json.dumps(request_body_default))
    # print(f"Response: {response.text}")
    
    print("\n测试清空自定义数据库:")
    print(f"Request: {json.dumps(request_body_custom, ensure_ascii=False, indent=2)}")
    # response = requests.post(url, headers=headers, data=json.dumps(request_body_custom))
    # print(f"Response: {response.text}")


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


# 主函数，运行测试
if __name__ == "__main__":
    import sys
    
    def print_usage():
        print("""
Usage: python client.py [option]
Options:
    basic           - 运行基础聊天测试（默认数据库）
    zh              - 运行中文聊天测试
    en              - 运行英文聊天测试  
    exemplify       - 运行exemplify测试
    parallel        - 运行并行测试
    multi-db        - 运行多数据库支持测试
    db-consistency  - 运行数据库切换一致性测试
    all             - 运行所有测试
    help            - 显示帮助信息
        """)
    
    # 获取命令行参数
    option = sys.argv[1] if len(sys.argv) > 1 else "basic"
    
    if option == "help":
        print_usage()
        sys.exit(0)
    
    elif option == "basic":
        print("=== 基础聊天测试 ===")
        test_chat_coref()
    
    elif option == "zh":
        print("=== 中文聊天测试 ===")
        test_chat_zh()
    
    elif option == "en":
        print("=== 英文聊天测试 ===")
        test_chat_en()
    
    elif option == "exemplify":
        print("=== Exemplify 测试 ===")
        test_exemplify()
    
    elif option == "parallel":
        print("=== 并行测试 ===")
        parallel_test_chat_coref(5)
    
    elif option == "multi-db":
        print("=== 多数据库支持测试 ===")
        test_multi_database_support()
    
    elif option == "db-consistency":
        print("=== 数据库切换一致性测试 ===")
        test_db_consistency()
    
    elif option == "all":
        print("=== 运行所有测试 ===")
        
        # 基础测试
        print("\n1. 基础聊天测试")
        test_chat_coref()
        
        print("\n2. 中文聊天测试")
        test_chat_zh()
        
        print("\n3. 英文聊天测试")
        test_chat_en()
        
        print("\n4. Exemplify 测试")
        test_exemplify()
        
        print("\n5. 并行测试")
        parallel_test_chat_coref(3)
        
        print("\n6. 多数据库支持测试")
        test_multi_database_support()
        
        print("\n7. 数据库切换一致性测试")
        test_db_consistency()
    
    else:
        print(f"未知选项: {option}")
        print_usage()
        sys.exit(1)


def test_export_graph(db_name=None, format_type='csv', export_dir='./export'):
    """测试图谱导出功能
    
    Args:
        db_name: 数据库名称，默认为 None 使用 HuixiangDou
        format_type: 导出格式，支持 'csv' 或 'json'，默认为 'csv'
        export_dir: 导出目录，默认为 './export'
    
    Returns:
        dict: 导出结果，包含 success、download_token 等信息
    """
    url = f"{BASE_URL}/v2/export_graph"
    headers = {"Content-Type": "application/json"}
    
    request_body = {
        "db_name": db_name or "HuixiangDou",
        "format": format_type,
        "export_dir": export_dir,
        "include_schema": True
    }
    
    print(f"测试导出数据库 {request_body['db_name']} 的图谱数据")
    print(f"导出格式: {format_type}")
    print(f"导出目录: {export_dir}")
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(request_body))
        result = response.json()
        
        if result.get('success'):
            print(f"✅ 导出成功")
            print(f"📊 导出文件: {result['data']['export_filename']}")
            print(f"📦 文件大小: {result['data']['file_size']} bytes")
            print(f"🔑 下载令牌: {result['data']['download_token']}")
            print(f"⏱️  导出耗时: {result['data']['export_time']}s")
        else:
            print(f"❌ 导出失败: {result.get('error', '未知错误')}")
            
        return result
        
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return {'success': False, 'error': str(e)}


def test_download_export(download_token, save_path=None):
    """测试导出文件下载功能
    
    Args:
        download_token: 下载令牌，从 export_graph 获得
        save_path: 保存路径，默认为 None 时使用服务器返回的文件名
    
    Returns:
        str: 保存的文件路径，失败返回 None
    """
    url = f"{BASE_URL}/v2/download_export/{download_token}"
    
    print(f"测试下载导出文件")
    print(f"下载令牌: {download_token}")
    
    try:
        response = requests.get(url, stream=True)
        
        if response.status_code == 200:
            # 从响应头获取文件名
            content_disposition = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[-1].strip('"')
            else:
                filename = f"export_{download_token}.csv"
            
            # 使用指定的保存路径或默认文件名
            if save_path:
                filename = save_path
            
            # 获取文件大小信息（如果有）
            file_size = response.headers.get('X-File-Size')
            db_name = response.headers.get('X-Database-Name')
            
            print(f"📁 保存文件名: {filename}")
            if file_size:
                print(f"📊 文件大小: {file_size} bytes")
            if db_name:
                print(f"🗄️  来源数据库: {db_name}")
            
            # 流式下载文件
            total_bytes = 0
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_bytes += len(chunk)
                        # 显示进度
                        if file_size and int(file_size) > 0:
                            progress = (total_bytes / int(file_size)) * 100
                            print(f"\r📥 下载进度: {progress:.1f}%", end='', flush=True)
            
            print(f"\n✅ 下载完成: {total_bytes} bytes")
            print(f"📂 保存路径: {os.path.abspath(filename)}")
            return filename
            
        else:
            print(f"❌ 下载失败: HTTP {response.status_code}")
            error_detail = response.text
            if error_detail:
                print(f"错误详情: {error_detail}")
            return None
            
    except Exception as e:
        print(f"❌ 下载请求失败: {str(e)}")
        return None


def test_export_workflow():
    """测试完整的导出和下载工作流程
    
    1. 导出图谱到指定格式
    2. 获取下载令牌
    3. 下载导出的文件
    """
    print("=== 测试完整导出工作流程 ===")
    print("这个测试将演示：")
    print("1. 导出数据库图谱到 CSV 文件")
    print("2. 获取下载令牌")
    print("3. 下载导出的文件到本地")
    print()
    
    # 测试参数
    test_db = "TestDB"
    test_format = "csv"
    test_export_dir = "./export_test"
    
    print(f"📋 测试参数:")
    print(f"   数据库: {test_db}")
    print(f"   导出格式: {test_format}")
    print(f"   导出目录: {test_export_dir}")
    print()
    
    # 第一步：导出图谱
    print("第一步：导出图谱...")
    export_result = test_export_graph(
        db_name=test_db,
        format_type=test_format,
        export_dir=test_export_dir
    )
    
    if not export_result.get('success'):
        print("❌ 导出失败，工作流程终止")
        return False
    
    # 第二步：获取下载令牌并下载文件
    print("\n第二步：下载导出的文件...")
    download_token = export_result['data']['download_token']
    
    # 构建保存路径
    original_filename = export_result['data']['export_filename']
    save_filename = f"downloaded_{original_filename}"
    
    downloaded_file = test_download_export(download_token, save_path=save_filename)
    
    if downloaded_file:
        print(f"\n🎉 完整工作流程测试成功！")
        print(f"📊 导出文件: {original_filename}")
        print(f"📁 下载文件: {downloaded_file}")
        
        # 验证文件
        if os.path.exists(downloaded_file):
            file_size = os.path.getsize(downloaded_file)
            print(f"✅ 文件验证: 存在，大小 {file_size} bytes")
            
            # 可选：显示文件前几行内容（如果是文本文件）
            if downloaded_file.endswith('.csv'):
                try:
                    with open(downloaded_file, 'r', encoding='utf-8') as f:
                        first_lines = [f.readline().strip() for _ in range(3)]
                    print("📄 文件预览:")
                    for i, line in enumerate(first_lines, 1):
                        if line:
                            print(f"   {i}: {line[:100]}...")
                except Exception as e:
                    print(f"⚠️  文件预览失败: {e}")
        
        # 清理测试文件（可选）
        cleanup = input("\n是否删除测试文件？(y/n): ").lower().strip()
        if cleanup == 'y':
            try:
                os.remove(downloaded_file)
                print(f"🗑️  已删除测试文件: {downloaded_file}")
            except Exception as e:
                print(f"⚠️  清理失败: {e}")
        
        return True
    else:
        print("❌ 下载失败，工作流程终止")
        return False


# 更新主函数菜单和帮助信息
def print_usage():
    """打印使用说明"""
    print("""
用法: python client.py [选项]

选项:
  coref           - 运行coreference测试
  chat            - 运行聊天测试（中文和英文）
  exemplify       - 运行exemplify测试
  parallel        - 运行并行测试
  multi_db        - 运行多数据库支持测试
  consistency     - 运行数据库一致性测试
  export          - 运行图谱导出测试
  download        - 运行文件下载测试（需要先运行导出获得token）
  export_workflow - 运行完整导出流程测试
  all             - 运行所有测试
  
示例:
  python client.py chat                    # 运行聊天测试
  python client.py export                  # 运行导出测试
  python client.py export_workflow         # 运行完整流程测试
  python client.py download                # 运行下载测试
""")


def main():
    """主函数 - 更新以支持新的导出功能"""
    import sys
    
    if len(sys.argv) < 2:
        print_usage()
        return
    
    option = sys.argv[1].lower()
    
    if option == "coref":
        test_chat_coref()
    elif option == "chat":
        print("=== 运行聊天测试 ===")
        print("\n1. 中文聊天测试")
        test_chat_zh()
        print("\n2. 英文聊天测试")
        test_chat_en()
    elif option == "exemplify":
        test_exemplify()
    elif option == "parallel":
        parallel_test_chat_coref(5)
    elif option == "multi_db":
        test_multi_database_support()
    elif option == "consistency":
        test_db_consistency()
    elif option == "export":
        test_export_graph()
    elif option == "download":
        if len(sys.argv) < 3:
            print("❌ 请提供下载令牌")
            print("用法: python client.py download <download_token>")
            return
        download_token = sys.argv[2]
        test_download_export(download_token)
    elif option == "export_workflow":
        test_export_workflow()
    elif option == "all":
        print("=== 运行所有测试 ===")
        print("\n1. Coreference测试")
        test_chat_coref()
        print("\n2. 中文聊天测试")
        test_chat_zh()
        print("\n3. 英文聊天测试")
        test_chat_en()
        print("\n4. Exemplify测试")
        test_exemplify()
        print("\n5. 并行测试")
        parallel_test_chat_coref(3)
        print("\n6. 多数据库支持测试")
        test_multi_database_support()
        print("\n7. 数据库切换一致性测试")
        test_db_consistency()
        print("\n8. 图谱导出测试")
        test_export_graph()
    else:
        print(f"未知选项: {option}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
