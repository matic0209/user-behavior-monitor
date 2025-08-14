import pandas as pd
import numpy as np
import os
import pickle
from datetime import datetime
from sklearn.metrics import accuracy_score, f1_score, roc_curve, auc, roc_auc_score
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
import matplotlib.pyplot as plt
from multiprocessing import Pool, cpu_count, TimeoutError
import psutil
import math
import signal
from functools import partial
import time
try:
    from src.classification import prepare_features
    CLASSIFICATION_AVAILABLE = True
except ImportError:
    try:
        from src.classification_mock import prepare_features
        CLASSIFICATION_AVAILABLE = False
        print("使用模拟的prepare_features函数")
    except ImportError:
        CLASSIFICATION_AVAILABLE = False
        def prepare_features(df, encoders):
            """模拟的特征准备函数"""
            print("使用内置模拟的prepare_features函数")
            return df
import logging

# 配置日志记录
def setup_logging():
    """设置日志记录系统"""
    # 创建logs目录
    os.makedirs('logs', exist_ok=True)
    
    # 获取当前时间作为文件名的一部分
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清除现有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 创建文件处理器 - 普通日志
    log_file = f'logs/predict_{timestamp}.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(log_format)
    
    # 创建文件处理器 - 错误日志
    error_file = f'logs/predict_error_{timestamp}.log'
    error_handler = logging.FileHandler(error_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    
    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_message(message, level='info'):
    """记录日志消息"""
    logger = logging.getLogger()
    if level.lower() == 'error':
        logger.error(message)
    else:
        logger.info(message)

# 初始化日志系统
setup_logging()

def load_models():
    """Load trained models"""
    log_message("Loading models...")
    model_info = {}
    
    # 遍历models目录下的所有模型文件
    for file in os.listdir('models'):
        if file.endswith('_model.pkl'):
            user_id = file.replace('_model.pkl', '')
            try:
                # 加载模型
                with open(f'models/{user_id}_model.pkl', 'rb') as f:
                    model = pickle.load(f)
                
                # 加载scaler
                with open(f'models/{user_id}_scaler.pkl', 'rb') as f:
                    scaler = pickle.load(f)
                
                # 加载特征名称
                with open(f'models/{user_id}_features.pkl', 'rb') as f:
                    feature_names = pickle.load(f)
                
                model_info[user_id] = {
                    'model': model,
                    'scaler': scaler,
                    'feature_names': feature_names
                }
                log_message(f"Loaded model for user {user_id}")
            except Exception as e:
                log_message(f"Error loading model for user {user_id}: {str(e)}", level='error')
                continue
    
    if not model_info:
        log_message("No models were loaded successfully", level='error')
        raise ValueError("No models were loaded successfully")
    
    return model_info

def load_data():
    """Load training and test data"""
    log_message("Loading data...")
    
    try:
        # Load training data for label encoding
        with open('data/processed/all_training_aggregation.pickle', 'rb') as f:
            train_data = pickle.load(f)
        
        # Load test data
        with open('data/processed/all_test_aggregation.pickle', 'rb') as f:
            test_data = pickle.load(f)
        
        return train_data, test_data
    except Exception as e:
        log_message(f"Error loading data: {str(e)}", level='error')
        raise

def prepare_encoders(train_data):
    """Prepare encoders once for all sessions"""
    log_message("Preparing encoders...")
    
    # Create encoders
    le_button = LabelEncoder().fit(train_data['button'].unique())
    le_state = LabelEncoder().fit(train_data['state'].unique())
    le_categ = LabelEncoder().fit(train_data['categ'].unique())
    
    # Prepare one-hot encoder
    oh_categ = OneHotEncoder()
    train_categ_le = le_categ.transform(train_data['categ'])
    vec_size = train_data['categ_agg'].nunique()
    oh_categ.fit(train_categ_le.reshape(-1, 1))
    
    return {
        'le_button': le_button,
        'le_state': le_state,
        'le_categ': le_categ,
        'oh_categ': oh_categ,
        'vec_size': vec_size
    }

def remove_outlier(df):
    df = df[(df['x'] < 65535) & (df['y'] < 65535)].copy()
    df.reset_index(drop=True, inplace=True)
    return df.copy()

def fill_in_scroll(df):
    df.loc[df['button'] == "Scroll", ['x', 'y']] = np.nan
    df['x'] = df['x'].ffill()
    df['y'] = df['y'].ffill()
    return df.copy()

def change_from_prev_rec(df):
    df['distance_from_previous'] = np.sqrt((df['x'].diff())**2 + (df['y'].diff())**2)
    df['elapsed_time_from_previous'] = df['client timestamp'].diff()
    df['angle'] = np.arctan2(df['y'], df['x']) * 180 / np.pi
    df['angle_movement'] = df['angle'].diff()
    df['angle_movement_abs'] = abs(df['angle_movement'])
    return df.copy()

def classify_categ(df):
    # 确保 button 字段为字符串类型
    if 'button' in df.columns:
        df['button'] = df['button'].astype(str)
    df['categ'] = ""
    df.loc[(df['state'] == 'Pressed') & (df.shift(-1)['state'] == 'Released') \
           & (df.shift(-2)['state'] == 'Pressed') \
           & (df.shift(-3)['state'] == 'Released') \
           & (df.shift(-1)['button'] == df.shift(-2)['button']) \
           & (df.shift(-2)['elapsed_time_from_previous'] <= 5), 'categ'] = 'double_click'
    i = 0
    while i <= len(df.index)-4:
        if df.iloc[i]['categ'] == 'double_click':
            df.loc[i+1, 'categ'] = 'double_click'
            df.loc[i+2, 'categ'] = 'double_click'
            df.loc[i+3, 'categ'] = 'double_click'
            i += 4
        else:
            i += 1
    df.loc[(df['state'] == 'Pressed') & (df.shift(-1)['state'] == 'Released') \
           & (df['categ'] == '') & (df['button'] == 'Left'), 'categ'] = 'left_click'
    df.loc[(df['state'] == 'Pressed') & (df.shift(-1)['state'] == 'Released') \
           & (df['categ'] == '') & (df['button'] == 'Right'), 'categ'] = 'right_click'
    df.loc[((df['state'] == 'Pressed') & (df.shift(-1)['state'] == 'Drag')) \
           | (df['state'] == 'Drag') \
           | ((df['state'] == 'Released') & (df.shift()['state'] == 'Drag')), 'categ'] = 'drag'
    df.loc[(df['state'] == 'Move'), 'categ'] = 'move'
    df.loc[(df['state'].isin(['Down', 'Up'])), 'categ'] = 'scroll'
    df['categ'] = df['categ'].replace('', np.nan).ffill().fillna('move')
    filllastrow = pd.DataFrame(columns = df.columns)
    filllastrow.loc[0, 'categ'] = 'move'
    df = pd.concat([df, filllastrow])
    df['action_cnt'] = 0
    action_cnt = 0
    categ_current = np.nan
    for i in range(len(df.index)-2, -1, -1):
        if i == len(df.index)-2:
            categ_current = df.iloc[i]['categ']
        if ((df.iloc[i]['categ'] != df.iloc[i+1]['categ']) \
             & (df.iloc[i]['categ'] != 'move')) \
            or ((df.iloc[i]['categ'] != 'drag') \
             and (df.iloc[i+1]['categ'] == 'drag')) \
            or ((df.iloc[i+1]['elapsed_time_from_previous'] > 5) \
             and (df.iloc[i]['categ'] == 'move') \
             and (df.iloc[i+1]['categ'] == 'move')) \
            or ((df.iloc[i+1]['elapsed_time_from_previous'] > 5) \
             and (df.iloc[i]['categ'] == 'scroll') \
             and (df.iloc[i+1]['categ'] == 'scroll')):
            action_cnt -= 1
            categ_current = df.iloc[i]['categ']
            df.loc[i, 'action_cnt'] = action_cnt
            df.loc[i, 'categ_agg'] = categ_current
        else:
            df.loc[i, 'action_cnt'] = action_cnt
            df.loc[i, 'categ_agg'] = categ_current
    df['action_cnt'] = df['action_cnt'] - action_cnt
    df = df.iloc[:-1]
    return df.copy()

def add_velocity_features(df):
    """Add velocity and acceleration related features."""
    log_message("Adding velocity features...")
    
    # Handle division by zero in velocity calculation
    df['velocity'] = np.where(
        df['elapsed_time_from_previous'] > 0,
        df['distance_from_previous'] / df['elapsed_time_from_previous'],
        0  # Set velocity to 0 when time difference is 0
    )
    df['velocity_x'] = np.where(
        df['elapsed_time_from_previous'] > 0,
        df['x'].diff() / df['elapsed_time_from_previous'],
        0
    )
    df['velocity_y'] = np.where(
        df['elapsed_time_from_previous'] > 0,
        df['y'].diff() / df['elapsed_time_from_previous'],
        0
    )
    
    # Handle division by zero in acceleration calculation
    df['acceleration'] = np.where(
        df['elapsed_time_from_previous'] > 0,
        df['velocity'].diff() / df['elapsed_time_from_previous'],
        0
    )
    df['acceleration_x'] = np.where(
        df['elapsed_time_from_previous'] > 0,
        df['velocity_x'].diff() / df['elapsed_time_from_previous'],
        0
    )
    df['acceleration_y'] = np.where(
        df['elapsed_time_from_previous'] > 0,
        df['velocity_y'].diff() / df['elapsed_time_from_previous'],
        0
    )
    
    # Handle division by zero in jerk calculation
    df['jerk'] = np.where(
        df['elapsed_time_from_previous'] > 0,
        df['acceleration'].diff() / df['elapsed_time_from_previous'],
        0
    )
    
    # Handle division by zero in angular velocity calculation
    df['angular_velocity'] = np.where(
        df['elapsed_time_from_previous'] > 0,
        df['angle_movement'] / df['elapsed_time_from_previous'],
        0
    )
    
    # Replace infinite values with NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # Fill NaN values with 0 for velocity-related features
    velocity_cols = ['velocity', 'velocity_x', 'velocity_y', 
                    'acceleration', 'acceleration_x', 'acceleration_y',
                    'jerk', 'angular_velocity']
    df[velocity_cols] = df[velocity_cols].fillna(0)
    
    return df

def add_temporal_features(df):
    """Add time-based features."""
    log_message("Adding temporal features...")
    
    # Convert timestamp to datetime
    df['datetime'] = pd.to_datetime(df['client timestamp'], unit='s')
    
    # Time-based features
    df['hour'] = df['datetime'].dt.hour
    df['minute'] = df['datetime'].dt.minute
    df['second'] = df['datetime'].dt.second
    df['day_of_week'] = df['datetime'].dt.dayofweek
    
    # Time intervals
    df['time_since_start'] = (df['datetime'] - df['datetime'].iloc[0]).dt.total_seconds()
    
    # Action duration
    df['action_duration'] = df.groupby('action_cnt')['elapsed_time_from_previous'].transform('sum')
    
    return df

def add_trajectory_features(df):
    """Add features related to mouse movement trajectory."""
    # 确保索引是连续的
    df = df.reset_index(drop=True)
    
    # Curvature
    df['curvature'] = df['angle_movement'] / df['distance_from_previous']
    
    # Direction changes
    df['direction_change'] = (df['angle_movement'].abs() > 45).astype(int)
    
    # Straightness (ratio of direct distance to actual path length)
    window_size = 10
    df['path_length'] = df['distance_from_previous'].rolling(window=window_size, min_periods=1).sum()
    df['direct_distance'] = np.sqrt(
        (df['x'] - df['x'].shift(window_size))**2 + 
        (df['y'] - df['y'].shift(window_size))**2
    )
    df['straightness'] = df['direct_distance'] / df['path_length']
    
    # Movement complexity
    df['movement_complexity'] = df['angle_movement_abs'].rolling(window=window_size, min_periods=1).std()
    
    return df

def add_statistical_features(df):
    """Add statistical features using rolling windows."""
    log_message("Adding statistical features...")
    
    # 确保索引是连续的
    df = df.reset_index(drop=True)
    
    window_sizes = [5, 10, 20, 50]
    features = ['velocity', 'acceleration', 'angle_movement', 'distance_from_previous']
    
    for window in window_sizes:
        for feature in features:
            if feature in df.columns:
                # Basic statistics
                df[f'{feature}_mean_{window}'] = df[feature].rolling(window=window, min_periods=1).mean()
                df[f'{feature}_std_{window}'] = df[feature].rolling(window=window, min_periods=1).std()
                df[f'{feature}_min_{window}'] = df[feature].rolling(window=window, min_periods=1).min()
                df[f'{feature}_max_{window}'] = df[feature].rolling(window=window, min_periods=1).max()
                df[f'{feature}_range_{window}'] = df[f'{feature}_max_{window}'] - df[f'{feature}_min_{window}']
                
                # Advanced statistics
                df[f'{feature}_skew_{window}'] = df[feature].rolling(window=window, min_periods=1).skew()
                df[f'{feature}_kurt_{window}'] = df[feature].rolling(window=window, min_periods=1).kurt()
    
    return df

def add_interaction_features(df):
    """Add features related to user interaction patterns."""
    log_message("Adding interaction features...")
    
    # 确保索引是连续的
    df = df.reset_index(drop=True)
    
    # Click patterns
    df['click_interval'] = df[df['categ'].isin(['left_click', 'right_click', 'double_click'])]['elapsed_time_from_previous']
    
    # Movement patterns
    df['movement_after_click'] = df['distance_from_previous'].shift(-1)
    df['time_after_click'] = df['elapsed_time_from_previous'].shift(-1)
    
    # Action sequence features
    df['action_sequence'] = df.groupby('action_cnt')['categ'].transform(lambda x: '_'.join(x))
    
    # Interaction density
    window_size = 100
    df['is_click'] = df['categ'].isin(['left_click', 'right_click', 'double_click']).astype(int)
    df['interaction_density'] = df['is_click'].rolling(window=window_size, min_periods=1).mean()
    df = df.drop('is_click', axis=1)
    
    return df

def add_geometric_features(df):
    """Add geometric features related to mouse movement."""
    log_message("Adding geometric features...")
    
    # Area features
    df['area_covered'] = df['x'] * df['y']
    df['area_change'] = df['area_covered'].diff()
    
    # Distance from center
    center_x = df['x'].mean()
    center_y = df['y'].mean()
    df['distance_from_center'] = np.sqrt((df['x'] - center_x)**2 + (df['y'] - center_y)**2)
    
    # Screen quadrant
    df['quadrant'] = pd.cut(df['angle'], bins=[-180, -90, 0, 90, 180], labels=[1, 2, 3, 4])
    
    # Movement direction
    df['direction'] = pd.cut(df['angle'], bins=8, labels=range(8))
    
    return df

def add_advanced_features(df):
    """Add advanced features for more sophisticated behavior analysis."""
    log_message("Adding advanced features...")
    
    # 确保索引是连续的
    df = df.reset_index(drop=True)
    
    # 1. 计算基本统计特征
    window_sizes = [5, 10, 20, 50]
    for window in window_sizes:
        # 速度相关特征
        df[f'velocity_mean_{window}'] = df['velocity'].rolling(window=window, min_periods=1).mean()
        df[f'velocity_std_{window}'] = df['velocity'].rolling(window=window, min_periods=1).std()
        df[f'velocity_max_{window}'] = df['velocity'].rolling(window=window, min_periods=1).max()
        df[f'velocity_min_{window}'] = df['velocity'].rolling(window=window, min_periods=1).min()
        
        # 加速度相关特征
        df[f'acceleration_mean_{window}'] = df['acceleration'].rolling(window=window, min_periods=1).mean()
        df[f'acceleration_std_{window}'] = df['acceleration'].rolling(window=window, min_periods=1).std()
        df[f'acceleration_max_{window}'] = df['acceleration'].rolling(window=window, min_periods=1).max()
        df[f'acceleration_min_{window}'] = df['acceleration'].rolling(window=window, min_periods=1).min()
        
        # 角度相关特征
        df[f'angle_mean_{window}'] = df['angle_movement'].rolling(window=window, min_periods=1).mean()
        df[f'angle_std_{window}'] = df['angle_movement'].rolling(window=window, min_periods=1).std()
        df[f'angle_max_{window}'] = df['angle_movement'].rolling(window=window, min_periods=1).max()
        df[f'angle_min_{window}'] = df['angle_movement'].rolling(window=window, min_periods=1).min()
    
    # 2. 计算交互特征
    if 'categ' in df.columns:
        # 确保categ列是字符串类型
        df['categ'] = df['categ'].astype(str)
        
        # 计算各种动作的计数
        action_counts = pd.DataFrame({
            'click_count': (df['categ'] == 'click').astype(int),
            'move_count': (df['categ'] == 'move').astype(int),
            'drag_count': (df['categ'] == 'drag').astype(int),
            'scroll_count': (df['categ'] == 'scroll').astype(int)
        }, index=df.index)
        
        # 计算动作比率
        total_actions = action_counts.sum(axis=1)
        action_ratios = action_counts.div(total_actions, axis=0).fillna(0)
        
        # 重命名比率列
        action_ratios.columns = ['click_ratio', 'move_ratio', 'drag_ratio', 'scroll_ratio']
        
        # 合并回原始DataFrame
        df = pd.concat([df, action_counts, action_ratios], axis=1)
    
    # 3. 计算几何特征
    if 'x' in df.columns and 'y' in df.columns:
        geometric_features = pd.DataFrame({
            'x_mean': df['x'].mean(),
            'x_std': df['x'].std(),
            'x_range': df['x'].max() - df['x'].min(),
            'y_mean': df['y'].mean(),
            'y_std': df['y'].std(),
            'y_range': df['y'].max() - df['y'].min()
        }, index=df.index)
        df = pd.concat([df, geometric_features], axis=1)
    
    # 4. 计算时间特征
    if 'datetime' in df.columns:
        df['time_gap'] = df['datetime'].diff().dt.total_seconds()
        time_features = pd.DataFrame({
            'time_gap_mean': df['time_gap'].mean(),
            'time_gap_std': df['time_gap'].std(),
            'time_gap_min': df['time_gap'].min(),
            'time_gap_max': df['time_gap'].max()
        }, index=df.index)
        df = pd.concat([df, time_features], axis=1)
    
    return df

def get_category_mappings(train_data):
    mappings = {}
    for col in ['quadrant', 'direction']:
        if col in train_data.columns and str(train_data[col].dtype) == 'category':
            mappings[col] = train_data[col].cat.categories
        elif col in train_data.columns:
            # 兼容未保存为category类型的情况
            mappings[col] = pd.Series(train_data[col]).dropna().unique().tolist()
    return mappings

def prepare_features_for_prediction(df, encoders):
    """Prepare features for prediction."""
    return fe.prepare_features_for_model(df, encoders)

def process_file(file_path):
    """处理单个文件"""
    try:
        log_message(f"Processing file: {file_path}")
        
        # 加载数据
        df = pd.read_csv(file_path)
        
        # 数据预处理
        df = remove_outlier(df)
        df = fill_in_scroll(df)
        df = change_from_prev_rec(df)
        df = classify_categ(df)
        
        # 准备预测
        encoders = prepare_encoders(df)
        features = prepare_features_for_model(df, encoders)
        
        # 加载模型
        model_info = load_models()
        
        # 预测
        predictions = {}
        for user_id, info in model_info.items():
            model = info['model']
            scaler = info['scaler']
            feature_names = info['feature_names']
            
            # 选择特征
            X = features[feature_names]
            
            # 标准化
            X_scaled = scaler.transform(X)
            
            # 预测
            pred = model.predict_proba(X_scaled)[:, 1]
            predictions[user_id] = pred
        
        return predictions
        
    except Exception as e:
        log_message(f"Error processing file {file_path}: {str(e)}", level='error')
        return None

def get_system_info():
    """获取系统资源信息"""
    cpu_count = os.cpu_count()
    memory = psutil.virtual_memory()
    return {
        'cpu_count': cpu_count,
        'memory_total': memory.total / (1024 * 1024 * 1024),  # GB
        'memory_available': memory.available / (1024 * 1024 * 1024),  # GB
        'memory_percent': memory.percent
    }

def process_user_prediction_agg(args):
    """Process prediction for a single user using aggregated features"""
    user_id, user_test = args
    user_id_str = str(user_id)
    user_id_num = user_id_str.replace('user', '')  # 去掉前缀

    process = psutil.Process()
    log_message(f"[AGG] Process {process.pid} started for user {user_id}")
    log_message(f"[AGG] Process memory usage: {process.memory_info().rss / (1024 * 1024):.2f} MB")

    try:
        start_time = time.time()
        log_message(f"[AGG] Starting prediction for user {user_id}")
        log_message(f"[AGG] Input data shape: {user_test.shape}")
        
        # 直接用聚合特征做预测
        preds, probs = predict_user_behavior_agg(user_test, user_id_num)
    
        end_time = time.time()
        log_message(f"[AGG] Prediction completed for user {user_id} in {end_time - start_time:.2f} seconds")
        log_message(f"[AGG] Process memory usage after prediction: {process.memory_info().rss / (1024 * 1024):.2f} MB")

        results = []
        for i, row in user_test.iterrows():
            results.append({
                'filename': f"session_{row['session']}" if 'session' in row else f"session_{i}",
                'is_illegal': int(preds[i])
            })
        return results
    except Exception as e:
        log_message(f"[AGG] Prediction failed for user {user_id}: {str(e)}", level='error')
        return []

def predict_user_behavior_agg(test_data, user_id):
    """Predict user behavior using the trained model (aggregated features)."""
    try:
        # 加载模型和编码器
        model_path = f'./models/user_{user_id}_model.pkl'
        scaler_path = f'./models/user_{user_id}_scaler.pkl'
        feature_path = f'./models/user_{user_id}_features.pkl'

        if not os.path.exists(model_path):
            log_message(f"[AGG] Model file {model_path} not found", level='error')
            return None, None
        if not os.path.exists(scaler_path):
            log_message(f"[AGG] Scaler file {scaler_path} not found", level='error')
            return None, None
        if not os.path.exists(feature_path):
            log_message(f"[AGG] Feature file {feature_path} not found", level='error')
            return None, None
            
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        with open(feature_path, 'rb') as f:
            feature_names = pickle.load(f)

        # 1. 处理异常值并严格按训练特征顺序对齐
        X = test_data.reindex(columns=feature_names, fill_value=0).copy()
        X = X.replace([np.inf, -np.inf], 0)
        
        # 2. 确保所有特征都是float类型
        X = X.astype(float)
        
        # 3. 填充缺失值
        X = X.fillna(0)
        
        # 4. 标准化 -> 确保传给模型的是numpy，避免XGBoost特征名校验
        X_scaled = scaler.transform(X.values)
        
        # 5. 预测
        pred = model.predict(X_scaled)
        prob = model.predict_proba(X_scaled)[:, 1] if hasattr(model, 'predict_proba') else [0]*len(X)
        
        return pred, prob
    except Exception as e:
        log_message(f"[AGG] Error in predict_user_behavior_agg: {str(e)}", level='error')
        return None, None

def main():
    """Main function for batch prediction."""
    try:
        log_message("Starting batch prediction using aggregated test data...")
        
        # 显示系统信息
        log_message("System Information:")
        log_message(f"- CPU Cores: {os.cpu_count()}")
        log_message(f"- Total Memory: {psutil.virtual_memory().total / (1024**3):.2f} GB")
        log_message(f"- Available Memory: {psutil.virtual_memory().available / (1024**3):.2f} GB")
        log_message(f"- Memory Usage: {psutil.virtual_memory().percent}%")
        
        # 加载测试数据
        test_file = '../data/processed/all_test_aggregation.pickle'
        if not os.path.exists(test_file):
            log_message(f"Test file {test_file} not found", level='error')
            return
        
        test_data = pd.read_pickle(test_file)
        log_message(f"Loaded test data with shape: {test_data.shape}")
        
        # 获取所有用户ID
        user_ids = test_data['user'].unique()
        log_message(f"Found {len(user_ids)} users in test data")
        
        # 结果收集
        output_rows = []
        for user_id in user_ids:
            log_message(f"\nProcessing user {user_id}...")
            user_test_data = test_data[test_data['user'] == user_id].copy()
            pred, prob = predict_user_behavior_agg(user_test_data, user_id)
            if pred is not None and prob is not None:
                # 重置索引以确保索引连续
                user_test_data = user_test_data.reset_index(drop=True)
                for i in range(len(user_test_data)):
                    filename = f"session_{user_test_data.iloc[i]['session']}"
                    # 使用模型预测结果：pred为1表示是该用户，0表示不是该用户
                    # 所以is_illegal就是1 - pred
                    is_illegal = 1 - pred[i]
                    output_rows.append({
                        'filename': filename,
                        'is_illegal': is_illegal
                    })
            else:
                log_message(f"Failed to predict for user {user_id}", level='error')
        
        # 保存结果
        if output_rows:
            results_df = pd.DataFrame(output_rows)
            results_df.to_csv('../results/prediction_results.csv', index=False)
            log_message("\nPrediction results saved to ../results/prediction_results.csv")
        else:
            log_message("No valid results to save", level='error')
        
    except Exception as e:
        log_message(f"Error in main: {str(e)}", level='error')

def predict_anomaly(user_id, features, model_info=None):
    """预测异常行为 - 兼容性函数"""
    try:
        log_message(f"Predicting anomaly for user {user_id}...")
        
        if model_info is None:
            # 尝试加载模型
            try:
                model_info = load_models()
            except Exception as e:
                log_message(f"Error loading models: {str(e)}", level='error')
                return None
        
        if user_id not in model_info:
            log_message(f"No model found for user {user_id}", level='error')
            return None
        
        # 获取用户模型
        user_model_info = model_info[user_id]
        model = user_model_info['model']
        scaler = user_model_info['scaler']
        feature_names = user_model_info['feature_names']
        
        # 准备特征
        if isinstance(features, dict):
            # 如果是字典，转换为DataFrame
            feature_df = pd.DataFrame([features])
        elif isinstance(features, pd.DataFrame):
            feature_df = features.copy()
        else:
            log_message("Invalid features format", level='error')
            return None
        
        # 确保特征列对齐
        for feature in feature_names:
            if feature not in feature_df.columns:
                feature_df[feature] = 0.0

        # 严格按训练顺序对齐
        feature_df = feature_df.reindex(columns=feature_names, fill_value=0).fillna(0)

        # 标准化特征（使用numpy避免XGBoost特征名校验）
        X_np = feature_df.values
        if scaler is not None:
            X_np = scaler.transform(X_np)

        # 预测（numpy输入）
        prediction = model.predict(X_np)[0]
        prediction_proba = model.predict_proba(X_np)[0]
        
        # 计算异常分数
        if len(prediction_proba) > 1:
            anomaly_score = 1 - prediction_proba[1]  # 异常分数
        else:
            anomaly_score = 1 - prediction_proba[0]
        
        result = {
            'user_id': user_id,
            'prediction': prediction,
            'anomaly_score': anomaly_score,
            'confidence': max(prediction_proba),
            'is_normal': prediction == 1,
            'timestamp': datetime.now().isoformat()
        }
        
        log_message(f"Prediction completed for user {user_id}: {'normal' if result['is_normal'] else 'anomaly'}")
        return result
        
    except Exception as e:
        log_message(f"Error predicting anomaly for user {user_id}: {str(e)}", level='error')
        return None

def predict_user_behavior(user_id, features, threshold=0.5):
    """预测用户行为 - 兼容性函数"""
    try:
        log_message(f"Predicting behavior for user {user_id}...")
        
        # 调用异常预测函数
        result = predict_anomaly(user_id, features)
        
        if result is None:
            return None
        
        # 根据阈值判断是否为异常
        is_anomaly = result['anomaly_score'] > threshold
        
        result['is_anomaly'] = is_anomaly
        result['threshold'] = threshold
        
        return result
        
    except Exception as e:
        log_message(f"Error predicting behavior for user {user_id}: {str(e)}", level='error')
        return None

if __name__ == "__main__":
    main() 