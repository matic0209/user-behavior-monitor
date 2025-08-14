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

# 仅在导入错误时才回退到mock；其他错误直接抛出，避免误用mock
try:
    from src.classification import (
        load_data, preprocess_data, train_model, evaluate_model, save_model
    )
    CLASSIFICATION_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"警告: 未找到真实classification依赖，将回退到模拟版: {e}")
    from src.classification_mock import (
        load_data, preprocess_data, train_model, evaluate_model, save_model
    )
    CLASSIFICATION_AVAILABLE = False

class SimpleModelTrainer:
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigLoader()
        paths_config = self.config.get_paths()
        # 优先使用显式的 database 路径，避免工作目录差异导致的相对路径指向错误数据库
        if 'database' in paths_config and paths_config['database']:
            self.db_path = Path(paths_config['database'])
        else:
            self.db_path = Path(paths_config['data']) / 'mouse_data.db'
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
        """从数据库加载其他用户的特征数据作为负样本"""
        try:
            self.logger.info(f"开始加载其他用户特征数据，排除用户: {exclude_user_id}")
            self.logger.info(f"数据库路径: {Path(self.db_path).resolve()}")
            
            conn = sqlite3.connect(self.db_path)
            self.logger.info("数据库连接成功")
            
            # 优先加载其他非当前用户的数据作为负样本
            query = '''
                SELECT feature_vector FROM features 
                WHERE TRIM(user_id) != TRIM(?)
                ORDER BY timestamp DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            self.logger.info(f"执行查询: {query}")
            self.logger.info(f"查询参数: {exclude_user_id}")
            
            df = pd.read_sql_query(query, conn, params=(exclude_user_id,))
            self.logger.info(f"查询结果: {len(df)} 条记录")
            
            conn.close()
            self.logger.info("数据库连接已关闭")
            
            if not df.empty:
                self.logger.info("开始解析特征向量...")
                # 解析特征向量
                df = self._parse_feature_vectors(df)
                self.logger.info(f"特征向量解析完成，最终形状: {df.shape}")
            else:
                self.logger.warning("查询结果为空，没有其他用户数据")
            
            self.logger.info(f"从数据库加载了 {len(df)} 条其他用户特征数据作为负样本")
            return df
            
        except Exception as e:
            self.logger.error(f"从数据库加载其他用户特征数据失败: {str(e)}")
            import traceback
            self.logger.error(f"异常详情: {traceback.format_exc()}")
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
        """准备训练数据：当前用户作为正样本，其他用户作为负样本"""
        try:
            self.logger.info(f"开始准备用户 {user_id} 的训练数据")
            
            # 1. 加载当前用户特征作为正样本
            positive_samples = self.load_user_features_from_db(user_id)
            if positive_samples.empty:
                self.logger.error(f"用户 {user_id} 没有特征数据")
                return None, None, None
            
            # 2. 优先加载其他用户数据作为负样本（正确的做法）
            negative_samples = self.load_other_users_features_from_db(user_id, negative_sample_limit)
            
            # 3. 如果其他用户数据不够，补充训练数据作为备用负样本
            if len(negative_samples) < negative_sample_limit // 2:
                additional_samples = self.load_training_data_as_negative_samples(user_id, negative_sample_limit - len(negative_samples))
                if not additional_samples.empty:
                    negative_samples = pd.concat([negative_samples, additional_samples], ignore_index=True)
                    self.logger.info(f"补充了 {len(additional_samples)} 条训练数据作为备用负样本")
            
            # 4. 特征对齐
            if not negative_samples.empty:
                # 使用训练数据的特征作为标准
                aligned_positive = self._align_features(positive_samples, negative_samples.columns)
                aligned_negative = self._align_features(negative_samples, negative_samples.columns)
                combined_data = pd.concat([aligned_positive, aligned_negative], ignore_index=True)
            else:
                # 如果没有负样本，只使用正样本进行训练
                combined_data = positive_samples
                self.logger.warning("没有负样本数据，将使用单类分类")
                # 创建虚拟负样本（通过添加噪声）
                aligned_positive = positive_samples.copy()
                # 为每个特征添加少量噪声作为负样本
                noise_samples = positive_samples.copy()
                for col in noise_samples.select_dtypes(include=[np.number]).columns:
                    if col not in ['id', 'timestamp', 'user_id', 'session_id']:
                        noise_samples[col] = noise_samples[col] + np.random.normal(0, 0.1, len(noise_samples))
                combined_data = pd.concat([aligned_positive, noise_samples], ignore_index=True)
            
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
            self.logger.info(f"  负样本（其他用户）: {negative_count}")
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
            data_result = load_data(str(temp_data_path))
            if data_result is None or len(data_result) < 1:
                self.logger.error("数据加载失败")
                return False
            
            # 提取数据（load_data返回(data, None, None)）
            data = data_result[0] if isinstance(data_result, tuple) else data_result
            if data is None:
                self.logger.error("数据加载失败")
                return False
            
            # 预处理数据
            preprocess_result = preprocess_data(data)
            if preprocess_result is None or len(preprocess_result) < 2:
                self.logger.error("数据预处理失败")
                return False
            
            # 提取预处理结果（preprocess_data返回(X, y, None)）
            X_processed, y_processed = preprocess_result[0], preprocess_result[1]
            if X_processed is None or y_processed is None:
                self.logger.error("数据预处理失败")
                return False
            
            # 训练模型
            model = train_model(X_processed, y_processed)
            if model is None:
                self.logger.error("模型训练失败")
                return False
            
            # 评估模型
            y_pred = model.predict(X_processed)
            y_pred_proba = model.predict_proba(X_processed)
            evaluation_result = evaluate_model(y_processed, y_pred, y_pred_proba)
            
            if evaluation_result is None or evaluation_result[0] is None:
                self.logger.error("模型评估失败")
                return False
            
            # 提取准确率
            metrics, cm = evaluation_result
            accuracy = metrics.get('accuracy', 0.0)
            self.logger.info(f"模型准确率: {accuracy:.4f}")
            
            # 保存模型
            model_path = self.models_path / f"user_{user_id}_model.pkl"
            save_success = save_model(model, str(model_path))
            if not save_success:
                self.logger.error("模型保存失败")
                return False
            else:
                self.logger.info(f"模型已保存: {model_path.resolve()}")
            
            # 保存特征列信息（以实际用于训练的数据列为准，避免后续预测特征名不一致）
            feature_info_path = self.models_path / f"user_{user_id}_features.json"
            
            # 调试信息
            self.logger.debug(f"feature_cols type: {type(feature_cols)}")
            self.logger.debug(f"feature_cols content: {feature_cols}")
            
            with open(feature_info_path, 'w') as f:
                used_feature_cols = list(X_processed.columns) if hasattr(X_processed, 'columns') else list(feature_cols)
                json.dump({
                    'feature_cols': used_feature_cols,
                    'n_features': len(used_feature_cols),
                    'training_samples': int(len(X_processed) if hasattr(X_processed, '__len__') else len(X)),
                    'accuracy': accuracy,
                    'metrics': metrics,
                    'trained_at': datetime.now().isoformat(),
                    'model_type': 'simple_classification'
                }, f, indent=2)
            self.logger.info(f"特征信息已保存: {feature_info_path.resolve()}")
            
            # 清理临时文件
            temp_data_path.unlink(missing_ok=True)
            
            self.logger.info(f"用户 {user_id} 模型训练完成，保存到 {model_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"使用classification模块训练失败: {str(e)}")
            # 如果真实模块失败且当前是模拟模块，打印提示安装真实依赖
            if not CLASSIFICATION_AVAILABLE:
                self.logger.error("当前使用的是模拟classification模块。请在Windows环境安装完整依赖以启用真实训练:")
                self.logger.error("pip install xgboost scikit-learn pandas numpy")
            import traceback
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            return False

    def load_user_model(self, user_id):
        """加载用户模型"""
        try:
            # 尝试不同的文件名格式
            possible_model_paths = [
                self.models_path / f"user_{user_id}_model.pkl",
                self.models_path / f"user_{user_id}_model.pkl"
            ]
            
            # 如果user_id不包含"user"后缀，也尝试添加
            if not user_id.endswith('_user'):
                possible_model_paths.append(self.models_path / f"user_{user_id}_user_model.pkl")
            
            self.logger.info("模型加载路径候选:")
            for p in possible_model_paths:
                self.logger.info(f"  - {p.resolve()}")
            
            model_path = None
            for path in possible_model_paths:
                if path.exists():
                    model_path = path
                    break
            
            if model_path is None:
                self.logger.error(f"用户 {user_id} 的模型文件不存在")
                self.logger.info("已尝试的路径：")
                for p in possible_model_paths:
                    self.logger.info(f"  - {p.resolve()}")
                # 列出所有可用的模型文件以便调试
                available_models = list(self.models_path.glob("user_*_model.pkl"))
                if available_models:
                    self.logger.debug(f"可用的模型文件: {[m.name for m in available_models]}")
                return None, None, None
            
            self.logger.info(f"选定模型路径: {model_path.resolve()}")
            # 对应的特征信息文件（修正文件名与后缀构造）
            feature_info_name = model_path.stem.replace('_model', '_features') + '.json'
            feature_info_path = model_path.with_name(feature_info_name)
            
            # 加载模型
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            # 加载特征信息
            feature_cols = None
            if feature_info_path.exists():
                with open(feature_info_path, 'r') as f:
                    feature_info = json.load(f)
                    feature_cols = feature_info.get('feature_cols', [])
            else:
                self.logger.warning(f"未找到特征信息文件: {feature_info_path}")
            
            self.logger.info(f"成功加载用户 {user_id} 的模型: {model_path.name}")
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
            
            # 准备特征：严格对齐训练列，缺失列补0，并按顺序重排
            if feature_cols:
                features = features.apply(pd.to_numeric, errors='coerce').fillna(0)
                for col in feature_cols:
                    if col not in features.columns:
                        features[col] = 0.0
                X = features.reindex(columns=feature_cols, fill_value=0).fillna(0)
            else:
                # 如果没有特征列信息，使用所有数值列
                numeric_cols = features.select_dtypes(include=[np.number]).columns
                X = features[numeric_cols].fillna(0)
            
            # 预测：传numpy避免xgboost特征名校验
            X_np = X.values
            predictions = model.predict(X_np)
            probabilities = model.predict_proba(X_np)
            
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