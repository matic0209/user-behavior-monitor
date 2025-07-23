# User Authentication Based on Mouse Characteristics #

## Load Packages ##
import pandas as pd
import numpy as np
import os
import pickle
import time
from datetime import datetime
from sklearn.model_selection import train_test_split, StratifiedKFold, learning_curve, validation_curve, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, confusion_matrix, precision_recall_curve, average_precision_score
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.feature_selection import VarianceThreshold, SelectFromModel, SelectKBest
from sklearn.pipeline import Pipeline
from multiprocessing import Pool, cpu_count, shared_memory
import psutil
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import precision_score, recall_score, f1_score
from imblearn.over_sampling import SMOTE
from sklearn.feature_selection import mutual_info_classif
import logging
import gc
from typing import Dict, Any
import multiprocessing as mp
from functools import partial

# 定义常量
DATA_PATH = './data/processed/all_training_aggregation.pickle'
MODEL_DIR = './models'
LOG_DIR = './logs'

# 确保目录存在
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# preprocessing
# import feature_engineering as fe  # 已删除，不再需要

# Set random seed
np.random.seed(0)

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
    log_file = f'logs/classification_{timestamp}.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(log_format)
    
    # 创建文件处理器 - 错误日志
    error_file = f'logs/classification_error_{timestamp}.log'
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

def plot_feature_importance(model, user_id, feature_names=None):
    """绘制特征重要性"""
    try:
        # 获取特征重要性
        importance = model.feature_importances_
        
        # 如果没有提供特征名称，使用默认名称
        if feature_names is None:
            feature_names = [f'feature_{i}' for i in range(len(importance))]
        
        # 创建特征重要性的DataFrame
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        })
        
        # 按重要性排序
        importance_df = importance_df.sort_values('importance', ascending=False)
        
        # 只显示前20个最重要的特征
        importance_df = importance_df.head(20)
        
        # 绘制条形图
        plt.figure(figsize=(12, 6))
        sns.barplot(x='importance', y='feature', data=importance_df)
        plt.title(f'Feature Importance for User {user_id}')
        plt.xlabel('Importance')
        plt.ylabel('Feature')
        plt.tight_layout()
        plt.savefig(f'results/feature_importance_user_{user_id}.png')
        plt.close()
        
    except Exception as e:
        log_message(f"Error plotting feature importance for user {user_id}: {str(e)}", level='error')

def plot_roc_curve(y_true, y_pred, title="ROC Curve"):
    """Plot ROC curve"""
    from sklearn.metrics import roc_curve
    fpr, tpr, _ = roc_curve(y_true, y_pred)
    auc = roc_auc_score(y_true, y_pred)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f'AUC = {auc:.3f}')
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(title)
    plt.legend()
    
    # Save plot
    os.makedirs('results', exist_ok=True)
    plt.savefig(f'results/{title.lower().replace(" ", "_")}.png')
    plt.close()

def plot_pr_curve(y_true, y_pred, title="PR Curve"):
    """Plot Precision-Recall curve"""
    precision, recall, _ = precision_recall_curve(y_true, y_pred)
    avg_precision = average_precision_score(y_true, y_pred)
    
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, label=f'AP = {avg_precision:.3f}')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(title)
    plt.legend()
    
    # Save plot
    os.makedirs('results', exist_ok=True)
    plt.savefig(f'results/{title.lower().replace(" ", "_")}.png')
    plt.close()

def engineer_features(df, is_training=True, scaler=None):
    """特征工程，创建新特征"""
    try:
        log_message("Starting feature engineering...")
        
        # 创建特征字典来存储所有新特征
        feature_dict = {}
        
        # 1. 时间特征
        log_message("Creating time-based features...")
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            feature_dict['hour'] = df['timestamp'].dt.hour
            feature_dict['day_of_week'] = df['timestamp'].dt.dayofweek
            feature_dict['is_weekend'] = feature_dict['day_of_week'].isin([5, 6]).astype(int)
        
        # 2. 数值特征
        log_message("Creating numerical features...")
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        numeric_cols = [col for col in numeric_cols if col not in ['user', 'session']]
        
        # 3. 组合特征
        log_message("Creating interaction features...")
        if len(numeric_cols) >= 2:
            interaction_features = {}
            for i, col1 in enumerate(numeric_cols[:-1]):
                for col2 in numeric_cols[i+1:]:
                    interaction_features[f'{col1}_{col2}_interact'] = df[col1] * df[col2]
            feature_dict.update(interaction_features)
        
        # 4. 比率特征
        log_message("Creating ratio features...")
        if len(numeric_cols) >= 2:
            ratio_features = {}
            for i, col1 in enumerate(numeric_cols[:-1]):
                for col2 in numeric_cols[i+1:]:
                    # 避免除以零
                    denominator = df[col2].replace(0, np.nan)
                    ratio_features[f'{col1}_{col2}_ratio'] = df[col1] / denominator
                    ratio_features[f'{col1}_{col2}_ratio'] = ratio_features[f'{col1}_{col2}_ratio'].fillna(0)
            feature_dict.update(ratio_features)
        
        # 5. 一次性创建所有新特征
        log_message("Merging all features...")
        new_features = pd.DataFrame(feature_dict, index=df.index)
        
        # 6. 处理缺失值
        log_message("Handling missing values...")
        new_features = new_features.fillna(0)
        
        # 7. 合并原始特征和新特征
        log_message("Combining with original features...")
        result = pd.concat([df, new_features], axis=1)
        
        # 8. 删除不需要的列
        if 'timestamp' in result.columns:
            result = result.drop('timestamp', axis=1)
        
        log_message(f"Feature engineering completed. Created {len(new_features.columns)} new features.")
        return result
        
    except Exception as e:
        log_message(f"Error in engineer_features: {str(e)}", level='error')
        raise

def select_features(X_train, y_train, X_val, threshold=0.01):
    """特征选择：使用方差阈值和互信息"""
    try:
        # 1. 确保输入数据是DataFrame格式
        if not isinstance(X_train, pd.DataFrame):
            X_train = pd.DataFrame(X_train)
        if not isinstance(X_val, pd.DataFrame):
            X_val = pd.DataFrame(X_val)
            
        # 2. 处理缺失值
        X_train = X_train.fillna(0)
        X_val = X_val.fillna(0)
        
        # 3. 确保训练集和验证集具有相同的列
        common_cols = X_train.columns.intersection(X_val.columns)
        if len(common_cols) == 0:
            raise ValueError("No common columns between train and validation sets")
            
        X_train = X_train[common_cols]
        X_val = X_val[common_cols]
        
        # 4. 移除低方差特征
        selector = VarianceThreshold(threshold=threshold)
        X_train_var = selector.fit_transform(X_train)
        X_val_var = selector.transform(X_val)
        
        # 获取保留的特征索引
        var_features = selector.get_support()
        
        # 5. 使用互信息选择特征
        mi_selector = SelectKBest(mutual_info_classif, k='all')
        mi_selector.fit(X_train_var, y_train)
        
        # 获取互信息分数
        mi_scores = mi_selector.scores_
        
        # 选择互信息分数大于阈值的特征
        mi_threshold = np.percentile(mi_scores, 50)  # 选择前50%的特征
        mi_features = mi_scores > mi_threshold
        
        # 组合两种选择方法的结果
        selected_features = var_features & mi_features
        
        # 应用特征选择
        X_train_selected = X_train_var[:, selected_features]
        X_val_selected = X_val_var[:, selected_features]
        
        # 记录选择的特征数量
        n_features = X_train.shape[1]
        n_selected = X_train_selected.shape[1]
        log_message(f"Selected {n_selected} features out of {n_features} ({(n_selected/n_features)*100:.1f}%)")
        
        return X_train_selected, X_val_selected, selected_features
        
    except Exception as e:
        log_message(f"Error in feature selection: {str(e)}", level='error')
        # 如果特征选择失败，返回原始数据
        return X_train.values, X_val.values, np.ones(X_train.shape[1], dtype=bool)

def analyze_data_distribution(X_train, y_train, X_val, y_val, user_id):
    """分析数据分布"""
    try:
        analysis = {}
        
        # 1. 基本统计信息
        analysis['train_samples'] = len(X_train)
        analysis['val_samples'] = len(X_val)
        analysis['train_pos_ratio'] = y_train.mean()
        analysis['val_pos_ratio'] = y_val.mean()
        
        # 2. 特征分布分析
        numeric_cols = X_train.select_dtypes(include=[np.number]).columns
        feature_stats = {}
        for col in numeric_cols:
            feature_stats[col] = {
                'train_mean': X_train[col].mean(),
                'train_std': X_train[col].std(),
                'val_mean': X_val[col].mean(),
                'val_std': X_val[col].std(),
                'train_skew': X_train[col].skew(),
                'train_kurt': X_train[col].kurtosis()
            }
        analysis['feature_stats'] = feature_stats
        
        # 3. 相关性分析
        corr_matrix = X_train[numeric_cols].corr()
        high_corr_pairs = []
        for i in range(len(numeric_cols)):
            for j in range(i+1, len(numeric_cols)):
                corr = corr_matrix.iloc[i, j]
                if abs(corr) > 0.8:
                    high_corr_pairs.append((numeric_cols[i], numeric_cols[j], corr))
        analysis['high_corr_pairs'] = high_corr_pairs
        
        # 4. 缺失值分析
        missing_train = X_train.isnull().sum()
        missing_val = X_val.isnull().sum()
        analysis['missing_values'] = {
            'train': missing_train[missing_train > 0].to_dict(),
            'val': missing_val[missing_val > 0].to_dict()
        }
        
        # 5. 异常值分析
        outliers = {}
        for col in numeric_cols:
            Q1 = X_train[col].quantile(0.25)
            Q3 = X_train[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers[col] = {
                'train': ((X_train[col] < (Q1 - 1.5 * IQR)) | (X_train[col] > (Q3 + 1.5 * IQR))).sum(),
                'val': ((X_val[col] < (Q1 - 1.5 * IQR)) | (X_val[col] > (Q3 + 1.5 * IQR))).sum()
            }
        analysis['outliers'] = outliers
        
        # 记录分析结果
        log_message(f"\nData Analysis for User {user_id}:")
        log_message(f"Training samples: {analysis['train_samples']}")
        log_message(f"Validation samples: {analysis['val_samples']}")
        log_message(f"Training positive ratio: {analysis['train_pos_ratio']:.2%}")
        log_message(f"Validation positive ratio: {analysis['val_pos_ratio']:.2%}")
        
        if high_corr_pairs:
            log_message("\nHighly correlated features:")
            for feat1, feat2, corr in high_corr_pairs:
                log_message(f"{feat1} - {feat2}: {corr:.2f}")
        
        if analysis['missing_values']['train'] or analysis['missing_values']['val']:
            log_message("\nMissing values:")
            for dataset, missing in analysis['missing_values'].items():
                if missing:
                    log_message(f"{dataset}: {missing}")
        
        if any(outliers.values()):
            log_message("\nOutliers detected:")
            for col, counts in outliers.items():
                if counts['train'] > 0 or counts['val'] > 0:
                    log_message(f"{col}: {counts['train']} in train, {counts['val']} in val")
        
        return analysis
        
    except Exception as e:
        log_message(f"Error in data analysis: {str(e)}")
        return None

def plot_data_distribution(X_train, y_train, X_val, y_val, user_id):
    """绘制数据分布图"""
    try:
        # 1. 标签分布
        plt.figure(figsize=(12, 4))
        plt.subplot(1, 2, 1)
        sns.countplot(x=y_train)
        plt.title(f'Training Set Label Distribution for User {user_id}')
        plt.subplot(1, 2, 2)
        sns.countplot(x=y_val)
        plt.title(f'Validation Set Label Distribution for User {user_id}')
        plt.tight_layout()
        plt.savefig(f'results/label_distribution_user_{user_id}.png')
        plt.close()
        
        # 2. 特征分布
        numeric_cols = X_train.select_dtypes(include=[np.number]).columns
        n_cols = min(5, len(numeric_cols))  # 选择前5个特征
        selected_cols = numeric_cols[:n_cols]
        
        plt.figure(figsize=(15, 10))
        for i, col in enumerate(selected_cols, 1):
            plt.subplot(2, 3, i)
            sns.kdeplot(data=X_train[col], label='Train')
            sns.kdeplot(data=X_val[col], label='Val')
            plt.title(f'{col} Distribution')
            plt.legend()
        plt.tight_layout()
        plt.savefig(f'results/feature_distribution_user_{user_id}.png')
        plt.close()
        
        # 3. 相关性热图
        plt.figure(figsize=(10, 8))
        corr_matrix = X_train[selected_cols].corr()
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
        plt.title(f'Feature Correlation Matrix for User {user_id}')
        plt.tight_layout()
        plt.savefig(f'results/correlation_matrix_user_{user_id}.png')
        plt.close()
        
        # 4. 箱线图
        plt.figure(figsize=(15, 6))
        X_train[selected_cols].boxplot()
        plt.title(f'Feature Boxplots for User {user_id}')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'results/boxplots_user_{user_id}.png')
        plt.close()
        
    except Exception as e:
        log_message(f"Error in plotting data distribution: {str(e)}")

def plot_training_curves(model, X_train, y_train, X_val, y_val, user_id):
    """绘制训练曲线"""
    try:
        # 1. 学习曲线
        train_sizes, train_scores, val_scores = learning_curve(
            model, X_train, y_train,
            cv=3, n_jobs=-1,
            train_sizes=np.linspace(0.1, 1.0, 5),  # 减少采样点数量
            scoring='roc_auc'
        )
        
        train_mean = np.mean(train_scores, axis=1)
        train_std = np.std(train_scores, axis=1)
        val_mean = np.mean(val_scores, axis=1)
        val_std = np.std(val_scores, axis=1)
        
        plt.figure(figsize=(10, 6))
        plt.plot(train_sizes, train_mean, label='Training score')
        plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.1)
        plt.plot(train_sizes, val_mean, label='Cross-validation score')
        plt.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.1)
        plt.title(f'Learning Curves for User {user_id}')
        plt.xlabel('Training Examples')
        plt.ylabel('ROC AUC Score')
        plt.legend(loc='best')
        plt.grid(True)
        plt.savefig(f'results/learning_curves_user_{user_id}.png')
        plt.close()
        
        # 2. 验证曲线
        param_range = np.logspace(-3, 3, 5)  # 减少参数范围
        train_scores, val_scores = validation_curve(
            model, X_train, y_train,
            param_name='learning_rate',
            param_range=param_range,
            cv=3, scoring='roc_auc', n_jobs=-1
        )
        
        train_mean = np.mean(train_scores, axis=1)
        train_std = np.std(train_scores, axis=1)
        val_mean = np.mean(val_scores, axis=1)
        val_std = np.std(val_scores, axis=1)
        
        plt.figure(figsize=(10, 6))
        plt.semilogx(param_range, train_mean, label='Training score')
        plt.fill_between(param_range, train_mean - train_std, train_mean + train_std, alpha=0.1)
        plt.semilogx(param_range, val_mean, label='Cross-validation score')
        plt.fill_between(param_range, val_mean - val_std, val_mean + val_std, alpha=0.1)
        plt.title(f'Validation Curves for User {user_id}')
        plt.xlabel('Learning Rate')
        plt.ylabel('ROC AUC Score')
        plt.legend(loc='best')
        plt.grid(True)
        plt.savefig(f'results/validation_curves_user_{user_id}.png')
        plt.close()
        
    except Exception as e:
        log_message(f"Error in plotting training curves: {str(e)}", level='error')

def prepare_features(X_train, X_val, y_train, data_analysis=False):
    """准备特征，包括特征工程和特征选择"""
    try:
        log_message("Starting feature preparation...")
        
        # 1. 基础特征工程
        log_message("Step 1: Basic feature engineering...")
        # 只保留基本的数值特征，不创建复杂的交互特征
        numeric_cols = X_train.select_dtypes(include=['int64', 'float64']).columns
        numeric_cols = [col for col in numeric_cols if col not in ['user', 'session']]
        
        X_train_engineered = X_train[numeric_cols].copy()
        X_val_engineered = X_val[numeric_cols].copy()
        
        # 2. 特征选择
        log_message("Step 2: Feature selection...")
        # 使用互信息选择特征
        mi_selector = SelectKBest(mutual_info_classif, k='all')
        mi_selector.fit(X_train_engineered, y_train)
        
        # 获取互信息分数
        mi_scores = pd.Series(mi_selector.scores_, index=X_train_engineered.columns)
        # 选择互信息分数大于中位数的特征
        selected_features = mi_scores[mi_scores > mi_scores.median()].index.tolist()
        
        X_train_selected = X_train_engineered[selected_features]
        X_val_selected = X_val_engineered[selected_features]
        
        log_message(f"Selected {len(selected_features)} features based on mutual information")
        
        # 3. 特征缩放
        log_message("Step 3: Scaling features...")
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train_selected)
        X_val_scaled = scaler.transform(X_val_selected)
        
        # 4. 转换为DataFrame
        X_train_processed = pd.DataFrame(X_train_scaled, columns=selected_features)
        X_val_processed = pd.DataFrame(X_val_scaled, columns=selected_features)
        
        # 5. 数据验证
        log_message("Step 5: Validating processed data...")
        # 检查是否有无穷值
        if np.isinf(X_train_processed.values).any() or np.isinf(X_val_processed.values).any():
            log_message("Warning: Infinite values detected, replacing with 0", level='warning')
            X_train_processed = X_train_processed.replace([np.inf, -np.inf], 0)
            X_val_processed = X_val_processed.replace([np.inf, -np.inf], 0)
        
        # 检查是否有缺失值
        if X_train_processed.isnull().any().any() or X_val_processed.isnull().any().any():
            log_message("Warning: Missing values detected, filling with 0", level='warning')
            X_train_processed = X_train_processed.fillna(0)
            X_val_processed = X_val_processed.fillna(0)
        
        # 6. 创建编码器
        log_message("Step 6: Creating encoders...")
        encoders = {}
        
        # 对分类特征进行编码
        categorical_cols = X_train.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            if col not in ['user', 'session']:
                le = LabelEncoder()
                le.fit(X_train[col].astype(str))
                encoders[col] = le
        
        # 7. 数据分析（如果需要）
        if data_analysis:
            log_message("Step 7: Performing data analysis...")
            # 计算特征统计信息
            train_stats = X_train_processed.describe()
            val_stats = X_val_processed.describe()
            
            # 检查特征分布
            log_message("Feature statistics:")
            log_message(f"Training set shape: {X_train_processed.shape}")
            log_message(f"Validation set shape: {X_val_processed.shape}")
            log_message(f"Number of features: {len(selected_features)}")
            
            # 检查标签分布
            log_message("Label distribution:")
            log_message(f"Training set: {y_train.value_counts(normalize=True).to_dict()}")
        
        log_message("Feature preparation completed successfully")
        return X_train_processed, X_val_processed, y_train, scaler, selected_features, encoders
        
    except Exception as e:
        log_message(f"Error in prepare_features: {str(e)}", level='error')
        raise

def create_shared_array(shape, dtype):
    """Create a shared memory array"""
    size = int(np.prod(shape))
    nbytes = size * np.dtype(dtype).itemsize
    shm = shared_memory.SharedMemory(create=True, size=nbytes)
    array = np.ndarray(shape, dtype=dtype, buffer=shm.buf)
    return array, shm

def get_optimal_process_count():
    """Calculate optimal number of processes based on system resources"""
    # Get system information
    cpu_count = os.cpu_count()
    memory = psutil.virtual_memory()
    memory_gb = memory.total / (1024 * 1024 * 1024)  # Convert to GB
    
    # 使用95%的CPU核心，留一些给系统
    cpu_based = max(1, int(cpu_count * 0.95))
    
    # 估计每个进程的内存使用（假设每个进程使用2GB）
    # 保留10%的内存给系统
    available_memory_gb = memory_gb * 0.9
    memory_based = max(1, int(available_memory_gb / 2))
    
    # 取CPU和内存限制中的较小值
    optimal_processes = min(cpu_based, memory_based)
    
    log_message(f"System Resources:")
    log_message(f"- CPU Cores: {cpu_count}")
    log_message(f"- Total Memory: {memory_gb:.1f}GB")
    log_message(f"- Available Memory: {memory.available / (1024 * 1024 * 1024):.1f}GB")
    log_message(f"- Optimal Process Count: {optimal_processes}")
    
    return optimal_processes

def monitor_resources():
    """Monitor system resources"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    log_message(f"Resource Usage:")
    log_message(f"- CPU Usage: {cpu_percent}%")
    log_message(f"- Memory Usage: {memory_percent}%")
    log_message(f"- Available Memory: {memory.available / (1024 * 1024 * 1024):.1f}GB")

def evaluate_model(y_true, y_pred, y_pred_proba):
    """评估模型性能"""
    try:
        # 计算各种评估指标
        metrics = {
            'auc': roc_auc_score(y_true, y_pred_proba),
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred),
            'recall': recall_score(y_true, y_pred),
            'f1': f1_score(y_true, y_pred)
        }
        
        # 计算混淆矩阵
        cm = confusion_matrix(y_true, y_pred)
        
        # 记录评估结果
        log_message("\nModel Evaluation Metrics:")
        for metric, value in metrics.items():
            log_message(f"{metric.upper()}: {value:.4f}")
        
        log_message("\nConfusion Matrix:")
        log_message(cm)
        
        return metrics, cm
        
    except Exception as e:
        log_message(f"Error in model evaluation: {str(e)}")
        return None, None

def load_and_split_data():
    """加载数据并进行预处理，保证健壮性和一致性"""
    try:
        log_message("Loading data...")
        # 使用pickle加载数据
        with open(DATA_PATH, 'rb') as f:
            data = pickle.load(f)
        log_message(f"Loaded {len(data)} records")

        # 获取所有用户
        users = data['user'].unique()
        log_message(f"Found {len(users)} unique users")

        processed_user_data = {}

        for user in users:
            try:
                log_message(f"\nProcessing data for user {user}")
                # 获取该用户的所有会话
                user_sessions = data[data['user'] == user]['session'].unique()
                if len(user_sessions) < 2:
                    log_message(f"User {user} has less than 2 sessions, skipping.", level='error')
                    continue

                # 随机分割会话为训练集和验证集
                np.random.shuffle(user_sessions)
                split_idx = int(len(user_sessions) * 0.8)
                train_sessions = user_sessions[:split_idx]
                val_sessions = user_sessions[split_idx:]
                if len(train_sessions) == 0 or len(val_sessions) == 0:
                    log_message(f"User {user} train/val session split empty, skipping.", level='error')
                    continue

                # 获取该用户的所有数据
                user_data = data[data['user'] == user].copy()
                other_users_data = data[data['user'] != user].copy()

                # 分割用户数据
                train_data = user_data[user_data['session'].isin(train_sessions)].copy()
                val_data = user_data[user_data['session'].isin(val_sessions)].copy()

                # 从其他用户数据中采样负样本
                n_train = len(train_data)
                n_val = len(val_data)
                
                # 确保负样本数量与正样本数量相同
                neg_train_data = other_users_data.sample(n=n_train, random_state=42)
                neg_val_data = other_users_data.sample(n=n_val, random_state=42)

                # 合并正负样本
                train_data = pd.concat([train_data, neg_train_data], ignore_index=True)
                val_data = pd.concat([val_data, neg_val_data], ignore_index=True)

                # 标签
                y_train = (train_data['user'] == user).astype(int)
                y_val = (val_data['user'] == user).astype(int)

                # 丢弃非特征列
                drop_cols = ['user', 'session']
                feature_cols = [col for col in train_data.columns if col not in drop_cols]
                X_train = train_data[feature_cols].copy()
                X_val = val_data[feature_cols].copy()

                # 特征列对齐
                X_val = X_val.reindex(columns=X_train.columns, fill_value=0)

                # 所有特征转为float，缺失值填充
                X_train = X_train.apply(pd.to_numeric, errors='coerce').fillna(0).astype(float)
                X_val = X_val.apply(pd.to_numeric, errors='coerce').fillna(0).astype(float)

                # 随机打乱
                X_train, y_train = X_train.sample(frac=1, random_state=42), y_train.sample(frac=1, random_state=42)
                X_val, y_val = X_val.sample(frac=1, random_state=42), y_val.sample(frac=1, random_state=42)

                # 检查样本数
                if len(X_train) == 0 or len(X_val) == 0:
                    log_message(f"User {user} has empty train/val after processing, skipping.", level='error')
                    continue

                # 检查标签分布
                train_pos_ratio = y_train.mean()
                val_pos_ratio = y_val.mean()
                log_message(f"User {user} label distribution - Train: {train_pos_ratio:.2%} positive, Val: {val_pos_ratio:.2%} positive")

                processed_user_data[user] = {
                    'X_train': X_train,
                    'X_val': X_val,
                    'y_train': y_train,
                    'y_val': y_val
                }
                log_message(f"User {user} train/val shape: {X_train.shape}, {X_val.shape}")
            except Exception as e:
                log_message(f"Error processing data for user {user}: {str(e)}", level='error')
                continue

        if not processed_user_data:
            raise ValueError("No valid user data after processing")
        return processed_user_data
    except Exception as e:
        log_message(f"Error loading data: {str(e)}", level='error')
        raise

def train_single_model(X_train, y_train, X_val, y_val, feature_names, scaler, user_id):
    """Train a single model for a user with XGBoost."""
    try:
        start_time = time.time()
        params = {
            'objective': 'binary:logistic',
            'eval_metric': ['auc'],
            'max_depth': 4,
            'learning_rate': 0.05,
            'n_estimators': 200,
            'subsample': 0.7,
            'colsample_bytree': 0.7,
            'min_child_weight': 3,
            'gamma': 1,
            'reg_alpha': 0.1,
            'reg_lambda': 1,
            'n_jobs': max(1, os.cpu_count()-1),
            'tree_method': 'hist',
            'verbosity': 1,
            'early_stopping_rounds': 20  # 将early_stopping_rounds移到params中
        }
        model = xgb.XGBClassifier(**params)
        
        # 只在验证集上评估模型
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=True
        )
        
        # 使用最佳迭代次数进行预测
        y_pred = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, y_pred)
        
        # 记录训练信息
        training_time = time.time() - start_time
        importance = dict(zip(feature_names, model.feature_importances_))
        
        # 记录特征重要性
        feature_importance = pd.DataFrame({
            'feature': feature_names,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        log_message(f"\nTop 10 important features for user {user_id}:")
        for _, row in feature_importance.head(10).iterrows():
            log_message(f"{row['feature']}: {row['importance']:.4f}")
        
        # 准备特征和编码器
        X_train_processed, X_val_processed, y_train, scaler, selected_features, encoders = prepare_features(
            X_train, X_val, y_train, data_analysis=False
        )
        
        return {
            'user_id': user_id,
            'model': model,
            'metrics': {'auc': auc},
            'importance': importance,
            'training_time': training_time,
            'scaler': scaler,
            'feature_names': feature_names,
            'best_iteration': model.best_iteration,
            'encoders': encoders
        }
    except Exception as e:
        log_message(f"Error training model for user {user_id}: {str(e)}", level='error')
        return None

def save_models(results, performance_metrics):
    """保存模型和结果，results为每个用户的dict列表"""
    try:
        os.makedirs('models', exist_ok=True)
        os.makedirs('results', exist_ok=True)
        for r in results:
            user_id = r['user_id']
            model = r['model']
            scaler = r['scaler']
            feature_names = r['feature_names']
            encoders = r.get('encoders')  # 获取编码器，如果不存在则为None
            
            model_path = f'models/user_{user_id}_model.pkl'
            scaler_path = f'models/user_{user_id}_scaler.pkl'
            feature_path = f'models/user_{user_id}_features.pkl'
            encoders_path = f'models/user_{user_id}_encoders.pkl'
            
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            with open(feature_path, 'wb') as f:
                pickle.dump(feature_names, f)
            if encoders is not None:  # 如果存在编码器，则保存
                with open(encoders_path, 'wb') as f:
                    pickle.dump(encoders, f)
            log_message(f"Saved model for user {user_id}")
        metrics_path = 'results/performance_metrics.pkl'
        with open(metrics_path, 'wb') as f:
            pickle.dump(performance_metrics, f)
        log_message("Successfully saved all models and results")
    except Exception as e:
        log_message(f"Error saving models and results: {str(e)}", level='error')
        raise

def validate_features(features: Dict[str, Any]) -> bool:
    """验证特征数据的有效性"""
    try:
        # 确保所有特征都是数值类型
        for key, value in features.items():
            if key == 'user_id':
                continue
            if not isinstance(value, (int, float, np.number)):
                try:
                    features[key] = float(value)
                except (ValueError, TypeError):
                    logger.error(f"Invalid value type for feature {key}: {value}")
                    return False
        
        # 检查必要特征是否存在
        required_features = [
            'total_requests', 'avg_response_time', 'error_rate',
            'unique_ips', 'request_frequency', 'data_volume'
        ]
        for feature in required_features:
            if feature not in features:
                logger.error(f"Missing required feature: {feature}")
                return False
        
        # 检查数值范围
        if not (0 <= features['error_rate'] <= 1):
            logger.error(f"Invalid error_rate value: {features['error_rate']}")
            return False
        
        if features['total_requests'] < 0:
            logger.error(f"Invalid total_requests value: {features['total_requests']}")
            return False
        
        if features['avg_response_time'] < 0:
            logger.error(f"Invalid avg_response_time value: {features['avg_response_time']}")
            return False
        
        if features['unique_ips'] < 0:
            logger.error(f"Invalid unique_ips value: {features['unique_ips']}")
            return False
        
        if features['request_frequency'] < 0:
            logger.error(f"Invalid request_frequency value: {features['request_frequency']}")
            return False
        
        if features['data_volume'] < 0:
            logger.error(f"Invalid data_volume value: {features['data_volume']}")
            return False
        
        # 检查是否有 NaN 值
        for key, value in features.items():
            if key != 'user_id' and (np.isnan(value) if isinstance(value, (float, np.number)) else False):
                logger.error(f"NaN value found in feature {key}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error in data validation: {str(e)}")
        return False

def validate_data(data: pd.DataFrame, user_id: int) -> bool:
    """验证数据是否有效"""
    try:
        # 确保数据是DataFrame类型
        if not isinstance(data, pd.DataFrame):
            logger.error(f"Data for user {user_id} is not a DataFrame")
            return False
            
        # 检查数据是否为空
        if data.empty:
            logger.error(f"Empty data for user {user_id}")
            return False
            
        # 检查必要的列是否存在
        required_columns = ['user', 'session']  # 只检查最基本的必要列
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            logger.error(f"Missing required columns for user {user_id}: {missing_columns}")
            return False
            
        # 确保数值列的类型正确
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            try:
                data[col] = pd.to_numeric(data[col], errors='coerce')
                # 替换无穷值
                data[col] = data[col].replace([np.inf, -np.inf], np.nan)
                # 填充缺失值
                data[col] = data[col].fillna(0)
            except Exception as e:
                logger.error(f"Error converting column {col} to numeric for user {user_id}: {str(e)}")
                return False
        
        # 检查数值列中的NaN值
        for col in numeric_columns:
            try:
                nan_count = data[col].isna().sum()
                if nan_count > 0:
                    logger.warning(f"Found {nan_count} NaN values in column {col} for user {user_id}")
                    # 用中位数填充NaN值
                    data[col] = data[col].fillna(data[col].median())
            except Exception as e:
                logger.error(f"Error checking NaN values in column {col} for user {user_id}: {str(e)}")
                return False
        
        # 检查时间戳列（如果存在）
        if 'timestamp' in data.columns:
            try:
                data['timestamp'] = pd.to_datetime(data['timestamp'])
            except Exception as e:
                logger.error(f"Error converting timestamp column for user {user_id}: {str(e)}")
                return False
            
        # 检查分类列（如果存在）
        categorical_columns = ['event_type', 'device_type', 'location']
        for col in categorical_columns:
            if col in data.columns:
                try:
                    # 将分类列转换为字符串类型
                    data[col] = data[col].astype(str)
                    # 检查是否有空值
                    if data[col].isna().any():
                        logger.warning(f"Found NaN values in column {col} for user {user_id}")
                        # 用最常见的值填充NaN
                        data[col] = data[col].fillna(data[col].mode()[0])
                except Exception as e:
                    logger.error(f"Error processing categorical column {col} for user {user_id}: {str(e)}")
                    return False
        
        # 检查数据范围（如果存在相关列）
        if 'duration' in data.columns:
            if (data['duration'] < 0).any():
                logger.warning(f"Found negative duration values for user {user_id}")
                data['duration'] = data['duration'].clip(lower=0)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in data validation for user {user_id}: {str(e)}")
        return False

def check_X_safe(X, user_id, stage):
    # 检查inf
    if np.isinf(X.values).any():
        bad_cols = X.columns[np.isinf(X).any()].tolist()
        log_message(f"User {user_id} {stage}: inf detected in columns: {bad_cols}", level='error')
    # 检查nan
    if np.isnan(X.values).any():
        bad_cols = X.columns[np.isnan(X).any()].tolist()
        log_message(f"User {user_id} {stage}: nan detected in columns: {bad_cols}", level='error')
    # 检查极端大值
    if (np.abs(X.values) > 1e12).any():
        bad_cols = X.columns[(np.abs(X) > 1e12).any()].tolist()
        log_message(f"User {user_id} {stage}: extreme value detected in columns: {bad_cols}", level='error')
    # 彻底清理
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0).clip(-1e6, 1e6)
    return X

def load_data(filepath=None):
    """加载数据 - 兼容性函数"""
    try:
        log_message("Loading data...")
        
        # 使用提供的文件路径或默认路径
        data_path = filepath if filepath else DATA_PATH
        
        # 检查数据文件是否存在
        if not os.path.exists(data_path):
            log_message(f"Data file not found: {data_path}", level='error')
            return None, None, None
        
        # 根据文件类型加载数据
        if data_path.endswith('.csv'):
            # 加载CSV文件
            data = pd.read_csv(data_path)
            log_message(f"CSV data loaded successfully: {len(data)} records")
        elif data_path.endswith('.pickle') or data_path.endswith('.pkl'):
            # 加载pickle文件
            with open(data_path, 'rb') as f:
                loaded_data = pickle.load(f)
            
            # 确保返回的是DataFrame
            if isinstance(loaded_data, pd.DataFrame):
                data = loaded_data
            elif isinstance(loaded_data, dict):
                # 如果是字典，尝试转换为DataFrame
                data = pd.DataFrame(loaded_data)
            else:
                # 其他类型，尝试转换为DataFrame
                data = pd.DataFrame(loaded_data)
            
            log_message(f"Pickle data loaded successfully: {len(data)} records")
        else:
            log_message(f"Unsupported file format: {data_path}", level='error')
            return None, None, None
        
        # 确保返回的是DataFrame
        if not isinstance(data, pd.DataFrame):
            log_message("Converting data to DataFrame...")
            data = pd.DataFrame(data)
        
        log_message(f"Final data shape: {data.shape}")
        return data, None, None
        
    except Exception as e:
        log_message(f"Error loading data: {str(e)}", level='error')
        return None, None, None

def preprocess_data(data):
    """预处理数据 - 兼容性函数"""
    try:
        log_message("Preprocessing data...")
        
        if data is None:
            log_message("No data to preprocess", level='error')
            return None, None, None
        
        log_message(f"Input data type: {type(data)}")
        log_message(f"Input data shape: {data.shape if hasattr(data, 'shape') else 'unknown'}")
        
        # 基本预处理
        if isinstance(data, pd.DataFrame):
            log_message("Data is DataFrame, proceeding with preprocessing...")
            
            # 处理缺失值
            data = data.fillna(0)
            log_message("Missing values filled")
            
            # 移除重复行
            original_len = len(data)
            data = data.drop_duplicates()
            log_message(f"Removed {original_len - len(data)} duplicate rows")
            
            # 分离特征和标签
            if 'label' in data.columns:
                log_message("Found 'label' column, separating features and labels...")
                X = data.drop('label', axis=1)
                y = data['label']
            else:
                log_message("No 'label' column found, creating dummy labels...")
                # 如果没有标签列，创建一个虚拟标签（用于无监督学习）
                X = data
                y = np.zeros(len(data))  # 创建虚拟标签
            
            # 确保所有特征都是数值型
            numeric_cols = X.select_dtypes(include=[np.number]).columns
            log_message(f"Found {len(numeric_cols)} numeric columns out of {len(X.columns)} total columns")
            
            if len(numeric_cols) == 0:
                log_message("No numeric columns found, attempting to convert...", level='error')
                # 尝试转换非数值列为数值
                for col in X.columns:
                    try:
                        X[col] = pd.to_numeric(X[col], errors='coerce')
                    except:
                        X[col] = 0
                numeric_cols = X.select_dtypes(include=[np.number]).columns
            
            X = X[numeric_cols]
            
            # 数据清理和验证
            log_message("Cleaning and validating data...")
            
            # 处理无穷大值
            if np.isinf(X.values).any():
                log_message("Found infinite values, replacing with 0")
                X = X.replace([np.inf, -np.inf], 0)
            
            # 处理NaN值
            if X.isnull().any().any():
                log_message("Found NaN values, filling with 0")
                X = X.fillna(0)
            
            # 检查并处理异常值
            for col in X.columns:
                col_data = X[col]
                if col_data.dtype in ['float64', 'float32']:
                    # 计算分位数
                    q99 = col_data.quantile(0.99)
                    q01 = col_data.quantile(0.01)
                    
                    # 如果存在极端值，进行裁剪
                    if q99 > 1e6 or q01 < -1e6:
                        log_message(f"Column {col} has extreme values, clipping to reasonable range")
                        X[col] = np.clip(X[col], -1e6, 1e6)
                    
                    # 检查是否有无穷大值
                    if np.isinf(col_data.values).any():
                        log_message(f"Column {col} has infinite values, replacing with 0")
                        X[col] = col_data.replace([np.inf, -np.inf], 0)
            
            # 最终验证
            X = X.astype(float)
            X = X.replace([np.inf, -np.inf], 0)
            X = X.fillna(0)
            
            log_message(f"Data preprocessed: {len(X)} records, {len(X.columns)} features")
            log_message(f"Feature columns: {list(X.columns)}")
            log_message(f"Data range: {X.min().min():.2f} to {X.max().max():.2f}")
            
            return X, y, None
        else:
            log_message(f"Data is not a DataFrame, type: {type(data)}", level='error')
            # 尝试转换为DataFrame
            try:
                data = pd.DataFrame(data)
                log_message("Successfully converted to DataFrame, retrying preprocessing...")
                return preprocess_data(data)
            except Exception as e:
                log_message(f"Failed to convert to DataFrame: {str(e)}", level='error')
                return None, None, None
            
    except Exception as e:
        log_message(f"Error preprocessing data: {str(e)}", level='error')
        import traceback
        log_message(f"Traceback: {traceback.format_exc()}", level='error')
        return None, None, None

def train_model(X_train, y_train, X_val=None, y_val=None, **kwargs):
    """训练模型 - 兼容性函数"""
    try:
        log_message("Training model...")
        
        # 数据清理和验证
        log_message("Cleaning training data...")
        
        # 检查并处理无穷大值
        if np.isinf(X_train.values).any():
            log_message("Found infinite values in training data, replacing with 0")
            X_train = X_train.replace([np.inf, -np.inf], 0)
        
        # 检查并处理NaN值
        if X_train.isnull().any().any():
            log_message("Found NaN values in training data, filling with 0")
            X_train = X_train.fillna(0)
        
        # 检查数据范围
        for col in X_train.columns:
            col_data = X_train[col]
            if col_data.dtype in ['float64', 'float32']:
                # 对于浮点数列，检查异常值
                q99 = col_data.quantile(0.99)
                q01 = col_data.quantile(0.01)
                if q99 > 1e6 or q01 < -1e6:
                    log_message(f"Column {col} has extreme values, clipping to reasonable range")
                    X_train[col] = np.clip(X_train[col], -1e6, 1e6)
        
        # 确保所有值都是有限的
        X_train = X_train.astype(float)
        X_train = X_train.replace([np.inf, -np.inf], 0)
        X_train = X_train.fillna(0)
        
        log_message(f"Training data shape: {X_train.shape}")
        log_message(f"Training data range: {X_train.min().min():.2f} to {X_train.max().max():.2f}")
        
        # 使用XGBoost作为默认模型，设置missing参数
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            missing=0,  # 设置缺失值处理
            **kwargs
        )
        
        # 训练模型
        model.fit(X_train, y_train)
        
        log_message("Model training completed")
        return model
        
    except Exception as e:
        log_message(f"Error training model: {str(e)}", level='error')
        import traceback
        log_message(f"Traceback: {traceback.format_exc()}", level='error')
        return None

def save_model(model, filepath):
    """保存模型 - 兼容性函数"""
    try:
        log_message(f"Saving model to {filepath}...")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 保存模型
        with open(filepath, 'wb') as f:
            pickle.dump(model, f)
        
        log_message("Model saved successfully")
        return True
        
    except Exception as e:
        log_message(f"Error saving model: {str(e)}", level='error')
        return False

def main():
    """Main function to train models for all users."""
    try:
        # 设置日志记录
        logger = setup_logging()
        log_message("Starting main training process...")
        start_time = time.time()
        log_message("Loading and preprocessing data...")
        processed_user_data = load_and_split_data()
        total_users = len(processed_user_data)
        log_message(f"Data loaded and preprocessed for {total_users} users")

        results = []
        successful_training = 0
        failed_training = 0
        log_message("\n" + "="*50)
        log_message("Starting model training for all users")
        log_message("="*50)

        for i, (user_id, data) in enumerate(processed_user_data.items(), 1):
            log_message(f"\nProcessing user {user_id} ({i}/{total_users})")
            log_message("-"*30)
            try:
                # 特征工程+特征选择+缩放
                X_train, X_val = data['X_train'], data['X_val']
                y_train, y_val = data['y_train'], data['y_val']
                
                # 先处理异常值
                X_train = X_train.replace([np.inf, -np.inf], 0)
                X_val = X_val.replace([np.inf, -np.inf], 0)
                
                # 方差阈值特征选择
                selector = VarianceThreshold(threshold=0.01)
                X_train_sel = selector.fit_transform(X_train)
                X_val_sel = selector.transform(X_val)
                feature_names = X_train.columns[selector.get_support()].tolist()
                
                # 标准化
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train_sel)
                X_val_scaled = scaler.transform(X_val_sel)
                
                # 转为DataFrame
                X_train_final = pd.DataFrame(X_train_scaled, columns=feature_names)
                X_val_final = pd.DataFrame(X_val_scaled, columns=feature_names)
                
                # 再次确保没有异常值
                X_train_final = X_train_final.replace([np.inf, -np.inf], 0)
                X_val_final = X_val_final.replace([np.inf, -np.inf], 0)
                
                # 训练模型
                result = train_single_model(
                    X_train_final, y_train.reset_index(drop=True),
                    X_val_final, y_val.reset_index(drop=True),
                    feature_names, scaler, user_id
                )
                if result is not None:
                    results.append(result)
                    successful_training += 1
                    log_message(f"✓ Successfully trained model for user {user_id}")
                    metrics = result['metrics']
                    log_message("Model performance:")
                    for metric, value in metrics.items():
                        log_message(f"  - {metric.upper()}: {value:.4f}")
                else:
                    failed_training += 1
                    log_message(f"✗ Training failed for user {user_id}", level='error')
            except Exception as e:
                failed_training += 1
                log_message(f"✗ Error training model for user {user_id}: {str(e)}", level='error')
                continue
            progress = (i / total_users) * 100
            log_message(f"\nOverall progress: {progress:.1f}%")
            log_message(f"Successful: {successful_training}, Failed: {failed_training}")
            if i % 5 == 0:
                gc.collect()
                log_message("Garbage collection completed")
        log_message("\n" + "="*50)
        log_message("Training Summary")
        log_message("="*50)
        log_message(f"Total users processed: {total_users}")
        log_message(f"Successfully trained: {successful_training}")
        log_message(f"Failed training: {failed_training}")
        log_message(f"Success rate: {(successful_training/total_users)*100:.1f}%")
        if not results:
            raise ValueError("No models were successfully trained")
        log_message("\nSaving models and results...")
        try:
            performance_metrics = {
                r['user_id']: {
                    'auc': r['metrics']['auc'],
                    'training_time': r['training_time']
                } for r in results
            }
            save_models(results, performance_metrics)
            log_message("✓ Models and results saved successfully")
        except Exception as e:
            log_message(f"✗ Error saving models and results: {str(e)}", level='error')
            raise
        total_time = time.time() - start_time
        log_message(f"\nTotal training time: {total_time:.2f} seconds")
        log_message(f"Average time per user: {total_time/total_users:.2f} seconds")
    except Exception as e:
        log_message(f"✗ Error in main training process: {str(e)}", level='error')
        raise
    finally:
        gc.collect()
        log_message("Garbage collection completed")

if __name__ == "__main__":
    main() 