# -*- coding: utf-8 -*-
"""Mouse dynamics

This script analyzes mouse event data to identify users based on their mouse behavior patterns.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sn
import os
import logging
from sklearn.preprocessing import MinMaxScaler, LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, confusion_matrix, classification_report, roc_auc_score
import xgboost as xgb
import pickle
import warnings
import joblib
from typing import List, Dict, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def featurize(df):
    """Extract features from mouse movement data"""
    features = []
    
    for session_id, group in df.groupby('session_id'):
        xList = group['screen_x'].values
        yList = group['screen_y'].values
        timestamps = group['timestamp'].values
        events = group['event_type'].values
        
        # Basic statistics
        center_x = np.mean(xList)
        center_y = np.mean(yList)
        first_x = xList[0]
        first_y = yList[0]
        
        # Click center
        click_mask = events == 5
        center_click_x = np.mean(xList[click_mask]) if np.any(click_mask) else 0
        center_click_y = np.mean(yList[click_mask]) if np.any(click_mask) else 0
        
        # Movement statistics
        dx = np.diff(xList)
        dy = np.diff(yList)
        dt = np.diff(timestamps)
        
        # Speed and acceleration
        speed = np.sqrt(dx**2 + dy**2) / (dt + 1e-6)  # Avoid division by zero
        acceleration = np.diff(speed) / (dt[1:] + 1e-6)
        
        # Direction changes
        angles = np.arctan2(dy, dx)
        angle_changes = np.diff(angles)
        
        # Event ratios
        event_counts = np.bincount(events.astype(int), minlength=6)[1:]  # Exclude 0
        event_ratios = event_counts / len(events)
        
        # Additional features
        radius = np.max(np.sqrt((xList - center_x)**2 + (yList - center_y)**2))
        
        # Create feature dictionary
        feature_dict = {
            'session_id': session_id,
            'center_x': center_x,
            'center_y': center_y,
            'center_click_x': center_click_x,
            'center_click_y': center_click_y,
            'first_x': first_x,
            'first_y': first_y,
            'radius': radius,
            'session_duration': timestamps[-1] - timestamps[0],
            'avg_speed': np.mean(speed) if len(speed) > 0 else 0,
            'max_speed': np.max(speed) if len(speed) > 0 else 0,
            'speed_std': np.std(speed) if len(speed) > 0 else 0,
            'accel_mean': np.mean(acceleration) if len(acceleration) > 0 else 0,
            'accel_std': np.std(acceleration) if len(acceleration) > 0 else 0,
            'angle_mean': np.mean(angles) if len(angles) > 0 else 0,
            'angle_std': np.std(angles) if len(angles) > 0 else 0,
            'angle_change_mean': np.mean(angle_changes) if len(angle_changes) > 0 else 0,
            'angle_change_std': np.std(angle_changes) if len(angle_changes) > 0 else 0,
        }
        
        # Add event ratios
        for i, ratio in enumerate(event_ratios, 1):
            feature_dict[f'ev{i}_ratio'] = ratio
            feature_dict[f'ev{i}_count'] = event_counts[i-1]
        
        features.append(feature_dict)
    
    return pd.DataFrame(features)

def plot_feature_importance(model, feature_names):
    """Plot feature importance"""
    importance = model.feature_importances_
    indices = np.argsort(importance)[::-1]
    
    plt.figure(figsize=(10, 6))
    plt.title('Feature Importance')
    plt.bar(range(len(importance)), importance[indices])
    plt.xticks(range(len(importance)), [feature_names[i] for i in indices], rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('feature_importance.png')
    plt.close()

def plot_confusion_matrix(y_true, y_pred, labels):
    """Plot confusion matrix"""
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sn.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig('confusion_matrix.png')
    plt.close()

class MouseDynamicsAnalyzer:
    def __init__(self, training_dir: str, test_dir: str, labels_file: str):
        self.training_dir = training_dir
        self.test_dir = test_dir
        self.labels_file = labels_file
        self.scaler = StandardScaler()
        
    def load_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """加载训练数据"""
        all_features = []
        all_labels = []
        
        # 遍历每个用户文件夹
        for user_id in range(1, 11):  # 10个用户
            user_dir = os.path.join(self.training_dir, f'user_{user_id}')
            if not os.path.exists(user_dir):
                logger.warning(f"User directory {user_dir} does not exist")
                continue
                
            # 加载该用户的所有session
            for session_file in os.listdir(user_dir):
                if session_file.endswith('.csv'):
                    session_path = os.path.join(user_dir, session_file)
                    features = self._process_session(session_path)
                    if features is not None:
                        all_features.append(features)
                        all_labels.append(user_id)  # 用户ID作为标签
                        
        return np.array(all_features), np.array(all_labels)
    
    def load_test_data(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """加载测试数据和标签"""
        all_features = []
        all_labels = []
        session_ids = []
        
        # 读取标签文件
        labels_df = pd.read_csv(self.labels_file)
        labels_dict = dict(zip(labels_df['session_id'], labels_df['label']))
        
        # 遍历每个用户文件夹
        for user_id in range(1, 11):
            user_dir = os.path.join(self.test_dir, f'user_{user_id}')
            if not os.path.exists(user_dir):
                logger.warning(f"User directory {user_dir} does not exist")
                continue
                
            # 加载该用户的所有session
            for session_file in os.listdir(user_dir):
                if session_file.endswith('.csv'):
                    session_id = session_file.replace('.csv', '')
                    session_path = os.path.join(user_dir, session_file)
                    features = self._process_session(session_path)
                    if features is not None:
                        all_features.append(features)
                        all_labels.append(labels_dict.get(session_id, 0))
                        session_ids.append(session_id)
                        
        return np.array(all_features), np.array(all_labels), session_ids
    
    def _process_session(self, session_path: str) -> np.ndarray:
        """处理单个session文件并提取特征"""
        try:
            # 读取session数据
            df = pd.read_csv(session_path)
            
            # 提取特征
            features = []
            
            # 1. 基本位置特征 (8个)
            features.extend([
                df['x'].mean(), df['x'].std(), df['x'].min(), df['x'].max(),
                df['y'].mean(), df['y'].std(), df['y'].min(), df['y'].max()
            ])
            
            # 2. 速度特征 (12个)
            if len(df) > 1:
                dx = df['x'].diff().dropna()
                dy = df['y'].diff().dropna()
                dt = df['timestamp'].diff().dropna()
                speeds = np.sqrt(dx**2 + dy**2) / dt
                features.extend([
                    speeds.mean(), speeds.std(), speeds.min(), speeds.max(),
                    speeds.median(), speeds.skew(), speeds.kurtosis(),
                    np.percentile(speeds, 25), np.percentile(speeds, 75),
                    speeds.var(), np.mean(np.abs(speeds)), np.std(np.abs(speeds))
                ])
            
            # 3. 事件类型统计 (12个)
            event_types = df['button'].value_counts(normalize=True)
            for event_type in range(6):
                features.append(event_types.get(event_type, 0))
            # 添加事件类型的变化率
            event_changes = df['button'].diff().dropna()
            for event_type in range(6):
                features.append(np.mean(event_changes == event_type))
            
            # 4. 角度特征 (16个)
            if len(df) > 1:
                angles = np.arctan2(dy, dx)
                angle_changes = np.diff(angles)
                features.extend([
                    angles.mean(), angles.std(), angles.min(), angles.max(),
                    angles.median(), angles.skew(), angles.kurtosis(),
                    np.percentile(angles, 25), np.percentile(angles, 75),
                    angle_changes.mean(), angle_changes.std(),
                    angle_changes.min(), angle_changes.max(),
                    angle_changes.median(), angle_changes.skew()
                ])
            
            # 5. 时间特征 (8个)
            timestamps = df['timestamp']
            time_diffs = timestamps.diff().dropna()
            features.extend([
                timestamps.max() - timestamps.min(),  # 总时长
                time_diffs.mean(), time_diffs.std(),
                time_diffs.min(), time_diffs.max(),
                time_diffs.median(), time_diffs.skew(),
                np.percentile(time_diffs, 75)
            ])
            
            # 6. 移动距离特征 (8个)
            if len(df) > 1:
                distances = np.sqrt(dx**2 + dy**2)
                features.extend([
                    distances.sum(),  # 总距离
                    distances.mean(), distances.std(),
                    distances.min(), distances.max(),
                    distances.median(), distances.skew(),
                    np.percentile(distances, 75)
                ])
            
            # 7. 加速度特征 (12个)
            if len(df) > 2:
                accel = np.diff(speeds) / dt[1:]
                features.extend([
                    accel.mean(), accel.std(),
                    accel.min(), accel.max(),
                    accel.median(), accel.skew(),
                    accel.kurtosis(),
                    np.percentile(accel, 25), np.percentile(accel, 75),
                    np.mean(np.abs(accel)), np.std(np.abs(accel)),
                    np.max(np.abs(accel))
                ])
            
            # 8. 加加速度(jerk)特征 (8个)
            if len(df) > 3:
                jerk = np.diff(accel) / dt[2:]
                features.extend([
                    jerk.mean(), jerk.std(),
                    jerk.min(), jerk.max(),
                    jerk.median(), jerk.skew(),
                    np.mean(np.abs(jerk)), np.max(np.abs(jerk))
                ])
            
            # 9. 网格分布特征 (100个)
            grid_size = 10
            x_grid = pd.cut(df['x'], bins=grid_size, labels=False)
            y_grid = pd.cut(df['y'], bins=grid_size, labels=False)
            grid_counts = pd.crosstab(x_grid, y_grid).values.flatten()
            features.extend(grid_counts)
            
            # 10. 象限特征 (8个)
            screen_center_x = df['x'].mean()
            screen_center_y = df['y'].mean()
            quadrants = []
            for x, y in zip(df['x'], df['y']):
                if x >= screen_center_x and y >= screen_center_y:
                    quadrants.append(0)
                elif x < screen_center_x and y >= screen_center_y:
                    quadrants.append(1)
                elif x < screen_center_x and y < screen_center_y:
                    quadrants.append(2)
                else:
                    quadrants.append(3)
            quadrants = np.array(quadrants)
            for i in range(4):
                features.append(np.mean(quadrants == i))
            # 添加象限转换频率
            quadrant_changes = np.diff(quadrants)
            for i in range(4):
                features.append(np.mean(quadrant_changes == i))
            
            # 11. 曲率特征 (8个)
            if len(df) > 2:
                # 计算曲率
                dx2 = np.diff(dx)
                dy2 = np.diff(dy)
                curvatures = np.abs(dx2 * dy - dy2 * dx) / (dx**2 + dy**2)**1.5
                curvatures = curvatures[~np.isnan(curvatures)]
                features.extend([
                    curvatures.mean(), curvatures.std(),
                    curvatures.min(), curvatures.max(),
                    curvatures.median(), curvatures.skew(),
                    np.mean(np.abs(curvatures)), np.max(np.abs(curvatures))
                ])
            
            # 12. 频域特征 (16个)
            if len(df) > 1:
                # 对x和y坐标进行FFT
                fft_x = np.fft.fft(df['x'])
                fft_y = np.fft.fft(df['y'])
                # 取前8个频率分量的幅值
                for i in range(8):
                    features.append(np.abs(fft_x[i]))
                    features.append(np.abs(fft_y[i]))
            
            # 13. 时间序列特征 (12个)
            if len(df) > 1:
                # 计算自相关
                for lag in [1, 2, 3]:
                    features.append(df['x'].autocorr(lag))
                    features.append(df['y'].autocorr(lag))
                # 计算移动平均
                for window in [5, 10, 15]:
                    features.append(df['x'].rolling(window=window).mean().mean())
                    features.append(df['y'].rolling(window=window).mean().mean())
            
            # 14. 运动模式特征 (8个)
            if len(df) > 1:
                # 计算直线运动比例
                straight_movements = np.abs(angle_changes) < np.pi/6
                features.append(np.mean(straight_movements))
                # 计算急转弯比例
                sharp_turns = np.abs(angle_changes) > np.pi/2
                features.append(np.mean(sharp_turns))
                # 计算停顿比例
                stops = speeds < np.mean(speeds) * 0.1
                features.append(np.mean(stops))
                # 计算加速/减速比例
                accel_changes = np.diff(speeds)
                features.append(np.mean(accel_changes > 0))
                features.append(np.mean(accel_changes < 0))
                # 计算运动方向变化
                features.append(np.mean(np.abs(angle_changes)))
                # 计算运动连续性
                features.append(np.mean(np.abs(np.diff(speeds)) < np.std(speeds)))
                # 计算运动规律性
                features.append(np.std(np.diff(speeds)) / np.mean(speeds))
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error processing session {session_path}: {str(e)}")
            return None
    
    def train_and_evaluate(self):
        """训练模型并评估"""
        # 加载训练数据
        logger.info("Loading training data...")
        X_train, y_train = self.load_training_data()
        
        # 加载测试数据
        logger.info("Loading test data...")
        X_test, y_test, session_ids = self.load_test_data()
        
        # 特征标准化
        logger.info("Standardizing features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 训练XGBoost模型
        logger.info("Training XGBoost model...")
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        
        model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            early_stopping_rounds=10,
            verbose=True
        )
        
        # 预测测试集
        logger.info("Making predictions...")
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        
        # 计算AUC
        auc = roc_auc_score(y_test, y_pred_proba)
        logger.info(f"\nAUC Score: {auc:.4f}")
        
        # 保存预测结果
        results_df = pd.DataFrame({
            'session_id': session_ids,
            'anomaly_score': y_pred_proba
        })
        results_df.to_csv('predictions.csv', index=False)
        logger.info("Predictions saved to predictions.csv")
        
        # 保存模型和scaler
        os.makedirs('models', exist_ok=True)
        joblib.dump(model, 'models/mouse_dynamics_model.pkl')
        joblib.dump(self.scaler, 'models/scaler.pkl')
        logger.info("Model and scaler saved to models/")
        
        # 绘制特征重要性图
        plt.figure(figsize=(10, 6))
        xgb.plot_importance(model, max_num_features=20)
        plt.title('Feature Importance')
        plt.tight_layout()
        plt.savefig('models/feature_importance.png')
        logger.info("Feature importance plot saved to models/feature_importance.png")
        
        return model, self.scaler, auc

def main():
    # 设置数据目录
    training_dir = 'training_files'
    test_dir = 'test_files'
    labels_file = 'public_labels.csv'
    
    try:
        logger.info("Starting mouse dynamics analysis...")
        analyzer = MouseDynamicsAnalyzer(training_dir, test_dir, labels_file)
        model, scaler, auc = analyzer.train_and_evaluate()
        logger.info(f"Analysis completed. Final AUC: {auc:.4f}")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()

