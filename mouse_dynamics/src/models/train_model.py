import numpy as np
import pandas as pd
import os
import logging
import yaml
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, StratifiedKFold
import xgboost as xgb
from sklearn.metrics import roc_auc_score, precision_recall_curve, average_precision_score
import matplotlib.pyplot as plt
import optuna
from optuna.visualization import plot_optimization_history, plot_param_importances
from typing import Dict, Tuple, List
from tqdm import tqdm
import seaborn as sns
from datetime import datetime
from pathlib import Path
from mouse_dynamics.src.features.feature_engineering import FeatureEngineering

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.data.feature_engineering import FeatureExtractor

class ModelTrainer:
    def __init__(self, config_path: str = "mouse_dynamics/configs/config.yaml"):
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.feature_engineering = FeatureEngineering()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path(self.config['paths']['log_dir'])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 初始化模型和scaler
        self.model = xgb.XGBClassifier(**self.config['model']['params'])
        self.scaler = StandardScaler()
        
        # 创建必要的目录
        os.makedirs(self.config['model']['save_dir'], exist_ok=True)
        os.makedirs(self.config['model']['feature_importance_dir'], exist_ok=True)
        os.makedirs(self.config['data']['predictions_dir'], exist_ok=True)
        
        self.feature_extractor = FeatureExtractor(self.config)
        
    def _load_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """加载训练数据"""
        self.logger.info("开始加载训练数据...")
        
        # 加载训练文件
        train_files = self.config['data']['training_files']
        train_data = []
        
        for file in tqdm(train_files, desc="加载训练文件"):
            try:
                df = pd.read_csv(file)
                train_data.append(df)
            except Exception as e:
                self.logger.error(f"加载文件 {file} 失败: {str(e)}")
                continue
        
        if not train_data:
            raise ValueError("没有成功加载任何训练数据")
        
        train_df = pd.concat(train_data, ignore_index=True)
        self.logger.info(f"成功加载训练数据，共 {len(train_df)} 条记录")
        
        # 加载标签
        labels_file = self.config['data']['public_labels']
        try:
            labels_df = pd.read_csv(labels_file)
            labels = labels_df['label'].values
            self.logger.info(f"成功加载标签数据，共 {len(labels)} 条记录")
        except Exception as e:
            self.logger.error(f"加载标签文件失败: {str(e)}")
            raise
        
        return train_df, labels
    
    def _prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """准备特征"""
        self.logger.info("开始特征工程...")
        features = self.feature_engineering.extract_features(data)
        self.logger.info(f"特征工程完成，特征维度: {features.shape}")
        return features
    
    def _evaluate_model(self, model: xgb.XGBClassifier, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """评估模型性能"""
        y_pred = model.predict(X)
        return {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, average='weighted'),
            'recall': recall_score(y, y_pred, average='weighted'),
            'f1': f1_score(y, y_pred, average='weighted')
        }
    
    def train(self):
        """训练模型"""
        try:
            # 加载数据
            train_df, labels = self._load_data()
            
            # 特征工程
            features = self._prepare_features(train_df)
            
            # 准备训练数据
            X = features
            y = labels
            
            # 设置模型参数
            model_params = self.config['model']['params']
            self.logger.info(f"模型参数: {model_params}")
            
            # 创建模型
            model = xgb.XGBClassifier(**model_params)
            
            # 训练模型
            self.logger.info("开始训练模型...")
            model.fit(
                X, y,
                eval_set=[(X, y)],
                eval_metric='mlogloss',
                verbose=True
            )
            
            # 评估模型
            metrics = self._evaluate_model(model, X, y)
            self.logger.info("模型评估结果:")
            for metric_name, value in metrics.items():
                self.logger.info(f"{metric_name}: {value:.4f}")
            
            # 保存模型
            model_dir = Path(self.config['paths']['model_dir'])
            model_dir.mkdir(parents=True, exist_ok=True)
            model_path = model_dir / f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
            joblib.dump(model, model_path)
            self.logger.info(f"模型已保存到: {model_path}")
            
            return model, metrics
            
        except Exception as e:
            self.logger.error(f"训练过程出错: {str(e)}")
            raise

def main():
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join('logs', 'training.log')),
            logging.StreamHandler()
        ]
    )
    
    try:
        # 训练模型
        trainer = ModelTrainer()
        model, metrics = trainer.train()
    except Exception as e:
        trainer.logger.error(f"An error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 