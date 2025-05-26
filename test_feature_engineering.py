import unittest
import numpy as np
from feature_engineering import FeatureExtractor

class TestFeatureExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = FeatureExtractor()
        
    def test_feature_count(self):
        """测试特征数量是否达到200个"""
        self.assertGreaterEqual(len(self.extractor.get_feature_names()), 200)
        
    def test_empty_events(self):
        """测试空事件序列"""
        features = self.extractor.extract_features([])
        self.assertEqual(len(features), len(self.extractor.get_feature_names()))
        self.assertTrue(np.all(features == 0))
        
    def test_single_event(self):
        """测试单个事件"""
        events = [
            ('mouse_move', 'user1', '1000.0', 'mouse_move', '(100, 100)')
        ]
        features = self.extractor.extract_features(events)
        self.assertEqual(len(features), len(self.extractor.get_feature_names()))
        self.assertTrue(np.all(features == 0))
        
    def test_basic_movement(self):
        """测试基本移动特征"""
        events = [
            ('mouse_move', 'user1', '1000.0', 'mouse_move', '(100, 100)'),
            ('mouse_move', 'user1', '1001.0', 'mouse_move', '(200, 200)'),
            ('mouse_move', 'user1', '1002.0', 'mouse_move', '(300, 300)')
        ]
        features = self.extractor.extract_features(events)
        
        # 验证特征数量
        self.assertEqual(len(features), len(self.extractor.get_feature_names()))
        
        # 验证基础运动特征
        feature_names = self.extractor.get_feature_names()
        dx_mean_idx = feature_names.index('mean_dx')
        dy_mean_idx = feature_names.index('mean_dy')
        
        self.assertAlmostEqual(features[dx_mean_idx], 100.0)
        self.assertAlmostEqual(features[dy_mean_idx], 100.0)
        
    def test_speed_features(self):
        """测试速度特征"""
        events = [
            ('mouse_move', 'user1', '1000.0', 'mouse_move', '(0, 0)'),
            ('mouse_move', 'user1', '1001.0', 'mouse_move', '(100, 0)'),
            ('mouse_move', 'user1', '1002.0', 'mouse_move', '(200, 0)')
        ]
        features = self.extractor.extract_features(events)
        
        # 验证速度特征
        feature_names = self.extractor.get_feature_names()
        speed_mean_idx = feature_names.index('mean_speed')
        
        # 速度应该是100像素/秒
        self.assertAlmostEqual(features[speed_mean_idx], 100.0, places=1)
        
    def test_angle_features(self):
        """测试角度特征"""
        events = [
            ('mouse_move', 'user1', '1000.0', 'mouse_move', '(0, 0)'),
            ('mouse_move', 'user1', '1001.0', 'mouse_move', '(100, 100)'),
            ('mouse_move', 'user1', '1002.0', 'mouse_move', '(200, 200)')
        ]
        features = self.extractor.extract_features(events)
        
        # 验证角度特征
        feature_names = self.extractor.get_feature_names()
        angle_mean_idx = feature_names.index('mean_angle')
        
        # 角度应该是45度（π/4弧度）
        self.assertAlmostEqual(features[angle_mean_idx], np.pi/4, places=1)
        
    def test_curvature_features(self):
        """测试曲率特征"""
        events = [
            ('mouse_move', 'user1', '1000.0', 'mouse_move', '(0, 0)'),
            ('mouse_move', 'user1', '1001.0', 'mouse_move', '(100, 0)'),
            ('mouse_move', 'user1', '1002.0', 'mouse_move', '(100, 100)')
        ]
        features = self.extractor.extract_features(events)
        
        # 验证曲率特征
        feature_names = self.extractor.get_feature_names()
        curvature_mean_idx = feature_names.index('mean_curvature')
        
        # 曲率应该接近π/2（90度转弯）
        self.assertAlmostEqual(features[curvature_mean_idx], np.pi/2, places=1)
        
    def test_frequency_features(self):
        """测试频率域特征"""
        # 创建一个正弦波形的移动
        events = []
        for i in range(100):
            x = 100 * np.sin(2 * np.pi * i / 20)  # 20个点一个周期
            y = 100 * np.cos(2 * np.pi * i / 20)
            events.append(('mouse_move', 'user1', f'{1000.0 + i}', 'mouse_move', f'({x}, {y})'))
            
        features = self.extractor.extract_features(events)
        
        # 验证频率域特征
        feature_names = self.extractor.get_feature_names()
        fft_mean_idx = feature_names.index('fft_mean')
        
        # FFT均值应该大于0
        self.assertGreater(features[fft_mean_idx], 0)
        
    def test_percentile_features(self):
        """测试分位数特征"""
        events = []
        for i in range(100):
            x = i * 10
            y = i * 10
            events.append(('mouse_move', 'user1', f'{1000.0 + i}', 'mouse_move', f'({x}, {y})'))
            
        features = self.extractor.extract_features(events)
        
        # 验证分位数特征
        feature_names = self.extractor.get_feature_names()
        speed_percentile_50_idx = feature_names.index('speed_percentile_50')
        
        # 中位数速度应该接近10像素/秒
        self.assertAlmostEqual(features[speed_percentile_50_idx], 10.0, places=1)
        
    def test_change_rate_features(self):
        """测试变化率特征"""
        events = []
        for i in range(100):
            x = i * i  # 加速运动
            y = i * i
            events.append(('mouse_move', 'user1', f'{1000.0 + i}', 'mouse_move', f'({x}, {y})'))
            
        features = self.extractor.extract_features(events)
        
        # 验证变化率特征
        feature_names = self.extractor.get_feature_names()
        speed_change_rate_1_idx = feature_names.index('speed_change_rate_1')
        
        # 速度变化率应该大于0（加速运动）
        self.assertGreater(features[speed_change_rate_1_idx], 0)

if __name__ == '__main__':
    unittest.main() 