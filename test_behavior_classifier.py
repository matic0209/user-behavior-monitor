import unittest
import numpy as np
from behavior_classifier import BehaviorClassifier, BehaviorAnalyzer
from feature_engineering import FeatureExtractor

class TestBehaviorClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = BehaviorClassifier()
        self.analyzer = BehaviorAnalyzer(self.classifier)
        self.feature_extractor = FeatureExtractor()
        
    def test_model_initialization(self):
        """测试模型初始化"""
        self.assertIsNotNone(self.classifier.model)
        self.assertIsNotNone(self.classifier.scaler)
        
    def test_feature_preprocessing(self):
        """测试特征预处理"""
        # 生成测试特征
        features = np.random.rand(10, len(self.feature_extractor.get_feature_names()))
        
        # 预处理特征
        scaled_features = self.classifier.preprocess_features(features)
        
        # 验证预处理结果
        self.assertEqual(features.shape, scaled_features.shape)
        self.assertFalse(np.array_equal(features, scaled_features))
        
    def test_model_training(self):
        """测试模型训练"""
        # 生成训练数据
        n_samples = 100
        n_features = len(self.feature_extractor.get_feature_names())
        features = np.random.rand(n_samples, n_features)
        labels = np.random.randint(0, 3, n_samples)
        
        # 训练模型
        score = self.classifier.train(features, labels)
        
        # 验证训练结果
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1)
        
    def test_prediction(self):
        """测试预测功能"""
        # 生成训练数据
        n_samples = 100
        n_features = len(self.feature_extractor.get_feature_names())
        features = np.random.rand(n_samples, n_features)
        labels = np.random.randint(0, 3, n_samples)
        
        # 训练模型
        self.classifier.train(features, labels)
        
        # 生成测试数据
        test_features = np.random.rand(5, n_features)
        
        # 预测
        predictions = self.classifier.predict(test_features)
        
        # 验证预测结果
        self.assertEqual(len(predictions), 5)
        self.assertTrue(all(pred in [0, 1, 2] for pred in predictions))
        
    def test_probability_prediction(self):
        """测试概率预测"""
        # 生成训练数据
        n_samples = 100
        n_features = len(self.feature_extractor.get_feature_names())
        features = np.random.rand(n_samples, n_features)
        labels = np.random.randint(0, 3, n_samples)
        
        # 训练模型
        self.classifier.train(features, labels)
        
        # 生成测试数据
        test_features = np.random.rand(5, n_features)
        
        # 预测概率
        probabilities = self.classifier.predict_proba(test_features)
        
        # 验证概率预测结果
        self.assertEqual(probabilities.shape, (5, 3))
        self.assertTrue(np.allclose(np.sum(probabilities, axis=1), 1.0))
        
    def test_feature_importance(self):
        """测试特征重要性"""
        # 生成训练数据
        n_samples = 100
        n_features = len(self.feature_extractor.get_feature_names())
        features = np.random.rand(n_samples, n_features)
        labels = np.random.randint(0, 3, n_samples)
        
        # 训练模型
        self.classifier.train(features, labels)
        
        # 获取特征重要性
        importance = self.classifier.get_feature_importance()
        
        # 验证特征重要性
        self.assertEqual(len(importance), n_features)
        self.assertTrue(all(imp >= 0 and imp <= 1 for imp in importance.values()))
        
    def test_model_save_load(self):
        """测试模型保存和加载"""
        # 生成训练数据
        n_samples = 100
        n_features = len(self.feature_extractor.get_feature_names())
        features = np.random.rand(n_samples, n_features)
        labels = np.random.randint(0, 3, n_samples)
        
        # 训练模型
        self.classifier.train(features, labels)
        
        # 保存模型
        self.classifier.save_model()
        
        # 创建新的分类器实例
        new_classifier = BehaviorClassifier()
        
        # 验证模型加载
        self.assertIsNotNone(new_classifier.model)
        self.assertIsNotNone(new_classifier.scaler)
        
    def test_behavior_analysis(self):
        """测试行为分析"""
        # 生成训练数据
        n_samples = 100
        n_features = len(self.feature_extractor.get_feature_names())
        features = np.random.rand(n_samples, n_features)
        labels = np.random.randint(0, 3, n_samples)
        
        # 训练模型
        self.classifier.train(features, labels)
        
        # 生成测试数据
        test_features = np.random.rand(n_features)
        
        # 分析行为
        result = self.analyzer.analyze_behavior(test_features)
        
        # 验证分析结果
        self.assertIn('behavior_type', result)
        self.assertIn('confidence', result)
        self.assertIn('probabilities', result)
        self.assertIn('is_anomaly', result)
        
    def test_behavior_description(self):
        """测试行为描述"""
        # 测试各种行为类型的描述
        behavior_types = ["正常行为", "可疑行为", "异常行为", "未知行为"]
        
        for behavior_type in behavior_types:
            description = self.analyzer.get_behavior_description(behavior_type)
            self.assertIsInstance(description, str)
            self.assertGreater(len(description), 0)

if __name__ == '__main__':
    unittest.main() 