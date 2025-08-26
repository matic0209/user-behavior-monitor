#!/usr/bin/env python3
"""
测试xgboost导入的脚本
用于调试PyInstaller打包问题
"""

import sys
import traceback

def test_imports():
    """测试所有必要的导入"""
    print("开始测试导入...")
    
    modules_to_test = [
        'numpy',
        'pandas', 
        'sklearn',
        'xgboost',
        'psutil',
        'pynput',
        'keyboard',
        'yaml',
        'json',
        'threading',
        'datetime',
        'pathlib',
        'win32api',
        'win32con',
        'win32gui'
    ]
    
    failed_imports = []
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✓ {module} 导入成功")
        except ImportError as e:
            print(f"✗ {module} 导入失败: {e}")
            failed_imports.append(module)
        except Exception as e:
            print(f"✗ {module} 导入异常: {e}")
            failed_imports.append(module)
    
    print(f"\n导入测试完成: {len(modules_to_test) - len(failed_imports)}/{len(modules_to_test)} 成功")
    
    if failed_imports:
        print(f"失败的导入: {failed_imports}")
        return False
    else:
        print("所有模块导入成功!")
        return True

def test_xgboost_specific():
    """专门测试xgboost相关功能"""
    print("\n测试xgboost特定功能...")
    
    try:
        import xgboost as xgb
        print("✓ xgboost 基础导入成功")
        
        # 测试XGBClassifier
        from xgboost import XGBClassifier
        print("✓ XGBClassifier 导入成功")
        
        # 测试sklearn集成
        from xgboost.sklearn import XGBClassifier as XGBClassifierSklearn
        print("✓ xgboost.sklearn.XGBClassifier 导入成功")
        
        # 测试创建模型
        model = XGBClassifier(n_estimators=10)
        print("✓ XGBClassifier 创建成功")
        
        return True
        
    except Exception as e:
        print(f"✗ xgboost测试失败: {e}")
        traceback.print_exc()
        return False

def test_sklearn_integration():
    """测试sklearn集成"""
    print("\n测试sklearn集成...")
    
    try:
        from sklearn.ensemble import RandomForestClassifier
        print("✓ RandomForestClassifier 导入成功")
        
        from sklearn.model_selection import train_test_split
        print("✓ train_test_split 导入成功")
        
        from sklearn.tree import DecisionTreeClassifier
        print("✓ DecisionTreeClassifier 导入成功")
        
        return True
        
    except Exception as e:
        print(f"✗ sklearn集成测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("模块导入测试工具")
    print("=" * 50)
    
    # 测试基础导入
    basic_ok = test_imports()
    
    # 测试xgboost特定功能
    xgb_ok = test_xgboost_specific()
    
    # 测试sklearn集成
    sklearn_ok = test_sklearn_integration()
    
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print(f"基础导入: {'✓ 通过' if basic_ok else '✗ 失败'}")
    print(f"xgboost功能: {'✓ 通过' if xgb_ok else '✗ 失败'}")
    print(f"sklearn集成: {'✓ 通过' if sklearn_ok else '✗ 失败'}")
    
    if basic_ok and xgb_ok and sklearn_ok:
        print("\n🎉 所有测试通过! 可以正常打包")
    else:
        print("\n⚠️ 部分测试失败，需要检查依赖安装")
    
    print("=" * 50)

if __name__ == '__main__':
    main() 