import numpy as np
import joblib
import os
from feature_engineering import FeatureExtractor

class BehaviorAnalyzer:
    def __init__(self, model_path='mouse_dynamics_model.joblib'):
        self.model_path = model_path
        self.model = None
        self.feature_extractor = FeatureExtractor()
        self.initialize_model()
        
    def initialize_model(self):
        """初始化或加载模型"""
        if os.path.exists(self.model_path):
            # 加载已有模型
            self.model = joblib.load(self.model_path)
        else:
            raise FileNotFoundError(f"模型文件 {self.model_path} 不存在")
            
    def detect_anomaly(self, events):
        """检测异常行为"""
        if self.model is None:
            return False, 0.0
            
        # 提取特征
        features = self.feature_extractor.extract_features(events)
        
        # 预测
        try:
            # 使用模型预测
            prediction = self.model.predict_proba([features])[0]
            # 获取异常类的概率
            anomaly_prob = prediction[1] if len(prediction) > 1 else prediction[0]
            
            # 如果异常概率大于阈值，认为是异常
            threshold = 0.8
            is_anomaly = anomaly_prob > threshold
            
            return is_anomaly, anomaly_prob
            
        except Exception as e:
            print(f"预测失败: {str(e)}")
            return False, 0.0
            
    def get_feature_names(self):
        """获取特征名称"""
        return self.feature_extractor.get_feature_names() 