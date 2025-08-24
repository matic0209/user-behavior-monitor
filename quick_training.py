#!/usr/bin/env python3
"""
快速训练启动脚本
使用优化的配置大幅减少训练时间
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_fast_training():
    """设置快速训练环境"""
    print("🚀 设置快速训练环境...")
    
    # 设置环境变量
    os.environ['FAST_TRAINING'] = 'true'
    os.environ['UBM_CONFIG_FILE'] = 'src/utils/config/fast_training.yaml'
    
    print("✅ 快速训练环境设置完成")
    print("   - 样本数量: 500 (原10000)")
    print("   - 采样频率: 50Hz (原10Hz)")
    print("   - 预计加速: 20倍")

def start_fast_training():
    """启动快速训练"""
    print("\n🎯 启动快速训练...")
    
    try:
        # 导入主程序
        from user_behavior_monitor import WindowsBehaviorMonitor
        
        # 创建监控器实例
        monitor = WindowsBehaviorMonitor()
        
        print("✅ 快速训练启动成功")
        print("📊 训练参数:")
        print("   - 目标样本数: 500")
        print("   - 采样频率: 50Hz")
        print("   - 预计时间: 1-3分钟")
        print("   - 原预计时间: 20-40分钟")
        
        # 启动训练
        monitor.start()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保在项目根目录运行此脚本")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Windows用户行为监控系统 - 快速训练模式")
    print("=" * 60)
    
    # 设置快速训练环境
    setup_fast_training()
    
    # 启动快速训练
    start_fast_training()
    
    print("\n" + "=" * 60)
    print("🎉 快速训练完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
