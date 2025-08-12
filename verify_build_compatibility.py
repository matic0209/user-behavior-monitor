#!/usr/bin/env python3
"""
构建脚本兼容性验证工具
验证 build_optimized_exe.py 是否包含了 build_windows_full.py 的所有功能
"""

import re
import ast
from pathlib import Path

def extract_hidden_imports(file_path):
    """提取文件中的隐藏导入"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    imports = []
    
    # 查找 --hidden-import 参数
    hidden_import_pattern = r"--hidden-import=(\w+(?:\.\w+)*)"
    imports.extend(re.findall(hidden_import_pattern, content))
    
    # 查找 hiddenimports 列表
    hiddenimports_pattern = r"hiddenimports\s*=\s*\[(.*?)\]"
    matches = re.findall(hiddenimports_pattern, content, re.DOTALL)
    for match in matches:
        # 解析列表中的字符串
        items = re.findall(r"'([^']*)'", match)
        imports.extend(items)
    
    return list(set(imports))

def extract_excluded_modules(file_path):
    """提取文件中的排除模块"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    excludes = []
    
    # 查找 --exclude-module 参数
    exclude_pattern = r"--exclude-module=(\w+)"
    excludes.extend(re.findall(exclude_pattern, content))
    
    # 查找 excludes 列表
    excludes_pattern = r"excludes\s*=\s*\[(.*?)\]"
    matches = re.findall(excludes_pattern, content, re.DOTALL)
    for match in matches:
        # 解析列表中的字符串
        items = re.findall(r"'([^']*)'", match)
        excludes.extend(items)
    
    return list(set(excludes))

def extract_collect_all(file_path):
    """提取文件中的 collect-all 参数"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    collect_all = []
    
    # 查找 --collect-all 参数
    collect_pattern = r"--collect-all=(\w+)"
    collect_all.extend(re.findall(collect_pattern, content))
    
    return list(set(collect_all))

def check_function_coverage():
    """检查函数覆盖情况"""
    print("🔍 检查函数覆盖情况...")
    
    # 读取两个文件
    with open('build_windows_full.py', 'r', encoding='utf-8') as f:
        full_content = f.read()
    
    with open('build_optimized_exe.py', 'r', encoding='utf-8') as f:
        optimized_content = f.read()
    
    # 提取函数名
    def extract_functions(content):
        tree = ast.parse(content)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        return functions
    
    full_functions = extract_functions(full_content)
    optimized_functions = extract_functions(optimized_content)
    
    print(f"build_windows_full.py 函数: {full_functions}")
    print(f"build_optimized_exe.py 函数: {optimized_functions}")
    
    # 检查覆盖
    missing_functions = []
    for func in full_functions:
        if func not in optimized_functions:
            missing_functions.append(func)
    
    if missing_functions:
        print(f"❌ 缺失函数: {missing_functions}")
        return False
    else:
        print("✅ 所有函数都已覆盖")
        return True

def main():
    """主验证函数"""
    print("🔍 构建脚本兼容性验证")
    print("=" * 50)
    
    # 检查文件是否存在
    if not Path('build_windows_full.py').exists():
        print("❌ build_windows_full.py 不存在")
        return
    
    if not Path('build_optimized_exe.py').exists():
        print("❌ build_optimized_exe.py 不存在")
        return
    
    print("✅ 文件存在性检查通过")
    
    # 1. 检查隐藏导入
    print("\n📦 检查隐藏导入...")
    full_imports = extract_hidden_imports('build_windows_full.py')
    optimized_imports = extract_hidden_imports('build_optimized_exe.py')
    
    print(f"build_windows_full.py 隐藏导入: {full_imports}")
    print(f"build_optimized_exe.py 隐藏导入: {optimized_imports}")
    
    missing_imports = [imp for imp in full_imports if imp not in optimized_imports]
    if missing_imports:
        print(f"❌ 缺失的隐藏导入: {missing_imports}")
    else:
        print("✅ 所有隐藏导入都已包含")
    
    # 2. 检查排除模块
    print("\n🚫 检查排除模块...")
    full_excludes = extract_excluded_modules('build_windows_full.py')
    optimized_excludes = extract_excluded_modules('build_optimized_exe.py')
    
    print(f"build_windows_full.py 排除模块: {full_excludes}")
    print(f"build_optimized_exe.py 排除模块: {optimized_excludes}")
    
    missing_excludes = [exc for exc in full_excludes if exc not in optimized_excludes]
    if missing_excludes:
        print(f"❌ 缺失的排除模块: {missing_excludes}")
    else:
        print("✅ 所有排除模块都已包含")
    
    # 3. 检查 collect-all
    print("\n📚 检查 collect-all...")
    full_collect = extract_collect_all('build_windows_full.py')
    optimized_collect = extract_collect_all('build_optimized_exe.py')
    
    print(f"build_windows_full.py collect-all: {full_collect}")
    print(f"build_optimized_exe.py collect-all: {optimized_collect}")
    
    # 4. 检查函数覆盖
    print("\n🔧 检查函数覆盖...")
    function_coverage = check_function_coverage()
    
    # 5. 总结
    print("\n" + "=" * 50)
    print("📋 验证总结:")
    
    all_passed = True
    
    if missing_imports:
        print(f"❌ 隐藏导入: 缺失 {len(missing_imports)} 个")
        all_passed = False
    else:
        print("✅ 隐藏导入: 完全覆盖")
    
    if missing_excludes:
        print(f"❌ 排除模块: 缺失 {len(missing_excludes)} 个")
        all_passed = False
    else:
        print("✅ 排除模块: 完全覆盖")
    
    if function_coverage:
        print("✅ 函数覆盖: 完全覆盖")
    else:
        print("❌ 函数覆盖: 部分缺失")
        all_passed = False
    
    if all_passed:
        print("\n🎉 验证通过! build_optimized_exe.py 完全兼容 build_windows_full.py")
    else:
        print("\n⚠️ 验证失败! 需要修复上述问题")
    
    print("=" * 50)

if __name__ == '__main__':
    main()
