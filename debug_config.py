#!/usr/bin/env python3
"""
调试配置加载的脚本
检查实际使用的配置值
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config.config_loader import ConfigLoader
from src.utils.logger.logger import Logger

def main():
    print("=== 配置调试信息 ===")
    print(f"项目根目录: {project_root}")
    print(f"当前工作目录: {Path.cwd()}")
    print("")
    
    try:
        # 加载配置
        config = ConfigLoader()
        logger = Logger()
        
        print("=== 数据采集配置 ===")
        dc_config = config.get_data_collection_config()
        print(f"完整数据采集配置: {dc_config}")
        print("")
        
        # 检查关键配置项
        target_samples = dc_config.get('target_samples_per_session', 'NOT_FOUND')
        collection_interval = dc_config.get('collection_interval', 'NOT_FOUND')
        max_buffer_size = dc_config.get('max_buffer_size', 'NOT_FOUND')
        
        print("=== 关键配置项 ===")
        print(f"target_samples_per_session: {target_samples}")
        print(f"collection_interval: {collection_interval}")
        print(f"max_buffer_size: {max_buffer_size}")
        print("")
        
        # 模拟主程序的逻辑
        print("=== 模拟主程序逻辑 ===")
        min_data_points = int(dc_config.get('target_samples_per_session', 1000))
        print(f"主程序会使用的 min_data_points: {min_data_points}")
        print("")
        
        # 检查配置文件路径
        print("=== 配置文件路径检查 ===")
        possible_paths = [
            Path(__file__).parent / 'src' / 'utils' / 'config' / 'config.yaml',
            Path.cwd() / 'src' / 'utils' / 'config' / 'config.yaml',
            Path.cwd() / 'config.yaml'
        ]
        
        for i, path in enumerate(possible_paths, 1):
            exists = path.exists()
            print(f"{i}. {path}")
            print(f"   存在: {exists}")
            if exists:
                try:
                    import yaml
                    with open(path, 'r', encoding='utf-8') as f:
                        yaml_config = yaml.safe_load(f)
                    target_in_file = yaml_config.get('data_collection', {}).get('target_samples_per_session', 'NOT_FOUND')
                    print(f"   文件中的 target_samples_per_session: {target_in_file}")
                except Exception as e:
                    print(f"   读取失败: {e}")
            print("")
        
        # 检查环境变量
        print("=== 环境变量检查 ===")
        import os
        ubm_base = os.getenv('UBM_BASE_PATH')
        ubm_db = os.getenv('UBM_DATABASE')
        ubm_config = os.getenv('UBM_CONFIG_FILE')
        
        print(f"UBM_BASE_PATH: {ubm_base}")
        print(f"UBM_DATABASE: {ubm_db}")
        print(f"UBM_CONFIG_FILE: {ubm_config}")
        print("")
        
        # 检查其他配置
        print("=== 其他相关配置 ===")
        pred_config = config.get_prediction_config()
        print(f"prediction.batch_size: {pred_config.get('batch_size', 'NOT_FOUND')}")
        print(f"prediction.min_samples: {pred_config.get('min_samples', 'NOT_FOUND')}")
        
        paths_config = config.get_paths()
        print(f"database path: {paths_config.get('database', 'NOT_FOUND')}")
        print("")
        
        print("=== 结论 ===")
        if target_samples == 1000:
            print("✅ 配置正确：target_samples_per_session = 1000")
            print("如果测试仍然很慢，可能是：")
            print("1. EXE文件使用了旧配置（需要重新构建）")
            print("2. 应用程序有缓存机制")
            print("3. 实际数据采集速度较慢")
        else:
            print(f"❌ 配置异常：target_samples_per_session = {target_samples}")
            print("建议：")
            print("1. 检查配置文件是否正确")
            print("2. 确认配置文件路径")
            print("3. 检查是否有环境变量覆盖")
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
