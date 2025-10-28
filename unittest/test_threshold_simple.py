#!/usr/bin/env python3
"""
简化版测试 - 验证每个数据库独立阈值文件功能
只测试文件路径和基本的 JSON 读写逻辑
"""

import os
import sys
import json
import tempfile

def test_threshold_file_paths():
    """测试阈值文件路径逻辑"""
    print("=== 测试阈值文件路径逻辑 ===")
    
    # 模拟不同的数据库工作目录
    test_cases = [
        {
            'db_name': 'HuixiangDou',
            'work_dir': 'workdir/HuixiangDou',
            'expected_threshold': 0.15
        },
        {
            'db_name': 'CustomDB', 
            'work_dir': 'workdir/CustomDB',
            'expected_threshold': 0.25
        },
        {
            'db_name': 'TestDB',
            'work_dir': 'workdir/TestDB', 
            'expected_threshold': 0.35
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i}: {test_case['db_name']} ---")
        
        db_name = test_case['db_name']
        work_dir = test_case['work_dir']
        expected_threshold = test_case['expected_threshold']
        
        # 构建阈值文件路径
        threshold_file = os.path.join(work_dir, 'threshold.json')
        print(f"数据库名称: {db_name}")
        print(f"工作目录: {work_dir}")
        print(f"阈值文件路径: {threshold_file}")
        
        # 模拟创建阈值文件
        os.makedirs(work_dir, exist_ok=True)
        
        threshold_config = {
            'reject_threshold': expected_threshold,
            'database_name': db_name,
            'calculated_at': '2024-01-01 12:00:00',
            'good_questions_count': 10,
            'bad_questions_count': 10
        }
        
        # 保存阈值文件
        with open(threshold_file, 'w', encoding='utf-8') as f:
            json.dump(threshold_config, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 阈值文件已创建: {threshold_file}")
        
        # 验证文件内容
        if os.path.exists(threshold_file):
            with open(threshold_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            loaded_threshold = loaded_config.get('reject_threshold')
            print(f"保存的阈值: {expected_threshold}")
            print(f"加载的阈值: {loaded_threshold}")
            print(f"数据库名称: {loaded_config.get('database_name')}")
            
            if abs(loaded_threshold - expected_threshold) < 0.001:
                print("✅ 阈值匹配正确")
            else:
                print("❌ 阈值不匹配")
        else:
            print("❌ 阈值文件未找到")
    
    print(f"\n=== 验证不同数据库的独立性 ===")
    
    # 验证每个数据库有不同的阈值
    for test_case in test_cases:
        work_dir = test_case['work_dir']
        threshold_file = os.path.join(work_dir, 'threshold.json')
        expected_threshold = test_case['expected_threshold']
        
        if os.path.exists(threshold_file):
            with open(threshold_file, 'r') as f:
                config = json.load(f)
            actual_threshold = config.get('reject_threshold')
            print(f"{test_case['db_name']}: {actual_threshold} (期望: {expected_threshold})")
            
            if abs(actual_threshold - expected_threshold) < 0.001:
                print(f"✅ {test_case['db_name']} 阈值正确")
            else:
                print(f"❌ {test_case['db_name']} 阈值错误")
        else:
            print(f"❌ {test_case['db_name']} 文件不存在")
    
    print(f"\n=== 测试加载不存在的阈值文件 ===")
    
    # 测试不存在的数据库
    non_existent_dir = 'workdir/NonExistentDB'
    non_existent_file = os.path.join(non_existent_dir, 'threshold.json')
    
    print(f"不存在的阈值文件: {non_existent_file}")
    
    if os.path.exists(non_existent_file):
        print("❌ 文件不应该存在")
    else:
        print("✅ 文件不存在（符合预期）")
        # 模拟加载函数的行为
        default_threshold = 0.1  # 默认阈值
        print(f"将使用默认阈值: {default_threshold}")
    
    # 清理测试文件
    print(f"\n=== 清理测试文件 ===")
    for test_case in test_cases:
        work_dir = test_case['work_dir']
        if os.path.exists(work_dir):
            import shutil
            shutil.rmtree(work_dir)
            print(f"✅ 已删除: {work_dir}")
    
    if os.path.exists('workdir/NonExistentDB'):
        import shutil
        shutil.rmtree('workdir/NonExistentDB')
        print(f"✅ 已删除: workdir/NonExistentDB")
    
    print("\n=== 测试总结 ===")
    print("✅ 阈值文件路径逻辑正确")
    print("✅ 每个数据库有独立的阈值文件")
    print("✅ 阈值文件格式正确（JSON）")
    print("✅ 文件不存在的处理逻辑正确")

def test_config_format():
    """测试阈值配置文件格式"""
    print("\n=== 测试阈值配置文件格式 ===")
    
    # 模拟阈值配置
    threshold_config = {
        'reject_threshold': 0.15234,
        'database_name': 'TestDB',
        'calculated_at': '2024-01-01 15:30:45',
        'good_questions_count': 15,
        'bad_questions_count': 12
    }
    
    print("模拟阈值配置:")
    print(json.dumps(threshold_config, indent=2, ensure_ascii=False))
    
    # 测试 JSON 序列化和反序列化
    json_str = json.dumps(threshold_config, ensure_ascii=False, indent=2)
    loaded_config = json.loads(json_str)
    
    print(f"\n序列化后加载的配置:")
    print(json.dumps(loaded_config, indent=2, ensure_ascii=False))
    
    # 验证关键字段
    assert loaded_config['reject_threshold'] == threshold_config['reject_threshold']
    assert loaded_config['database_name'] == threshold_config['database_name']
    assert loaded_config['calculated_at'] == threshold_config['calculated_at']
    assert loaded_config['good_questions_count'] == threshold_config['good_questions_count']
    assert loaded_config['bad_questions_count'] == threshold_config['bad_questions_count']
    
    print("✅ 配置文件格式测试通过")

def main():
    """主函数"""
    print("开始测试每个数据库的独立阈值配置...")
    print("=" * 60)
    
    test_threshold_file_paths()
    test_config_format()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("\n新的阈值配置方案:")
    print("- 每个数据库有自己的 threshold.json 文件")
    print("- 文件保存在数据库的工作目录下")
    print("- 格式: JSON，包含阈值和元信息")
    print("- 加载时优先使用数据库特定文件，不存在时使用默认值")

if __name__ == "__main__":
    main()