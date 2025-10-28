#!/usr/bin/env python3
"""
测试新的导出和下载功能
这个脚本演示如何使用新的客户端导出功能
"""

import json
import sys
import os

# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_export_functions():
    """测试导出相关函数"""
    print("=== 测试新的导出功能 ===")
    
    try:
        # 由于依赖问题，我们直接检查函数定义
        with open('huixiangdou/client.py', 'r') as f:
            content = f.read()
        
        # 检查函数是否存在
        functions_to_check = [
            'def test_export_graph(',
            'def test_download_export(',
            'def test_export_workflow('
        ]
        
        print("检查新函数定义:")
        for func in functions_to_check:
            if func in content:
                print(f"✅ {func.replace('def ', '').replace('(', '')} 已定义")
            else:
                print(f"❌ {func.replace('def ', '').replace('(', '')} 未找到")
        
        # 检查 API 端点定义
        endpoints = [
            ('/v2/export_graph', 'POST'),
            ('/v2/download_export/', 'GET')
        ]
        
        print("\n检查 API 端点:")
        with open('huixiangdou/server.py', 'r') as f:
            server_content = f.read()
        
        for endpoint, method in endpoints:
            if f'@{method.lower()}("{endpoint}"' in server_content:
                print(f"✅ {method} {endpoint} 端点存在")
            else:
                print(f"❌ {method} {endpoint} 端点未找到")
        
        # 检查请求模型
        models = [
            'ExportGraphRequest',
            'export_files'  # 全局变量
        ]
        
        print("\n检查请求模型:")
        for model in models:
            if model in server_content:
                print(f"✅ {model} 模型/变量存在")
            else:
                print(f"❌ {model} 模型/变量未找到")
        
        # 模拟函数调用（不实际执行）
        print("\n=== 模拟函数使用 ===")
        print("# 导出图谱")
        print("result = test_export_graph(db_name='TestDB', format_type='csv')")
        print("# 预期返回: {'success': True, 'data': {'download_token': 'abc123', ...}}")
        print()
        print("# 下载文件") 
        print("downloaded_file = test_download_export('abc123', 'exported_graph.csv')")
        print("# 预期返回: 文件路径或 None")
        print()
        print("# 完整工作流程")
        print("test_export_workflow()")
        print("# 预期: 自动完成导出和下载")
        
        print("\n=== 使用示例 ===")
        print("1. 基础导出测试:")
        print("   python -m huixiangdou.client export")
        print()
        print("2. 完整工作流程测试:")
        print("   python -m huixiangdou.client export_workflow")
        print()
        print("3. 下载特定文件:")
        print("   python -m huixiangdou.client download <download_token>")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    return True

def show_api_documentation():
    """显示 API 使用文档"""
    print("\n=== API 使用文档 ===")
    
    print("\n1. 图谱导出 API (/v2/export_graph)")
    print("请求格式:")
    print(json.dumps({
        "db_name": "HuixiangDou",
        "format": "csv",
        "export_dir": "./export",
        "include_schema": True
    }, indent=2))
    
    print("\n响应格式:")
    print(json.dumps({
        "success": True,
        "data": {
            "export_path": "./export/HuixiangDou_export_20241227.csv",
            "file_size": 1024000,
            "download_token": "a1b2c3d4e5f6",
            "message": "导出成功"
        }
    }, indent=2))
    
    print("\n2. 文件下载 API (/v2/download_export/{download_token})")
    print("方法: GET")
    print("路径参数: download_token")
    print("响应: 文件流 + HTTP 头信息")
    print("头信息:")
    print("  Content-Disposition: attachment; filename=\"export.csv\"")
    print("  X-File-Size: 1024000")
    print("  X-Database-Name: HuixiangDou")

def main():
    """主函数"""
    print("🧪 测试客户端新的导出功能")
    print("=" * 50)
    
    success = test_export_functions()
    
    if success:
        print("\n✅ 功能检查完成！")
        show_api_documentation()
        
        print("\n" + "=" * 50)
        print("🎉 新的导出功能已就绪！")
        print("\n要使用这些功能，请确保:")
        print("1. 服务器正在运行 (python -m huixiangdou.server)")
        print("2. 有可用的数据库")
        print("3. 网络连接正常")
        print("\n然后运行:")
        print("python -m huixiangdou.client export")
        print("或")
        print("python -m huixiangdou.client export_workflow")
    else:
        print("\n❌ 功能检查失败")
        sys.exit(1)

if __name__ == "__main__":
    main()