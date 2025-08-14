import pandas as pd
import numpy as np
import sqlite3
import json
import pickle
import time
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader

class TrainingDataImporter:
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigLoader()
        self.db_path = Path(self.config.get_paths()['data']) / 'mouse_data.db'
        
        self.logger.info("训练数据导入器初始化完成")

    def load_training_data(self, pickle_path):
        """加载训练数据pickle文件"""
        try:
            self.logger.info(f"加载训练数据: {pickle_path}")
            
            with open(pickle_path, 'rb') as f:
                data = pickle.load(f)
            
            self.logger.info(f"成功加载训练数据: {data.shape[0]} 行, {data.shape[1]} 列")
            return data
            
        except Exception as e:
            self.logger.error(f"加载训练数据失败: {str(e)}")
            return None

    def import_training_data_to_db(self, pickle_path, user_id_prefix="training_user"):
        """将训练数据导入到数据库作为负样本"""
        try:
            # 加载数据
            df = self.load_training_data(pickle_path)
            if df is None:
                return False
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 确保features表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    feature_vector TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_features_user_session ON features(user_id, session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_features_timestamp ON features(timestamp)')
            
            # 导入数据
            imported_count = 0
            current_time = time.time()
            
            for idx, row in df.iterrows():
                try:
                    # 生成用户ID和会话ID
                    original_user = row.get('user', 'unknown')
                    session_id = str(row.get('session', f'session_{idx}'))
                    user_id = f"{user_id_prefix}_{original_user}"
                    
                    # 准备特征向量（排除session和user列）
                    feature_data = row.drop(['session', 'user']).to_dict()
                    
                    # 转换为JSON字符串
                    feature_vector = json.dumps(feature_data)
                    
                    # 插入数据库
                    cursor.execute('''
                        INSERT INTO features 
                        (user_id, session_id, timestamp, feature_vector)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        user_id,
                        session_id,
                        current_time + idx,  # 使用递增时间戳
                        feature_vector
                    ))
                    
                    imported_count += 1
                    
                    # 每1000条记录提交一次
                    if imported_count % 1000 == 0:
                        conn.commit()
                        self.logger.info(f"已导入 {imported_count} 条记录")
                
                except Exception as e:
                    self.logger.error(f"导入第 {idx} 行数据失败: {str(e)}")
                    continue
            
            # 最终提交
            conn.commit()
            conn.close()
            
            self.logger.info(f"训练数据导入完成: 共导入 {imported_count} 条记录")
            return True
            
        except Exception as e:
            self.logger.error(f"导入训练数据失败: {str(e)}")
            return False

    def import_all_training_data(self):
        """导入所有训练数据"""
        try:
            data_path = Path(self.config.get_paths()['data'])
            debug_mode = self.config.get_system_config().get('debug_mode', False)

            # 导入训练数据
            training_file = data_path / 'processed' / 'all_training_aggregation.pickle'
            if training_file.exists():
                success = self.import_training_data_to_db(training_file, "training_user")
                if success:
                    self.logger.info("训练数据导入成功")
                else:
                    self.logger.error("训练数据导入失败")
            else:
                self.logger.warning(f"训练数据文件不存在: {training_file}")

            # 发布版：默认不导入测试数据；仅在调试模式下导入
            if debug_mode:
                test_file = data_path / 'processed' / 'all_test_aggregation.pickle'
                if test_file.exists():
                    success = self.import_training_data_to_db(test_file, "test_user")
                    if success:
                        self.logger.info("测试数据导入成功 (调试模式)")
                    else:
                        self.logger.error("测试数据导入失败 (调试模式)")
                else:
                    self.logger.warning(f"测试数据文件不存在: {test_file}")
                
        except Exception as e:
            self.logger.error(f"导入所有训练数据失败: {str(e)}")

    def get_imported_data_stats(self):
        """获取导入数据的统计信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 统计不同用户类型的数据
            cursor.execute('''
                SELECT 
                    CASE 
                        WHEN user_id LIKE 'training_user%' THEN 'training_data'
                        WHEN user_id LIKE 'test_user%' THEN 'test_data'
                        ELSE 'real_user_data'
                    END as data_type,
                    COUNT(*) as count,
                    COUNT(DISTINCT user_id) as unique_users
                FROM features 
                GROUP BY data_type
            ''')
            
            stats = cursor.fetchall()
            conn.close()
            
            self.logger.info("导入数据统计:")
            for data_type, count, unique_users in stats:
                self.logger.info(f"  {data_type}: {count} 条记录, {unique_users} 个用户")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取导入数据统计失败: {str(e)}")
            return []

    def cleanup_imported_data(self, data_type=None):
        """清理导入的数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if data_type == "training":
                # 清理训练数据
                cursor.execute('DELETE FROM features WHERE user_id LIKE "training_user%"')
                deleted_count = cursor.rowcount
                self.logger.info(f"清理了 {deleted_count} 条训练数据")
            elif data_type == "test":
                # 清理测试数据
                cursor.execute('DELETE FROM features WHERE user_id LIKE "test_user%"')
                deleted_count = cursor.rowcount
                self.logger.info(f"清理了 {deleted_count} 条测试数据")
            else:
                # 清理所有导入的数据
                cursor.execute('DELETE FROM features WHERE user_id LIKE "training_user%" OR user_id LIKE "test_user%"')
                deleted_count = cursor.rowcount
                self.logger.info(f"清理了 {deleted_count} 条导入数据")
            
            conn.commit()
            conn.close()
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"清理导入数据失败: {str(e)}")
            return 0

def main():
    """主函数 - 用于测试数据导入"""
    print("=== 训练数据导入工具 ===")
    
    importer = TrainingDataImporter()
    
    # 导入所有训练数据
    print("开始导入训练数据...")
    importer.import_all_training_data()
    
    # 显示统计信息
    print("\n数据统计:")
    importer.get_imported_data_stats()
    
    print("\n导入完成!")

if __name__ == "__main__":
    main() 