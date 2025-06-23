#!/usr/bin/env python3
"""
系统逻辑一致性测试脚本
验证各个模块之间的数据流和配置一致性
"""

import sys
import os
from pathlib import Path
import sqlite3
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_config_consistency():
    """测试配置文件一致性"""
    print("=== 测试配置文件一致性 ===")
    
    try:
        from src.utils.config.config_loader import ConfigLoader
        config = ConfigLoader()
        
        # 检查关键配置项
        paths = config.get_paths()
        required_paths = ['database', 'user_config', 'models', 'data', 'logs']
        
        missing_paths = []
        for path_key in required_paths:
            if path_key not in paths:
                missing_paths.append(path_key)
            else:
                print(f"✓ {path_key}: {paths[path_key]}")
        
        if missing_paths:
            print(f"✗ 缺少配置项: {missing_paths}")
            return False
        
        print("✓ 配置文件一致性检查通过")
        return True
        
    except Exception as e:
        print(f"✗ 配置文件一致性检查失败: {str(e)}")
        return False

def test_database_consistency():
    """测试数据库一致性"""
    print("\n=== 测试数据库一致性 ===")
    
    try:
        from src.utils.config.config_loader import ConfigLoader
        config = ConfigLoader()
        db_path = Path(config.get_paths()['database'])
        
        if not db_path.exists():
            print(f"✗ 数据库文件不存在: {db_path}")
            return False
        
        print(f"✓ 数据库文件存在: {db_path}")
        
        # 检查数据库表结构
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"数据库中的表: {tables}")
        
        # 检查必需的表
        required_tables = ['mouse_events', 'features']
        missing_tables = []
        
        for table in required_tables:
            if table in tables:
                # 检查表结构
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"✓ 表 {table}: {columns}")
            else:
                missing_tables.append(table)
                print(f"✗ 缺少表: {table}")
        
        conn.close()
        
        if missing_tables:
            print(f"✗ 缺少必需的表: {missing_tables}")
            return False
        
        print("✓ 数据库一致性检查通过")
        return True
        
    except Exception as e:
        print(f"✗ 数据库一致性检查失败: {str(e)}")
        return False

def test_module_imports():
    """测试模块导入一致性"""
    print("\n=== 测试模块导入一致性 ===")
    
    modules_to_test = [
        ('src.utils.logger.logger', 'Logger'),
        ('src.utils.config.config_loader', 'ConfigLoader'),
        ('src.core.data_collector.windows_mouse_collector', 'WindowsMouseCollector'),
        ('src.core.feature_engineer.simple_feature_processor', 'SimpleFeatureProcessor'),
        ('src.core.model_trainer.simple_model_trainer', 'SimpleModelTrainer'),
        ('src.core.predictor.simple_predictor', 'SimplePredictor'),
        ('src.core.alert.alert_service', 'AlertService'),
        ('src.core.user_manager', 'UserManager'),
        ('src.classification', 'load_data'),
        ('src.predict', 'predict_anomaly')
    ]
    
    failed_imports = []
    
    for module_path, class_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            if hasattr(module, class_name):
                print(f"✓ {module_path}.{class_name}")
            else:
                print(f"✗ {module_path} 中缺少 {class_name}")
                failed_imports.append(f"{module_path}.{class_name}")
        except ImportError as e:
            print(f"✗ 无法导入 {module_path}.{class_name}: {str(e)}")
            failed_imports.append(f"{module_path}.{class_name}")
        except Exception as e:
            print(f"✗ 导入 {module_path}.{class_name} 时出错: {str(e)}")
            failed_imports.append(f"{module_path}.{class_name}")
    
    if failed_imports:
        print(f"✗ 导入失败的模块: {failed_imports}")
        return False
    
    print("✓ 模块导入一致性检查通过")
    return True

def test_data_flow():
    """测试数据流一致性"""
    print("\n=== 测试数据流一致性 ===")
    
    try:
        from src.utils.config.config_loader import ConfigLoader
        config = ConfigLoader()
        db_path = Path(config.get_paths()['database'])
        
        if not db_path.exists():
            print("✗ 数据库不存在，无法测试数据流")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查数据流：mouse_events -> features
        cursor.execute("SELECT COUNT(*) FROM mouse_events")
        mouse_events_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM features")
        features_count = cursor.fetchone()[0]
        
        print(f"mouse_events 表记录数: {mouse_events_count}")
        print(f"features 表记录数: {features_count}")
        
        # 检查用户一致性
        cursor.execute("SELECT DISTINCT user_id FROM mouse_events")
        mouse_users = set(user[0] for user in cursor.fetchall())
        
        cursor.execute("SELECT DISTINCT user_id FROM features")
        feature_users = set(user[0] for user in cursor.fetchall())
        
        print(f"mouse_events 用户数: {len(mouse_users)}")
        print(f"features 用户数: {len(feature_users)}")
        
        # 检查是否有用户数据不匹配
        mouse_only_users = mouse_users - feature_users
        feature_only_users = feature_users - mouse_users
        
        if mouse_only_users:
            print(f"⚠️  只在 mouse_events 中的用户: {list(mouse_only_users)[:5]}")
        
        if feature_only_users:
            print(f"⚠️  只在 features 中的用户: {list(feature_only_users)[:5]}")
        
        conn.close()
        
        if mouse_events_count > 0 and features_count == 0:
            print("⚠️  有鼠标事件数据但没有特征数据，可能需要运行特征处理")
        elif mouse_events_count == 0 and features_count > 0:
            print("⚠️  有特征数据但没有鼠标事件数据，数据来源可能异常")
        elif mouse_events_count > 0 and features_count > 0:
            print("✓ 数据流一致性检查通过")
            return True
        else:
            print("⚠️  两个表都没有数据，系统可能尚未运行")
            return True
        
    except Exception as e:
        print(f"✗ 数据流一致性检查失败: {str(e)}")
        return False

def test_file_paths():
    """测试文件路径一致性"""
    print("\n=== 测试文件路径一致性 ===")
    
    try:
        from src.utils.config.config_loader import ConfigLoader
        config = ConfigLoader()
        paths = config.get_paths()
        
        # 检查关键目录
        required_dirs = ['models', 'data', 'logs']
        missing_dirs = []
        
        for dir_key in required_dirs:
            dir_path = Path(paths[dir_key])
            if dir_path.exists():
                print(f"✓ 目录存在: {dir_path}")
            else:
                print(f"✗ 目录不存在: {dir_path}")
                missing_dirs.append(dir_key)
        
        # 检查数据库文件
        db_path = Path(paths['database'])
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            print(f"✓ 数据库文件存在: {db_path} ({size_mb:.2f} MB)")
        else:
            print(f"✗ 数据库文件不存在: {db_path}")
            missing_dirs.append('database')
        
        if missing_dirs:
            print(f"✗ 缺少文件/目录: {missing_dirs}")
            return False
        
        print("✓ 文件路径一致性检查通过")
        return True
        
    except Exception as e:
        print(f"✗ 文件路径一致性检查失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("系统逻辑一致性测试")
    print("=" * 50)
    
    tests = [
        ("配置文件一致性", test_config_consistency),
        ("数据库一致性", test_database_consistency),
        ("模块导入一致性", test_module_imports),
        ("数据流一致性", test_data_flow),
        ("文件路径一致性", test_file_paths)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed_tests}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！系统逻辑一致性良好")
        return 0
    else:
        print("⚠️  部分测试失败，请检查上述问题")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 