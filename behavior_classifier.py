import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os

class BehaviorClassifier:
    def __init__(self, model_path='models/behavior_model.joblib'):
        """初始化行为分类器
        
        Args:
            model_path: 模型保存路径
        """
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        
        # 如果模型文件存在，加载模型
        if os.path.exists(model_path):
            self.load_model()
        else:
            # 创建新的模型
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
    
    def preprocess_features(self, features):
        """预处理特征
        
        Args:
            features: 特征向量或特征矩阵
            
        Returns:
            标准化后的特征
        """
        return self.scaler.fit_transform(features)
    
    def train(self, features, labels):
        """训练模型
        
        Args:
            features: 特征矩阵
            labels: 标签向量
        """
        # 数据分割
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=42
        )
        
        # 特征标准化
        X_train_scaled = self.preprocess_features(X_train)
        X_test_scaled = self.preprocess_features(X_test)
        
        # 训练模型
        self.model.fit(X_train_scaled, y_train)
        
        # 评估模型
        y_pred = self.model.predict(X_test_scaled)
        print("\n模型评估报告:")
        print(classification_report(y_test, y_pred))
        
        # 保存模型
        self.save_model()
        
        return self.model.score(X_test_scaled, y_test)
    
    def predict(self, features):
        """预测行为类别
        
        Args:
            features: 特征向量或特征矩阵
            
        Returns:
            预测的类别
        """
        if self.model is None:
            raise ValueError("模型未训练或加载")
            
        # 标准化特征
        features_scaled = self.scaler.transform(features)
        
        # 预测
        return self.model.predict(features_scaled)
    
    def predict_proba(self, features):
        """预测行为类别的概率
        
        Args:
            features: 特征向量或特征矩阵
            
        Returns:
            各类别的预测概率
        """
        if self.model is None:
            raise ValueError("模型未训练或加载")
            
        # 标准化特征
        features_scaled = self.scaler.transform(features)
        
        # 预测概率
        return self.model.predict_proba(features_scaled)
    
    def get_feature_importance(self):
        """获取特征重要性
        
        Returns:
            特征重要性字典
        """
        if self.model is None:
            raise ValueError("模型未训练或加载")
            
        return dict(zip(self.model.feature_names_in_, 
                       self.model.feature_importances_))
    
    def save_model(self):
        """保存模型"""
        if self.model is None:
            raise ValueError("模型未训练")
            
        # 创建模型目录
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # 保存模型和标准化器
        model_data = {
            'model': self.model,
            'scaler': self.scaler
        }
        joblib.dump(model_data, self.model_path)
    
    def load_model(self):
        """加载模型"""
        try:
            model_data = joblib.load(self.model_path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
        except Exception as e:
            print(f"加载模型失败: {str(e)}")
            self.model = None
            self.scaler = StandardScaler()

class BehaviorAnalyzer:
    def __init__(self, classifier=None):
        """初始化行为分析器
        
        Args:
            classifier: 行为分类器实例
        """
        self.classifier = classifier or BehaviorClassifier()
        self.behavior_types = {
            0: "正常行为",
            1: "可疑行为",
            2: "异常行为"
        }
    
    def analyze_behavior(self, features, threshold=0.8):
        """分析行为
        
        Args:
            features: 特征向量
            threshold: 异常判定阈值
            
        Returns:
            行为分析结果字典
        """
        # 获取预测概率
        probabilities = self.classifier.predict_proba(features.reshape(1, -1))[0]
        
        # 获取最可能的类别
        predicted_class = np.argmax(probabilities)
        confidence = probabilities[predicted_class]
        
        # 判断行为类型
        if confidence < threshold:
            behavior_type = "未知行为"
        else:
            behavior_type = self.behavior_types.get(predicted_class, "未知行为")
        
        # 构建结果
        result = {
            "behavior_type": behavior_type,
            "confidence": confidence,
            "probabilities": dict(zip(self.behavior_types.values(), probabilities)),
            "is_anomaly": predicted_class > 0 and confidence >= threshold
        }
        
        return result
    
    def get_behavior_description(self, behavior_type):
        """获取行为描述
        
        Args:
            behavior_type: 行为类型
            
        Returns:
            行为描述
        """
        descriptions = {
            "正常行为": "用户行为符合正常模式，没有发现异常。",
            "可疑行为": "用户行为存在一些可疑特征，建议进一步观察。",
            "异常行为": "用户行为明显偏离正常模式，可能存在安全风险。",
            "未知行为": "无法确定用户行为类型，需要更多数据进行分析。"
        }
        return descriptions.get(behavior_type, "未知行为类型") 