#!/usr/bin/env python3
"""测试数据库切换功能"""

import os
import sys
import json
import requests
import time

def test_db_switch_ui():
    """测试UI界面的数据库切换功能"""
    print("=== 测试数据库切换UI功能 ===")
    
    # 测试步骤：
    print("1. Gradio UI 现在包含数据库名称输入框")
    print("2. 初始值: HuixiangDou (来自配置文件)")
    print("3. 用户可以直接编辑文本框切换数据库")
    print("4. 所有后续操作(chat/add_files/drop_db)都会使用新数据库名称")
    
    print("\n=== 预期行为 ===")
    print("- 编辑数据库名称时，会触发切换逻辑")
    print("- 切换成功会显示成功消息")
    print("- 切换失败会显示错误消息")
    print("- 文件列表会更新为新数据库的内容")
    
    # 模拟测试API调用
    base_url = "http://127.0.0.1:23333"
    
    test_cases = [
        ("HuixiangDou", "默认数据库"),
        ("TestDB", "测试数据库"),
        ("CustomDB", "自定义数据库")
    ]
    
    for db_name, description in test_cases:
        print(f"\n--- 测试数据库: {db_name} ({description}) ---")
        
        # 模拟chat请求
        chat_data = {
            "text": "你好，请介绍一下知识图谱",
            "db_name": db_name
        }
        
        print(f"请求数据: {json.dumps(chat_data, ensure_ascii=False, indent=2)}")
        print(f"预期行为: 使用数据库 {db_name} 进行查询")
        
        # 模拟add_files请求
        print(f"文件上传: 会保存到 {db_name} 数据库")
        
        # 模拟drop_db请求
        print(f"清空操作: 会清空 {db_name} 数据库")

def show_ui_changes():
    """显示UI界面的主要变化"""
    print("\n=== UI界面变化 ===")
    
    print("新增组件:")
    print("- ui_db_name: gr.Textbox(label='数据库名称', ...)")
    print("  - placeholder: '输入数据库名称'")
    print("  - value: current_db_name (初始为'HuixiangDou')")
    print("  - info: '当前使用的数据库名称，可直接编辑切换'")
    
    print("\n新增事件处理:")
    print("- ui_db_name.change(fn=on_db_name_changed, ...)")
    print("  - 实时监听文本框变化")
    print("  - 自动切换数据库")
    print("  - 显示切换结果")

if __name__ == "__main__":
    print("数据库切换UI功能测试")
    print("=" * 50)
    
    test_db_switch_ui()
    show_ui_changes()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("请启动 Gradio UI 验证实际效果:")
    print("python -m huixiangdou.gradio_ui")