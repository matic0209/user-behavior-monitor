import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader

class DataCollector:
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigLoader()
        self.paths = self.config.get_paths()
        
        # 创建数据目录
        data_dir = Path(self.paths['data'])
        data_dir.mkdir(parents=True, exist_ok=True)

    def collect_mouse_data(self, user_id: str, session_id: str) -> pd.DataFrame:
        """收集鼠标数据（模拟）"""
        try:
            self.logger.info(f"开始收集用户 {user_id} 会话 {session_id} 的鼠标数据")
            
            # 这里应该是实际的鼠标数据收集逻辑
            # 目前使用模拟数据
            data = self._generate_mock_data(user_id, session_id)
            
            # 保存原始数据
            raw_data_path = Path(self.paths['data']) / 'raw' / f'user_{user_id}_session_{session_id}.csv'
            raw_data_path.parent.mkdir(parents=True, exist_ok=True)
            data.to_csv(raw_data_path, index=False)
            
            self.logger.info(f"鼠标数据收集完成，保存至 {raw_data_path}")
            return data
            
        except Exception as e:
            self.logger.error(f"鼠标数据收集失败: {str(e)}")
            raise

    def _generate_mock_data(self, user_id: str, session_id: str) -> pd.DataFrame:
        """生成模拟鼠标数据"""
        np.random.seed(hash(f"{user_id}_{session_id}") % 2**32)
        
        # 生成时间序列
        start_time = datetime.now()
        timestamps = []
        for i in range(1000):
            timestamps.append(start_time.timestamp() + i * 0.1)
        
        # 生成鼠标坐标
        x_coords = np.random.randint(0, 1920, 1000)
        y_coords = np.random.randint(0, 1080, 1000)
        
        # 生成鼠标状态
        states = np.random.choice(['Move', 'Pressed', 'Released', 'Drag'], 1000, p=[0.7, 0.1, 0.1, 0.1])
        
        # 生成按钮信息
        buttons = np.random.choice(['Left', 'Right', 'Scroll'], 1000, p=[0.8, 0.1, 0.1])
        
        data = pd.DataFrame({
            'user_id': user_id,
            'session': session_id,
            'timestamp': timestamps,
            'x': x_coords,
            'y': y_coords,
            'state': states,
            'button': buttons,
            'client timestamp': timestamps
        })
        
        return data

    def collect_batch_data(self, user_ids: list, sessions_per_user: int = 5) -> dict:
        """批量收集数据"""
        try:
            self.logger.info(f"开始批量收集数据，用户数: {len(user_ids)}")
            
            all_data = {}
            
            for user_id in user_ids:
                user_data = []
                for session_idx in range(sessions_per_user):
                    session_id = f"session_{session_idx}"
                    session_data = self.collect_mouse_data(user_id, session_id)
                    user_data.append(session_data)
                
                all_data[user_id] = pd.concat(user_data, ignore_index=True)
            
            self.logger.info("批量数据收集完成")
            return all_data
            
        except Exception as e:
            self.logger.error(f"批量数据收集失败: {str(e)}")
            raise

    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证数据质量"""
        try:
            # 检查必要的列
            required_columns = ['user_id', 'session', 'x', 'y', 'state', 'button']
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                self.logger.error(f"缺少必要的列: {missing_columns}")
                return False
            
            # 检查数据类型
            if not all(data['x'].dtype == 'int64', data['y'].dtype == 'int64'):
                self.logger.error("坐标列必须是整数类型")
                return False
            
            # 检查坐标范围
            if (data['x'] < 0).any() or (data['y'] < 0).any():
                self.logger.error("坐标值不能为负数")
                return False
            
            # 检查状态值
            valid_states = ['Move', 'Pressed', 'Released', 'Drag']
            invalid_states = data[~data['state'].isin(valid_states)]['state'].unique()
            if len(invalid_states) > 0:
                self.logger.error(f"无效的状态值: {invalid_states}")
                return False
            
            self.logger.info("数据验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"数据验证失败: {str(e)}")
            return False

    def get_data_statistics(self, data: pd.DataFrame) -> dict:
        """获取数据统计信息"""
        try:
            stats = {
                'total_records': len(data),
                'unique_users': data['user_id'].nunique(),
                'unique_sessions': data['session'].nunique(),
                'date_range': {
                    'start': data['timestamp'].min(),
                    'end': data['timestamp'].max()
                },
                'state_distribution': data['state'].value_counts().to_dict(),
                'button_distribution': data['button'].value_counts().to_dict(),
                'coordinate_range': {
                    'x_min': data['x'].min(),
                    'x_max': data['x'].max(),
                    'y_min': data['y'].min(),
                    'y_max': data['y'].max()
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取数据统计信息失败: {str(e)}")
            return {} 