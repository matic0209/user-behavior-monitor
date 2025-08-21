import pandas as pd
import numpy as np
import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path
import sys
import threading
from collections import deque

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader

# 条件导入predict模块
try:
    from src.predict import predict_anomaly
    PREDICT_AVAILABLE = True
except ImportError:
    try:
        from src.predict_mock import predict_anomaly
        PREDICT_AVAILABLE = False
        print("警告: 使用模拟的predict模块")
    except ImportError:
        PREDICT_AVAILABLE = False
        # 创建模拟函数
        def predict_anomaly(*args, **kwargs): 
            return {"anomaly_score": 0.0, "prediction": 0}
        print("警告: 使用内置模拟函数")

class SimplePredictor:
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigLoader()
        self.db_path = Path(self.config.get_paths()['data']) / 'mouse_data.db'
        
        if not PREDICT_AVAILABLE:
            self.logger.error("predict模块不可用，预测功能受限")
        
        # 预测配置
        self.prediction_config = self.config.get_prediction_config()
        self.batch_size = self.prediction_config.get('batch_size', 50)
        self.prediction_interval = self.prediction_config.get('prediction_interval', 5)  # 降低到5秒
        self.anomaly_threshold = self.prediction_config.get('anomaly_threshold', 0.3)  # 降低阈值到0.3
        
        # 预测状态
        self.is_predicting = False
        self.prediction_thread = None
        self.data_buffer = deque(maxlen=self.batch_size * 2)
        
        self.logger.info("简单预测器初始化完成")
        self.logger.info(f"预测配置: batch_size={self.batch_size}, interval={self.prediction_interval}s, threshold={self.anomaly_threshold}")
        try:
            self.logger.info("UBM_MARK: PREDICT_INIT")
        except Exception:
            pass

    def load_recent_features(self, user_id, limit=None):
        """从数据库加载最近的特征数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT feature_vector, timestamp FROM features 
                WHERE user_id = ?
                ORDER BY timestamp DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            df = pd.read_sql_query(query, conn, params=(user_id,))
            conn.close()
            
            if not df.empty:
                # 解析特征向量
                df = self._parse_feature_vectors(df)
            
            self.logger.info(f"从数据库加载了用户 {user_id} 的 {len(df)} 条特征数据")
            return df
            
        except Exception as e:
            self.logger.error(f"从数据库加载特征数据失败: {str(e)}")
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

    def predict_with_trained_model(self, features_df, user_id):
        """使用训练好的模型进行预测"""
        try:
            # 导入模型训练器来加载模型
            from src.core.model_trainer.simple_model_trainer import SimpleModelTrainer
            model_trainer = SimpleModelTrainer()
            
            # 加载用户模型
            model, scaler, feature_cols = model_trainer.load_user_model(user_id)
            if model is None:
                self.logger.error(f"用户 {user_id} 的模型不存在，无法预测")
                return None
            
            # 特征对齐（严格一致：列集合与顺序必须与训练一致；缺失列用0补齐）
            if feature_cols:
                exclude_cols = ['id', 'timestamp', 'user_id', 'session_id']
                feature_cols_filtered = [col for col in feature_cols if col not in exclude_cols]
                
                # 将所有列尽可能转为数值，保证与训练阶段一致的输入类型
                features_df = features_df.apply(pd.to_numeric, errors='coerce').fillna(0)
                
                # 缺失特征用0补齐
                missing_features = [col for col in feature_cols_filtered if col not in features_df.columns]
                if missing_features:
                    self.logger.warning(f"缺少特征: {missing_features}")
                    for feature in missing_features:
                        features_df[feature] = 0.0
                
                # 严格按照训练时顺序取列
                X = features_df.reindex(columns=feature_cols_filtered, fill_value=0).fillna(0)
            else:
                # 如果没有特征列信息，使用所有数值列（排除非特征列）
                numeric_cols = features_df.select_dtypes(include=[np.number]).columns
                exclude_cols = ['id', 'timestamp', 'user_id', 'session_id']
                feature_cols_filtered = [col for col in numeric_cols if col not in exclude_cols]
                X = features_df[feature_cols_filtered].fillna(0)
            
            # 预测：传入numpy以避免XGBoost对特征名的严格校验
            X_np = X.values
            predictions = model.predict(X_np)
            probabilities = model.predict_proba(X_np)
            
            # 处理预测结果
            results = []
            for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
                # 获取正常类别的概率
                normal_prob = prob[1] if len(prob) > 1 else prob[0]
                anomaly_score = 1 - normal_prob
                is_anomaly = anomaly_score > self.anomaly_threshold
                
                results.append({
                    'prediction': int(pred),
                    'anomaly_score': float(anomaly_score),
                    'is_normal': not is_anomaly,
                    'probability': float(normal_prob),
                    'timestamp': features_df.iloc[i].get('timestamp', time.time())
                })
            
            self.logger.info(f"使用训练模型预测完成: {len(results)} 个结果")
            return results
            
        except Exception as e:
            self.logger.error(f"使用训练模型预测失败: {str(e)}")
            return None

    def predict_with_predict_module(self, features_df, user_id):
        """使用predict模块进行预测（备用方案）"""
        try:
            if not PREDICT_AVAILABLE:
                self.logger.error("predict模块不可用")
                return None
            
            if features_df.empty:
                self.logger.warning("特征数据为空，无法预测")
                return None
            
            self.logger.info(f"使用predict模块预测 {len(features_df)} 条数据")
            
            # 准备数据
            # 选择数值特征列
            numeric_cols = features_df.select_dtypes(include=[np.number]).columns
            feature_cols = [col for col in numeric_cols if col not in [
                'id', 'timestamp', 'user_id', 'session_id'
            ]]
            
            if len(feature_cols) == 0:
                self.logger.error("没有找到有效的特征列")
                return None
            
            X = features_df[feature_cols].fillna(0)
            
            # 使用predict模块进行预测
            # 批量处理，避免重复加载模型
            predictions = []
            
            # 尝试一次性加载模型，避免重复加载
            try:
                from src.predict import load_models
                model_info = load_models()
                user_model_info = model_info.get(user_id)
                
                if user_model_info:
                    # 如果有模型，批量预测
                    for i, row in X.iterrows():
                        feature_dict = row.to_dict()
                        result = predict_anomaly(user_id, feature_dict, model_info)
                        if result:
                            predictions.append(result['anomaly_score'])
                        else:
                            predictions.append(0.5)
                else:
                    # 如果没有模型，使用默认值
                    predictions = [0.5] * len(X)
                    
            except Exception as e:
                self.logger.warning(f"批量预测失败，使用默认值: {str(e)}")
                predictions = [0.5] * len(X)
            
            # 处理预测结果
            results = []
            for i, pred in enumerate(predictions):
                # 假设predict_anomaly返回异常分数（0-1之间，越高越异常）
                anomaly_score = float(pred)
                is_anomaly = anomaly_score > self.anomaly_threshold
                
                results.append({
                    'prediction': 0 if is_anomaly else 1,  # 0=异常, 1=正常
                    'anomaly_score': anomaly_score,
                    'is_normal': not is_anomaly,
                    'probability': 1 - anomaly_score,  # 正常概率
                    'timestamp': features_df.iloc[i].get('timestamp', time.time())
                })
            
            self.logger.info(f"预测完成: {len(results)} 个结果")
            return results
            
        except Exception as e:
            self.logger.error(f"使用predict模块预测失败: {str(e)}")
            return None

    def predict_user_behavior(self, user_id, features_df=None):
        """预测用户行为"""
        try:
            # 如果没有提供特征数据，从数据库加载最近的
            if features_df is None:
                features_df = self.load_recent_features(user_id, self.batch_size)
            
            if features_df.empty:
                self.logger.warning(f"用户 {user_id} 没有特征数据")
                return []
            
            # 优先使用训练好的模型进行预测
            results = self.predict_with_trained_model(features_df, user_id)
            
            # 如果训练模型不可用，使用predict模块作为备用
            if results is None:
                self.logger.warning("训练模型不可用，使用predict模块作为备用")
                results = self.predict_with_predict_module(features_df, user_id)
            
            if results:
                # 统计预测结果
                normal_count = sum(1 for r in results if r['is_normal'])
                anomaly_count = len(results) - normal_count
                
                self.logger.info(f"用户 {user_id} 预测结果: 正常 {normal_count}, 异常 {anomaly_count}")
                
                # 保存预测结果到数据库
                self.save_predictions_to_db(user_id, results)
            
            return results or []
            
        except Exception as e:
            self.logger.error(f"预测用户 {user_id} 行为失败: {str(e)}")
            return []

    def save_predictions_to_db(self, user_id, predictions):
        """保存预测结果到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建预测结果表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    prediction INTEGER NOT NULL,
                    anomaly_score REAL NOT NULL,
                    is_normal BOOLEAN NOT NULL,
                    probability REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 批量插入预测结果
            data_to_insert = [
                (user_id, pred['timestamp'], pred['prediction'], 
                 pred['anomaly_score'], pred['is_normal'], pred['probability'])
                for pred in predictions
            ]
            
            cursor.executemany('''
                INSERT INTO predictions 
                (user_id, timestamp, prediction, anomaly_score, is_normal, probability)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', data_to_insert)
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"保存了 {len(predictions)} 条预测结果到数据库")
            
        except Exception as e:
            self.logger.error(f"保存预测结果到数据库失败: {str(e)}")

    def start_continuous_prediction(self, user_id, callback=None):
        """开始连续预测"""
        if self.is_predicting:
            self.logger.warning("连续预测已在运行中")
            return False
        
        self.is_predicting = True
        self.prediction_thread = threading.Thread(
            target=self._prediction_loop,
            args=(user_id, callback),
            daemon=True
        )
        self.prediction_thread.start()
        
        self.logger.info(f"开始用户 {user_id} 的连续预测")
        try:
            self.logger.info("UBM_MARK: PREDICT_START")
        except Exception:
            pass
        return True

    def stop_continuous_prediction(self):
        """停止连续预测"""
        if not self.is_predicting:
            return
        
        self.is_predicting = False
        if self.prediction_thread:
            self.prediction_thread.join(timeout=5)
        
        self.logger.info("停止连续预测")

    def _prediction_loop(self, user_id, callback=None):
        """预测循环"""
        self.logger.info(f"开始预测循环 - 用户: {user_id}, 间隔: {self.prediction_interval}秒")
        
        while self.is_predicting:
            try:
                # 加载最近的特征数据
                features_df = self.load_recent_features(user_id, self.batch_size)
                
                if not features_df.empty:
                    self.logger.debug(f"加载到 {len(features_df)} 条特征数据")
                    try:
                        self.logger.info(f"UBM_MARK: PREDICT_RUNNING batch={len(features_df)}")
                    except Exception:
                        pass
                    
                    # 进行预测
                    predictions = self.predict_user_behavior(user_id, features_df)
                    
                    if predictions:
                        self.logger.debug(f"完成 {len(predictions)} 个预测")
                        
                        # 分析预测结果
                        normal_count = sum(1 for p in predictions if p['is_normal'])
                        anomaly_count = sum(1 for p in predictions if not p['is_normal'])
                        
                        self.logger.info(f"预测结果: 正常={normal_count}, 异常={anomaly_count}")
                        
                        # 检查是否有异常
                        anomalies = [p for p in predictions if not p['is_normal']]
                        if anomalies:
                            self.logger.warning(f"检测到 {len(anomalies)} 个异常行为")
                            # 显示异常详情
                            for i, anomaly in enumerate(anomalies[:3]):  # 只显示前3个
                                self.logger.warning(f"异常 {i+1}: 分数={anomaly['anomaly_score']:.3f}, 概率={anomaly['probability']:.3f}")
                        
                        # 调用回调函数
                        if callback:
                            callback(user_id, predictions)
                    else:
                        self.logger.warning("预测结果为空")
                else:
                    self.logger.debug("没有新的特征数据")
                
                # 等待下次预测
                time.sleep(self.prediction_interval)
                
            except Exception as e:
                self.logger.error(f"预测循环出错: {str(e)}")
                import traceback
                self.logger.debug(f"异常详情: {traceback.format_exc()}")
                time.sleep(self.prediction_interval)

    def get_user_predictions(self, user_id, limit=100):
        """获取用户的预测历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT * FROM predictions 
                WHERE user_id = ?
                ORDER BY timestamp DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            df = pd.read_sql_query(query, conn, params=(user_id,))
            conn.close()
            
            self.logger.info(f"获取用户 {user_id} 的预测历史: {len(df)} 条记录")
            return df
            
        except Exception as e:
            self.logger.error(f"获取用户预测历史失败: {str(e)}")
            return pd.DataFrame()

    def get_anomaly_statistics(self, user_id, hours=24):
        """获取异常统计信息"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 统计异常数量
            cursor.execute('''
                SELECT COUNT(*) FROM predictions 
                WHERE user_id = ? AND timestamp > ? AND is_normal = 0
            ''', (user_id, cutoff_time))
            
            anomaly_count = cursor.fetchone()[0]
            
            # 统计总预测数量
            cursor.execute('''
                SELECT COUNT(*) FROM predictions 
                WHERE user_id = ? AND timestamp > ?
            ''', (user_id, cutoff_time))
            
            total_count = cursor.fetchone()[0]
            
            conn.close()
            
            anomaly_rate = (anomaly_count / total_count * 100) if total_count > 0 else 0
            
            stats = {
                'anomaly_count': anomaly_count,
                'total_count': total_count,
                'anomaly_rate': anomaly_rate,
                'time_period_hours': hours
            }
            
            self.logger.info(f"用户 {user_id} 异常统计: {anomaly_count}/{total_count} ({anomaly_rate:.2f}%)")
            return stats
            
        except Exception as e:
            self.logger.error(f"获取异常统计失败: {str(e)}")
            return {} 