#!/usr/bin/env python3
"""
ROGRAG 图谱导出功能测试脚本
测试 /v2/export_graph 和下载功能
"""

import requests
import json
import time
import os

# API 基础地址
BASE_URL = "http://127.0.0.1:23333"

def test_export_default_db():
    """测试默认数据库导出"""
    print("=" * 60)
    print("测试默认数据库图谱导出")
    print("=" * 60)
    
    url = f"{BASE_URL}/v2/export_graph"
    headers = {"Content-Type": "application/json"}
    
    # 默认请求（不指定数据库）
    request_body = {
        "format": "csv",
        "export_dir": "./export",
        "include_schema": True
    }
    
    print(f"请求 URL: {url}")
    print(f"请求体: {json.dumps(request_body, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(request_body))
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status", {}).get("code") == 0:
                data = result.get("data", {})
                download_token = data.get("download_token")
                export_path = data.get("export_path")
                file_size = data.get("file_size")
                
                print(f"✅ 导出成功!")
                print(f"📁 导出文件路径: {export_path}")
                print(f"📊 文件大小: {file_size} bytes")
                print(f"🔑 下载令牌: {download_token}")
                
                return download_token
            else:
                print(f"❌ 导出失败: {result.get('status', {}).get('error')}")
                return None
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return None

def test_export_custom_db():
    """测试自定义数据库导出"""
    print("\n" + "=" * 60)
    print("测试自定义数据库图谱导出")
    print("=" * 60)
    
    url = f"{BASE_URL}/v2/export_graph"
    headers = {"Content-Type": "application/json"}
    
    # 自定义数据库请求
    request_body = {
        "db_name": "TestDB",
        "format": "json",
        "export_dir": "./export_test",
        "include_schema": True
    }
    
    print(f"请求 URL: {url}")
    print(f"请求体: {json.dumps(request_body, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(request_body))
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get("status", {}).get("code") == 0:
                print("✅ 自定义数据库导出请求成功!")
                return result.get("data", {}).get("download_token")
            else:
                print(f"❌ 导出失败: {result.get('status', {}).get('error')}")
                return None
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return None

def test_download_export(download_token: str):
    """测试下载导出文件"""
    print(f"\n" + "=" * 60)
    print(f"测试下载导出文件 (令牌: {download_token})")
    print("=" * 60)
    
    # 直接下载文件
    download_url = f"{BASE_URL}/v2/download_export/{download_token}"
    print(f"开始下载文件: {download_url}")
    
    try:
        download_response = requests.get(download_url, stream=True)
        print(f"文件下载请求状态码: {download_response.status_code}")
        
        if download_response.status_code == 200:
            # 从响应头获取文件信息（如果可用）
            content_disposition = download_response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                file_name = content_disposition.split('filename=')[1].strip('"')
            else:
                file_name = f"exported_graph_{download_token}.csv"  # 默认文件名
            
            # 从响应头获取文件大小（如果可用）
            file_size = int(download_response.headers.get('X-File-Size', 0))
            
            print(f"📁 文件名: {file_name}")
            if file_size > 0:
                print(f"📊 文件大小: {file_size} bytes")
            
            # 保存文件
            save_path = f"./downloaded_{file_name}"
            with open(save_path, 'wb') as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # 验证文件大小
            downloaded_size = os.path.getsize(save_path)
            print(f"✅ 文件下载成功!")
            print(f"📁 保存路径: {save_path}")
            print(f"📊 实际下载文件大小: {downloaded_size} bytes")
            
            if file_size > 0 and downloaded_size == file_size:
                print("✅ 文件大小验证通过!")
            elif file_size > 0:
                print(f"⚠️  文件大小不匹配: 期望 {file_size}, 实际 {downloaded_size}")
            
            return save_path
        else:
            # 处理错误响应
            try:
                error_result = download_response.json()
                print(f"❌ 文件下载失败: {error_result}")
            except:
                print(f"❌ 文件下载失败，状态码: {download_response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 下载异常: {str(e)}")
        return None

def test_invalid_token():
    """测试无效的下载令牌"""
    print("\n" + "=" * 60)
    print("测试无效的下载令牌")
    print("=" * 60)
    
    invalid_token = "invalid_token_12345"
    info_url = f"{BASE_URL}/v2/download_export/{invalid_token}"
    
    try:
        response = requests.get(info_url)
        print(f"请求状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get("status", {}).get("code") != 0:
                print("✅ 无效令牌正确处理!")
            else:
                print("❌ 无效令牌未正确处理")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")

def main():
    """主测试函数"""
    print("ROGRAG 图谱导出功能测试")
    print("=" * 60)
    print("注意: 确保 ROGRAG 服务器正在运行")
    print("=" * 60)
    
    # 测试1: 默认数据库导出
    download_token = test_export_default_db()
    
    if download_token:
        # 测试2: 文件下载
        downloaded_file = test_download_export(download_token)
        
        if downloaded_file and os.path.exists(downloaded_file):
            print(f"\n✅ 完整测试通过!")
            print(f"📁 下载的文件保存在: {downloaded_file}")
            
            # 可选：显示文件内容预览
            try:
                with open(downloaded_file, 'r', encoding='utf-8') as f:
                    preview = f.read(500)  # 读取前500字符
                print(f"\n📄 文件内容预览:")
                print(preview)
                if len(preview) == 500:
                    print("...")
            except Exception as e:
                print(f"无法预览文件内容: {e}")
        else:
            print("\n❌ 文件下载测试失败")
    else:
        print("\n❌ 默认数据库导出测试失败")
    
    # 测试3: 自定义数据库导出
    custom_token = test_export_custom_db()
    if custom_token:
        print("\n✅ 自定义数据库导出测试通过!")
    
    # 测试4: 无效令牌测试
    test_invalid_token()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()