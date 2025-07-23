import pandas as pd
import numpy as np
import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader

# 移除对已删除的feature_engineering模块的导入
# try:
#     from src.feature_engineering import (
#         remove_outlier, fill_in_scroll, change_from_prev_rec, classify_categ,
#         add_velocity_features, add_trajectory_features, add_temporal_features,
#         add_statistical_features, add_interaction_features, add_geometric_features,
#         add_advanced_features, aggregate_features
#     )
#     FEATURE_ENGINEERING_AVAILABLE = True
# except ImportError:
#     FEATURE_ENGINEERING_AVAILABLE = False
#     print("警告: 无法导入feature_engineering模块")

# 简单的特征处理实现
def remove_outlier(df):
    """移除异常值"""
    df = df[(df['x'] < 65535) & (df['y'] < 65535)].copy()
    df.reset_index(drop=True, inplace=True)
    return df

def fill_in_scroll(df):
    """填充滚动事件的位置信息"""
    df.loc[df['button'] == "Scroll", ['x', 'y']] = np.nan
    df['x'] = df['x'].ffill()
    df['y'] = df['y'].ffill()
    return df

def change_from_prev_rec(df):
    """计算与前一记录的差异"""
    df['distance_from_previous'] = np.sqrt((df['x'].diff())**2 + (df['y'].diff())**2)
    df['elapsed_time_from_previous'] = df['client timestamp'].diff()
    df['angle'] = np.arctan2(df['y'], df['x']) * 180 / np.pi
    df['angle_movement'] = df['angle'].diff()
    df['angle_movement_abs'] = abs(df['angle_movement'])
    return df

def classify_categ(df):
    """分类鼠标事件"""
    if 'button' in df.columns:
        df['button'] = df['button'].astype(str)
    df['categ'] = "move"  # 默认分类
    return df

def add_velocity_features(df):
    """添加速度特征"""
    if 'distance_from_previous' in df.columns and 'elapsed_time_from_previous' in df.columns:
        df['velocity'] = df['distance_from_previous'] / (df['elapsed_time_from_previous'] + 1e-6)
        df['max_velocity'] = df['velocity'].rolling(window=10, min_periods=1).max()
        df['avg_velocity'] = df['velocity'].rolling(window=10, min_periods=1).mean()
    return df

def add_trajectory_features(df):
    """添加轨迹特征"""
    if 'distance_from_previous' in df.columns:
        df['total_distance'] = df['distance_from_previous'].cumsum()
        df['straight_line_distance'] = np.sqrt((df['x'] - df['x'].iloc[0])**2 + (df['y'] - df['y'].iloc[0])**2)
        df['efficiency'] = df['straight_line_distance'] / (df['total_distance'] + 1e-6)
    return df

def add_temporal_features(df):
    """添加时间特征"""
    if 'client timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['client timestamp'], unit='s')
        df['hour'] = df['timestamp'].dt.hour
        df['minute'] = df['timestamp'].dt.minute
        df['second'] = df['timestamp'].dt.second
    return df

def add_statistical_features(df):
    """添加统计特征"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col not in ['x', 'y', 'client timestamp']:
            df[f'{col}_rolling_mean'] = df[col].rolling(window=10, min_periods=1).mean()
            df[f'{col}_rolling_std'] = df[col].rolling(window=10, min_periods=1).std()
    return df

def add_interaction_features(df):
    """添加交互特征"""
    if 'button' in df.columns and 'state' in df.columns:
        df['click_count'] = ((df['state'] == 'Pressed') & (df['button'].isin(['Left', 'Right']))).cumsum()
        df['scroll_count'] = (df['button'] == 'Scroll').cumsum()
    return df

def add_geometric_features(df):
    """添加几何特征"""
    if 'x' in df.columns and 'y' in df.columns:
        df['distance_from_center'] = np.sqrt((df['x'] - 1920/2)**2 + (df['y'] - 1080/2)**2)
        df['quadrant'] = ((df['x'] > 1920/2).astype(int) * 2 + (df['y'] > 1080/2).astype(int))
    return df

def add_advanced_features(df):
    """添加高级特征"""
    if 'velocity' in df.columns:
        df['velocity_change'] = df['velocity'].diff()
        df['velocity_acceleration'] = df['velocity_change'].diff()
    return df

def aggregate_features(df):
    """聚合特征"""
    if df.empty:
        return pd.DataFrame()
    
    # 计算聚合特征
    agg_features = {}
    
    # 基本统计
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col not in ['x', 'y', 'client timestamp']:
            agg_features[f'{col}_mean'] = df[col].mean()
            agg_features[f'{col}_std'] = df[col].std()
            agg_features[f'{col}_min'] = df[col].min()
            agg_features[f'{col}_max'] = df[col].max()
    
    # 事件统计
    if 'button' in df.columns:
        button_counts = df['button'].value_counts()
        for button, count in button_counts.items():
            agg_features[f'button_{button}_count'] = count
    
    if 'state' in df.columns:
        state_counts = df['state'].value_counts()
        for state, count in state_counts.items():
            agg_features[f'state_{state}_count'] = count
    
    return pd.DataFrame([agg_features])

FEATURE_ENGINEERING_AVAILABLE = True

class SimpleFeatureProcessor:
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigLoader()
        self.db_path = Path(self.config.get_paths()['data']) / 'mouse_data.db'
        
        if not FEATURE_ENGINEERING_AVAILABLE:
            self.logger.error("feature_engineering模块不可用，特征处理功能受限")
        
        self.logger.info("简单特征处理器初始化完成")

    def load_data_from_db(self, user_id, session_id=None):
        """从数据库加载鼠标数据，格式与feature_engineering期望的输入格式一致"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            if session_id:
                query = '''
                    SELECT timestamp as "client timestamp", x, y, button, event_type as state, event_type
                    FROM mouse_events 
                    WHERE user_id = ? AND session_id = ?
                    ORDER BY timestamp
                '''
                params = (user_id, session_id)
            else:
                query = '''
                    SELECT timestamp as "client timestamp", x, y, button, event_type as state, event_type
                    FROM mouse_events 
                    WHERE user_id = ?
                    ORDER BY timestamp
                '''
                params = (user_id,)
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            self.logger.info(f"从数据库加载了 {len(df)} 条鼠标事件数据")
            return df
            
        except Exception as e:
            self.logger.error(f"从数据库加载数据失败: {str(e)}")
            return pd.DataFrame()

    def _align_features_with_training_data(self, features_df):
        """将特征与训练数据对齐"""
        try:
            # 从数据库获取训练数据的特征列作为标准
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT feature_vector FROM features 
                WHERE user_id LIKE 'training_user%' 
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                self.logger.warning("没有找到训练数据，无法对齐特征")
                return features_df
            
            # 解析训练数据的特征列
            training_features = json.loads(result[0])
            target_features = list(training_features.keys())
            
            # 确保所有目标特征都存在
            for feature in target_features:
                if feature not in features_df.columns:
                    features_df[feature] = 0.0  # 用0填充缺失特征
            
            # 只保留目标特征列
            aligned_features = features_df[target_features].copy()
            
            self.logger.info(f"特征对齐完成: {len(aligned_features.columns)} 个特征")
            return aligned_features
            
        except Exception as e:
            self.logger.error(f"特征对齐失败: {str(e)}")
            return features_df

    def process_features(self, df):
        """使用feature_engineering模块处理特征"""
        if df.empty:
            self.logger.warning("输入数据为空，无法处理特征")
            return pd.DataFrame()
        
        if not FEATURE_ENGINEERING_AVAILABLE:
            self.logger.error("feature_engineering模块不可用")
            return pd.DataFrame()
        
        try:
            self.logger.info("开始使用feature_engineering处理鼠标特征")
            
            # 复制数据避免修改原始数据
            df = df.copy()
            
            # 1. 数据预处理 (复用feature_engineering的函数)
            self.logger.debug("执行数据预处理")
            df = remove_outlier(df)
            df = fill_in_scroll(df)
            df = change_from_prev_rec(df)
            df = classify_categ(df)
            
            # 2. 特征提取 (根据配置选择)
            feature_config = self.config.get_feature_config()
            
            if feature_config.get('velocity_features', True):
                self.logger.debug("提取速度特征")
                df = add_velocity_features(df)
            
            if feature_config.get('trajectory_features', True):
                self.logger.debug("提取轨迹特征")
                df = add_trajectory_features(df)
            
            if feature_config.get('temporal_features', True):
                self.logger.debug("提取时间特征")
                df = add_temporal_features(df)
            
            if feature_config.get('statistical_features', True):
                self.logger.debug("提取统计特征")
                df = add_statistical_features(df)
            
            if feature_config.get('interaction_features', True):
                self.logger.debug("提取交互特征")
                df = add_interaction_features(df)
            
            if feature_config.get('geometric_features', True):
                self.logger.debug("提取几何特征")
                df = add_geometric_features(df)
            
            if feature_config.get('advanced_features', True):
                self.logger.debug("提取高级特征")
                df = add_advanced_features(df)
            
            # 3. 特征聚合
            self.logger.debug("聚合特征")
            aggregated_features = aggregate_features(df)
            
            # 4. 特征对齐（确保与训练数据一致）
            if not aggregated_features.empty:
                aggregated_features = self._align_features_with_training_data(aggregated_features)
            
            self.logger.info(f"特征处理完成，生成了 {len(aggregated_features)} 条聚合特征")
            return aggregated_features
            
        except Exception as e:
            self.logger.error(f"特征处理失败: {str(e)}")
            return pd.DataFrame()

    def save_features_to_db(self, features_df, user_id, session_id):
        """保存特征到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 将特征转换为JSON字符串
            features_df['feature_vector'] = features_df.apply(
                lambda row: json.dumps(row.to_dict()), axis=1
            )
            
            # 保存到数据库
            for _, row in features_df.iterrows():
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO features 
                    (user_id, session_id, timestamp, feature_vector)
                    VALUES (?, ?, ?, ?)
                ''', (
                    user_id,
                    session_id,
                    time.time(),
                    row.get('feature_vector', '{}')
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"保存了 {len(features_df)} 条特征到数据库")
            
        except Exception as e:
            self.logger.error(f"保存特征到数据库失败: {str(e)}")

    def process_session_features(self, user_id, session_id):
        """处理指定会话的特征"""
        try:
            self.logger.info(f"处理用户 {user_id} 会话 {session_id} 的特征")
            
            # 检查数据库连接
            if not Path(self.db_path).exists():
                self.logger.error(f"数据库文件不存在: {self.db_path}")
                return False
            
            # 检查是否有鼠标事件数据
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM mouse_events 
                WHERE user_id = ? AND session_id = ?
            ''', (user_id, session_id))
            count = cursor.fetchone()[0]
            conn.close()
            
            if count == 0:
                self.logger.warning(f"用户 {user_id} 会话 {session_id} 没有鼠标事件数据")
                return False
            
            self.logger.info(f"用户 {user_id} 会话 {session_id} 有 {count} 条鼠标事件数据")
            
            # 首先转换mouse_events数据为features
            conversion_success = self.convert_mouse_events_to_features(user_id, session_id)
            if not conversion_success:
                self.logger.warning(f"转换用户 {user_id} 会话 {session_id} 的鼠标事件数据失败")
                return False
            
            # 然后处理特征（如果需要进一步处理）
            # 这里可以添加额外的特征处理逻辑
            
            self.logger.info(f"用户 {user_id} 会话 {session_id} 的特征处理完成")
            return True
            
        except Exception as e:
            self.logger.error(f"处理用户 {user_id} 会话 {session_id} 的特征失败: {str(e)}")
            import traceback
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            return False

    def process_all_user_sessions(self, user_id):
        """处理用户所有会话的特征"""
        try:
            self.logger.info(f"处理用户 {user_id} 所有会话的特征")
            
            # 首先转换所有mouse_events数据为features
            conversion_success = self.convert_mouse_events_to_features(user_id)
            if not conversion_success:
                self.logger.warning(f"转换用户 {user_id} 的鼠标事件数据失败")
                return False
            
            # 获取用户的所有会话
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT session_id FROM mouse_events 
                WHERE user_id = ?
                ORDER BY session_id
            ''', (user_id,))
            
            sessions = cursor.fetchall()
            conn.close()
            
            if not sessions:
                self.logger.warning(f"用户 {user_id} 没有会话数据")
                return False
            
            self.logger.info(f"用户 {user_id} 共有 {len(sessions)} 个会话")
            
            # 处理每个会话的特征
            success_count = 0
            for (session_id,) in sessions:
                if self.process_session_features(user_id, session_id):
                    success_count += 1
            
            self.logger.info(f"用户 {user_id} 特征处理完成: {success_count}/{len(sessions)} 个会话成功")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"处理用户 {user_id} 所有会话的特征失败: {str(e)}")
            return False

    def get_user_features(self, user_id, limit=None):
        """获取用户的特征数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT * FROM features 
                WHERE user_id = ?
                ORDER BY timestamp DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            self.logger.info(f"获取用户 {user_id} 的特征数据: {len(df)} 条记录")
            return df
            
        except Exception as e:
            self.logger.error(f"获取用户特征数据失败: {str(e)}")
            return pd.DataFrame()

    def convert_mouse_events_to_features(self, user_id, session_id=None):
        """将mouse_events数据转换为features并保存到数据库"""
        try:
            self.logger.info(f"开始转换用户 {user_id} 的鼠标事件数据为特征")
            
            # 加载鼠标事件数据
            df = self.load_data_from_db(user_id, session_id)
            if df.empty:
                self.logger.warning(f"用户 {user_id} 没有鼠标事件数据")
                return False
            
            # 处理特征
            features_df = self.process_features(df)
            if features_df.empty:
                self.logger.warning(f"用户 {user_id} 的特征处理结果为空")
                return False
            
            # 保存特征到数据库
            success = self.save_features_to_db(features_df, user_id, session_id)
            
            if success:
                self.logger.info(f"成功转换并保存了用户 {user_id} 的 {len(features_df)} 条特征数据")
            else:
                self.logger.error(f"保存用户 {user_id} 的特征数据失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"转换鼠标事件数据为特征失败: {str(e)}")
            return False 