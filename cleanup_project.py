#!/usr/bin/env python3
"""
项目清理脚本 - 整理项目结构，移动文件到合适的目录
"""

import os
import shutil
from pathlib import Path

def create_directories():
    """创建必要的目录结构"""
    dirs = [
        'tools',           # 工具脚本
        'docs',            # 文档
        'build',           # 构建脚本
        'tests/tools',     # 测试工具
        'archive',         # 归档文件
    ]
    
    for dir_name in dirs:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
        print(f"✓ 创建目录: {dir_name}")

def move_files():
    """移动文件到合适的目录"""
    
    # 文件移动规则
    move_rules = {
        # 构建相关脚本 -> build/
        'build': [
            'build_*.py', 'quick_build.py', 'simple_build.py', 'uos20_build.py',
            'install_*.py', 'download_*.py', 'create_*.py', 'generate_*.py',
            'verify_build_compatibility.py', 'UserBehaviorMonitor.spec'
        ],
        
        # 工具脚本 -> tools/
        'tools': [
            'alert_monitor.py', 'background_manager.py', 'service_manager.py',
            'process_manager.py', 'log_manager.py', 'system_alert_monitor.py',
            'uos20_*.py', 'windows_service.py', 'mock_heartbeat_server.py',
            'demo_heartbeat.py', 'optimize_system.py', 'init_system.py',
            'start_monitor.py', 'view_mouse_data.py', 'export_sample_db.py',
            'load_processed_data_to_db.py', 'import_training_data.py'
        ],
        
        # 文档 -> docs/
        'docs': [
            '*_GUIDE.md', '*_README.md', '*_FIX.md', 'PRODUCT_ARCHITECTURE.md',
            'USAGE.md', 'CLEANUP_SUMMARY.md', 'COMPLETE_TEST_CASES_GUIDE.md',
            'TEST_*.md', 'WINDOWS_*.md', 'HEARTBEAT_*.md', 'WORKFLOW_*.md',
            'BUILD_SCRIPTS_*.md', 'NEGATIVE_SAMPLE_FIX.md', 'results_summary.md'
        ],
        
        # 测试工具 -> tests/tools/
        'tests/tools': [
            'TC10_*.py', 'TC10_*.bat', 'TC10_*.md'
        ],
        
        # 调试和检查脚本 -> archive/
        'archive': [
            'debug_*.py', 'check_*.py', 'diagnose_*.py', 'fix_*.py',
            'test_*.py', 'quick_*.py', 'clean_*.py', 'simple_mouse_test.py'
        ]
    }
    
    import glob
    
    for target_dir, patterns in move_rules.items():
        for pattern in patterns:
            files = glob.glob(pattern)
            for file in files:
                if os.path.isfile(file):
                    source = Path(file)
                    dest = Path(target_dir) / source.name
                    
                    # 避免覆盖已存在的文件
                    if dest.exists():
                        print(f"⚠️  跳过 {file} (目标已存在)")
                        continue
                    
                    try:
                        shutil.move(str(source), str(dest))
                        print(f"✓ 移动: {file} -> {target_dir}/")
                    except Exception as e:
                        print(f"❌ 移动失败: {file} - {str(e)}")

def cleanup_shell_scripts():
    """清理shell脚本"""
    shell_files = ['alert_monitor.sh', 'install_uos20.sh']
    
    for file in shell_files:
        if os.path.exists(file):
            dest = Path('tools') / file
            try:
                shutil.move(file, str(dest))
                print(f"✓ 移动: {file} -> tools/")
            except Exception as e:
                print(f"❌ 移动失败: {file} - {str(e)}")

def cleanup_requirements():
    """整理requirements文件"""
    req_files = [
        'requirements_minimal.txt',
        'requirements_uos20_python37.txt', 
        'requirements_uos20.txt'
    ]
    
    for file in req_files:
        if os.path.exists(file):
            dest = Path('build') / file
            try:
                shutil.move(file, str(dest))
                print(f"✓ 移动: {file} -> build/")
            except Exception as e:
                print(f"❌ 移动失败: {file} - {str(e)}")

def remove_temp_files():
    """删除临时文件"""
    temp_files = [
        'monitor.pid',
        'index.html',
        '用户异常行为告警功能.docx'
    ]
    
    for file in temp_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✓ 删除临时文件: {file}")
            except Exception as e:
                print(f"❌ 删除失败: {file} - {str(e)}")

def update_main_files():
    """保留在根目录的核心文件"""
    core_files = [
        'user_behavior_monitor.py',          # 主程序
        'user_behavior_monitor_optimized.py', # 优化版本
        'README.md',                         # 主文档
        'requirements.txt',                  # 主要依赖
        'QUICK_START.md',                   # 快速开始
        'RELEASE_GUIDE.md'                  # 发布指南
    ]
    
    print(f"\n📁 保留在根目录的核心文件:")
    for file in core_files:
        if os.path.exists(file):
            print(f"   ✓ {file}")
        else:
            print(f"   ⚠️  {file} (不存在)")

def main():
    """主清理函数"""
    print("🧹 开始项目清理...")
    print("=" * 50)
    
    # 1. 创建目录结构
    print("\n📁 创建目录结构:")
    create_directories()
    
    # 2. 移动文件
    print("\n📦 移动文件:")
    move_files()
    cleanup_shell_scripts()
    cleanup_requirements()
    
    # 3. 删除临时文件
    print("\n🗑️  清理临时文件:")
    remove_temp_files()
    
    # 4. 显示核心文件
    update_main_files()
    
    print("\n" + "=" * 50)
    print("✅ 项目清理完成!")
    print("\n📋 新的项目结构:")
    print("├── 根目录 - 核心程序和主要文档")
    print("├── build/ - 构建和安装脚本")
    print("├── tools/ - 工具和服务脚本")
    print("├── docs/ - 详细文档")
    print("├── tests/tools/ - 测试工具")
    print("├── archive/ - 调试和历史文件")
    print("├── src/ - 源代码")
    print("├── data/ - 数据文件")
    print("└── logs/ - 日志文件")

if __name__ == "__main__":
    main()
