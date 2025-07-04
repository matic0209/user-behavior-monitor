import pandas as pd
import numpy as np
import sqlite3
import json
import pickle
import time
from datetime import datetime
from pathlib import Path
import sys
import os

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader

# 直接导入classification模块
try:
    from src.classification import (
        load_data, preprocess_data, train_model, evaluate_model, save_model
    )
    CLASSIFICATION_AVAILABLE = True
except ImportError:
    CLASSIFICATION_AVAILABLE = False
    print("警告: 无法导入classification模块")

class SimpleModelTrainer:
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigLoader()
        self.db_path = Path(self.config.get_paths()['data']) / 'mouse_data.db'
        self.models_path = Path(self.config.get_paths()['models'])
        self.models_path.mkdir(parents=True, exist_ok=True)
        
        if not CLASSIFICATION_AVAILABLE:
            self.logger.error("classification模块不可用，模型训练功能受限")
        
        self.logger.info("简单模型训练器初始化完成")

    def load_user_features_from_db(self, user_id):
        """从数据库加载用户特征数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT feature_vector FROM features 
                WHERE user_id = ?
                ORDER BY timestamp DESC
            '''
            
            df = pd.read_sql_query(query, conn, params=(user_id,))
            conn.close()
            
            if not df.empty:
                # 解析特征向量
                df = self._parse_feature_vectors(df)
            
            self.logger.info(f"从数据库加载了用户 {user_id} 的 {len(df)} 条特征数据")
            return df
            
        except Exception as e:
            self.logger.error(f"从数据库加载用户特征数据失败: {str(e)}")
            return pd.DataFrame()

    def load_training_data_as_negative_samples(self, exclude_user_id, limit=None):
        """从数据库加载训练数据作为负样本"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT feature_vector FROM features 
                WHERE user_id LIKE 'training_user%' OR user_id LIKE 'test_user%'
                ORDER BY timestamp DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            df = pd.read_sql_query(query, conn, params=())
            conn.close()
            
            if not df.empty:
                # 解析特征向量
                df = self._parse_feature_vectors(df)
            
            self.logger.info(f"从数据库加载了 {len(df)} 条训练数据作为负样本")
            return df
            
        except Exception as e:
            self.logger.error(f"从数据库加载训练数据失败: {str(e)}")
            return pd.DataFrame()

    def load_other_users_features_from_db(self, exclude_user_id, limit=None):
        """从数据库加载其他用户的特征数据作为负样本（备用方案）"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT feature_vector FROM features 
                WHERE user_id != ? AND user_id NOT LIKE 'training_user%' AND user_id NOT LIKE 'test_user%'
                ORDER BY timestamp DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            df = pd.read_sql_query(query, conn, params=(exclude_user_id,))
            conn.close()
            
            if not df.empty:
                # 解析特征向量
                df = self._parse_feature_vectors(df)
            
            self.logger.info(f"从数据库加载了 {len(df)} 条其他用户特征数据作为负样本")
            return df
            
        except Exception as e:
            self.logger.error(f"从数据库加载其他用户特征数据失败: {str(e)}")
            return pd.DataFrame()

    def _parse_feature_vectors(self, df):
        """解析特征向量JSON字符串"""
        try:
            # 解析feature_vector列
            if 'feature_vector' in df.columns:
                feature_vectors = []
                for vector_str in df['feature_vector']:
                    try:
                        if isinstance(vector_str, str):
                            vector_dict = json.loads(vector_str)
                        else:
                            vector_dict = vector_str
                        feature_vectors.append(vector_dict)
                    except:
                        feature_vectors.append({})
                
                # 将特征向量转换为DataFrame
                feature_df = pd.DataFrame(feature_vectors)
                
                # 合并到原始DataFrame
                df = pd.concat([df.drop('feature_vector', axis=1), feature_df], axis=1)
            
            return df
            
        except Exception as e:
            self.logger.error(f"解析特征向量失败: {str(e)}")
            return df

    def _align_features(self, features_df, target_features=None):
        """对齐特征列，确保与训练数据一致"""
        try:
            if target_features is None:
                # 如果没有指定目标特征，从训练数据中获取
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT feature_vector FROM features 
                    WHERE user_id LIKE 'training_user%' 
                    LIMIT 1
                ''')
                
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    # 解析一个训练数据样本来获取特征列
                    sample_features = json.loads(result[0])
                    target_features = list(sample_features.keys())
                else:
                    self.logger.warning("没有找到训练数据样本，无法对齐特征")
                    return features_df
            
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

    def prepare_training_data(self, user_id, negative_sample_limit=1000):
        """准备训练数据：当前用户作为正样本，训练数据作为负样本"""
        try:
            self.logger.info(f"开始准备用户 {user_id} 的训练数据")
            
            # 1. 加载当前用户特征作为正样本
            positive_samples = self.load_user_features_from_db(user_id)
            if positive_samples.empty:
                self.logger.error(f"用户 {user_id} 没有特征数据")
                return None, None, None
            
            # 2. 优先加载训练数据作为负样本
            negative_samples = self.load_training_data_as_negative_samples(user_id, negative_sample_limit)
            
            # 3. 如果训练数据不够，补充其他用户数据
            if len(negative_samples) < negative_sample_limit // 2:
                additional_samples = self.load_other_users_features_from_db(user_id, negative_sample_limit - len(negative_samples))
                if not additional_samples.empty:
                    negative_samples = pd.concat([negative_samples, additional_samples], ignore_index=True)
                    self.logger.info(f"补充了 {len(additional_samples)} 条其他用户数据")
            
            # 4. 特征对齐
            if not negative_samples.empty:
                # 使用训练数据的特征作为标准
                aligned_positive = self._align_features(positive_samples, negative_samples.columns)
                aligned_negative = self._align_features(negative_samples, negative_samples.columns)
                combined_data = pd.concat([aligned_positive, aligned_negative], ignore_index=True)
            else:
                combined_data = positive_samples
                self.logger.warning("没有负样本数据")
            
            # 5. 准备特征和标签
            # 选择数值特征列
            numeric_cols = combined_data.select_dtypes(include=[np.number]).columns
            feature_cols = [col for col in numeric_cols if col not in [
                'id', 'timestamp', 'user_id', 'session_id'
            ]]
            
            if len(feature_cols) == 0:
                self.logger.error("没有找到有效的特征列")
                return None, None, None
            
            # 准备特征矩阵
            X = combined_data[feature_cols].fillna(0)
            
            # 创建标签：当前用户为1（正常），负样本为0（异常）
            y = np.ones(len(combined_data))
            y[len(aligned_positive):] = 0  # 负样本标记为异常
            
            # 6. 数据统计
            positive_count = len(aligned_positive)
            negative_count = len(aligned_negative) if not negative_samples.empty else 0
            
            self.logger.info(f"训练数据统计:")
            self.logger.info(f"  正样本（用户 {user_id}）: {positive_count}")
            self.logger.info(f"  负样本（训练数据）: {negative_count}")
            self.logger.info(f"  总计: {len(X)} 个样本, {len(feature_cols)} 个特征")
            
            return X, y, feature_cols
            
        except Exception as e:
            self.logger.error(f"准备训练数据失败: {str(e)}")
            return None, None, None

    def train_user_model(self, user_id):
        """训练用户模型"""
        self.logger.info(f"开始训练用户 {user_id} 的模型")
        
        # 1. 准备训练数据
        X, y, feature_cols = self.prepare_training_data(user_id)
        if X is None:
            self.logger.error(f"用户 {user_id} 训练数据准备失败")
            return False
        
        # 2. 使用classification模块训练模型
        return self._train_with_classification_module(X, y, user_id, feature_cols)

    def _train_with_classification_module(self, X, y, user_id, feature_cols):
        """使用classification模块训练模型"""
        try:
            self.logger.info("使用classification模块训练模型")
            
            # 创建临时数据文件
            temp_data_path = self.models_path / f"temp_data_{user_id}.csv"
            
            # 准备数据
            data_df = X.copy()
            data_df['label'] = y
            data_df.to_csv(temp_data_path, index=False)
            
            # 使用classification模块的函数
            data = load_data(str(temp_data_path))
            X_processed, y_processed = preprocess_data(data)
            
            # 训练模型
            model = train_model(X_processed, y_processed)
            
            # 评估模型
            accuracy = evaluate_model(model, X_processed, y_processed)
            self.logger.info(f"模型准确率: {accuracy:.4f}")
            
            # 保存模型
            model_path = self.models_path / f"user_{user_id}_model.pkl"
            save_model(model, str(model_path))
            
            # 保存特征列信息
            feature_info_path = self.models_path / f"user_{user_id}_features.json"
            with open(feature_info_path, 'w') as f:
                json.dump({
                    'feature_cols': feature_cols.tolist(),
                    'n_features': len(feature_cols),
                    'training_samples': len(X),
                    'accuracy': accuracy,
                    'trained_at': datetime.now().isoformat(),
                    'model_type': 'simple_classification'
                }, f, indent=2)
            
            # 清理临时文件
            temp_data_path.unlink(missing_ok=True)
            
            self.logger.info(f"用户 {user_id} 模型训练完成，保存到 {model_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"使用classification模块训练失败: {str(e)}")
            return False

    def load_user_model(self, user_id):
        """加载用户模型"""
        try:
            model_path = self.models_path / f"user_{user_id}_model.pkl"
            feature_info_path = self.models_path / f"user_{user_id}_features.json"
            
            if not model_path.exists():
                self.logger.error(f"用户 {user_id} 的模型文件不存在")
                return None, None, None
            
            # 加载模型
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            # 加载特征信息
            feature_cols = None
            if feature_info_path.exists():
                with open(feature_info_path, 'r') as f:
                    feature_info = json.load(f)
                    feature_cols = feature_info.get('feature_cols', [])
            
            self.logger.info(f"成功加载用户 {user_id} 的模型")
            return model, None, feature_cols  # 返回None作为scaler，因为classification模块可能不需要
            
        except Exception as e:
            self.logger.error(f"加载用户 {user_id} 模型失败: {str(e)}")
            return None, None, None

    def predict_user_behavior(self, user_id, features):
        """预测用户行为"""
        try:
            # 加载模型
            model, scaler, feature_cols = self.load_user_model(user_id)
            if model is None:
                return None
            
            # 准备特征
            if feature_cols:
                # 确保特征列匹配
                available_features = [col for col in feature_cols if col in features.columns]
                if len(available_features) != len(feature_cols):
                    self.logger.warning(f"特征列不匹配: 期望 {len(feature_cols)}, 实际 {len(available_features)}")
                
                X = features[available_features].fillna(0)
            else:
                # 如果没有特征列信息，使用所有数值列
                numeric_cols = features.select_dtypes(include=[np.number]).columns
                X = features[numeric_cols].fillna(0)
            
            # 预测
            predictions = model.predict(X)
            probabilities = model.predict_proba(X)
            
            # 返回结果
            results = []
            for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
                results.append({
                    'prediction': int(pred),
                    'probability': float(prob[1] if len(prob) > 1 else prob[0]),
                    'is_normal': bool(pred == 1),
                    'anomaly_score': float(1 - prob[1] if len(prob) > 1 else 1 - prob[0])
                })
            
            self.logger.info(f"用户 {user_id} 行为预测完成: {len(results)} 个预测结果")
            return results
            
        except Exception as e:
            self.logger.error(f"预测用户 {user_id} 行为失败: {str(e)}")
            return None

    def retrain_all_models(self):
        """重新训练所有用户的模型"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取所有用户
            cursor.execute('SELECT DISTINCT user_id FROM features')
            users = cursor.fetchall()
            conn.close()
            
            self.logger.info(f"开始重新训练 {len(users)} 个用户的模型")
            
            success_count = 0
            for (user_id,) in users:
                if self.train_user_model(user_id):
                    success_count += 1
            
            self.logger.info(f"模型重新训练完成: {success_count}/{len(users)} 个用户成功")
            return success_count
            
        except Exception as e:
            self.logger.error(f"重新训练所有模型失败: {str(e)}")
            return 0 