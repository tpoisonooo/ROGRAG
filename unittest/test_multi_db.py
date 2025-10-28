#!/usr/bin/env python3
"""Test script for multi-database support in ROGRAG API endpoints."""

import requests
import json
import os

def test_chat_endpoint():
    """Test /v2/chat endpoint with different databases."""
    url = "http://localhost:23333/v2/chat"
    
    # Test request to default database
    payload_default = {
        "language": "zh_cn",
        "enable_web_search": False,
        "user": "什么是机器学习？",
        "history": [],
        "db_name": "HuixiangDou"  # 默认数据库
    }
    
    # Test request to custom database
    payload_custom = {
        "language": "zh_cn", 
        "enable_web_search": False,
        "user": "什么是深度学习？",
        "history": [],
        "db_name": "CustomDB"  # 自定义数据库
    }
    
    print("Testing /v2/chat endpoint...")
    print(f"Default DB request: {json.dumps(payload_default, ensure_ascii=False, indent=2)}")
    print(f"Custom DB request: {json.dumps(payload_custom, ensure_ascii=False, indent=2)}")
    print("Note: This is a demo script. Actual API calls require a running server.")


def test_add_files_endpoint():
    """Test /v2/add_files endpoint with different databases."""
    url = "http://localhost:23333/v2/add_files"
    
    # Test request to default database
    payload_default = {
        "file_list": ["/path/to/file1.pdf", "/path/to/file2.txt"],
        "db_name": "HuixiangDou"  # 默认数据库
    }
    
    # Test request to custom database
    payload_custom = {
        "file_list": ["/path/to/file3.docx", "/path/to/file4.md"],
        "db_name": "CustomDB"  # 自定义数据库
    }
    
    print("\nTesting /v2/add_files endpoint...")
    print(f"Default DB request: {json.dumps(payload_default, ensure_ascii=False, indent=2)}")
    print(f"Custom DB request: {json.dumps(payload_custom, ensure_ascii=False, indent=2)}")


def test_drop_db_endpoint():
    """Test /v2/drop_db endpoint with different databases."""
    url = "http://localhost:23333/v2/drop_db"
    
    # Test request to default database
    payload_default = {
        "db_name": "HuixiangDou"  # 默认数据库
    }
    
    # Test request to custom database
    payload_custom = {
        "db_name": "CustomDB"  # 自定义数据库
    }
    
    print("\nTesting /v2/drop_db endpoint...")
    print(f"Default DB request: {json.dumps(payload_default, ensure_ascii=False, indent=2)}")
    print(f"Custom DB request: {json.dumps(payload_custom, ensure_ascii=False, indent=2)}")


def main():
    """Main test function."""
    print("ROGRAG Multi-Database Support Test")
    print("=" * 40)
    
    test_chat_endpoint()
    test_add_files_endpoint()
    test_drop_db_endpoint()
    
    print("\n" + "=" * 40)
    print("Test script completed.")
    print("\nAPI Usage Examples:")
    print("1. Chat with specific database:")
    print('   curl -X POST "http://localhost:23333/v2/chat" -H "Content-Type: application/json" -d \'{"language": "zh_cn", "enable_web_search": false, "user": "什么是机器学习？", "history": [], "db_name": "CustomDB"}\'')
    print("\n2. Add files to specific database:")
    print('   curl -X POST "http://localhost:23333/v2/add_files" -H "Content-Type: application/json" -d \'{"file_list": ["/path/to/file.pdf"], "db_name": "CustomDB"}\'')
    print("\n3. Drop specific database:")
    print('   curl -X POST "http://localhost:23333/v2/drop_db" -H "Content-Type: application/json" -d \'{"db_name": "CustomDB"}\'')


if __name__ == "__main__":
    main()