import numpy as np
import pandas as pd
from scipy import stats
from scipy.fft import fft
from scipy.signal import find_peaks
import math

class FeatureExtractor:
    def __init__(self):
        self.feature_names = self._generate_feature_names()
        
    def _generate_feature_names(self):
        """生成所有特征名称"""
        names = []
        
        # 基础运动特征 (20个)
        base_features = [
            'mean_dx', 'mean_dy', 'std_dx', 'std_dy',
            'min_dx', 'min_dy', 'max_dx', 'max_dy',
            'range_dx', 'range_dy', 'median_dx', 'median_dy',
            'skew_dx', 'skew_dy', 'kurtosis_dx', 'kurtosis_dy',
            'iqr_dx', 'iqr_dy', 'mad_dx', 'mad_dy'
        ]
        names.extend(base_features)
        
        # 速度特征 (30个)
        speed_features = [
            'mean_speed', 'std_speed', 'max_speed', 'min_speed',
            'median_speed', 'range_speed', 'skew_speed', 'kurtosis_speed',
            'iqr_speed', 'mad_speed'
        ]
        # 速度分位数特征
        for i in range(1, 10):
            speed_features.append(f'speed_percentile_{i*10}')
        # 速度变化率特征
        for i in range(1, 11):
            speed_features.append(f'speed_change_rate_{i}')
        names.extend(speed_features)
        
        # 加速度特征 (30个)
        acc_features = [
            'mean_acc', 'std_acc', 'max_acc', 'min_acc',
            'median_acc', 'range_acc', 'skew_acc', 'kurtosis_acc',
            'iqr_acc', 'mad_acc'
        ]
        # 加速度分位数特征
        for i in range(1, 10):
            acc_features.append(f'acc_percentile_{i*10}')
        # 加速度变化率特征
        for i in range(1, 11):
            acc_features.append(f'acc_change_rate_{i}')
        names.extend(acc_features)
        
        # 角度特征 (30个)
        angle_features = [
            'mean_angle', 'std_angle', 'max_angle', 'min_angle',
            'median_angle', 'range_angle', 'skew_angle', 'kurtosis_angle',
            'iqr_angle', 'mad_angle'
        ]
        # 角度分位数特征
        for i in range(1, 10):
            angle_features.append(f'angle_percentile_{i*10}')
        # 角度变化率特征
        for i in range(1, 11):
            angle_features.append(f'angle_change_rate_{i}')
        names.extend(angle_features)
        
        # 曲率特征 (30个)
        curvature_features = [
            'mean_curvature', 'std_curvature', 'max_curvature', 'min_curvature',
            'median_curvature', 'range_curvature', 'skew_curvature', 'kurtosis_curvature',
            'iqr_curvature', 'mad_curvature'
        ]
        # 曲率分位数特征
        for i in range(1, 10):
            curvature_features.append(f'curvature_percentile_{i*10}')
        # 曲率变化率特征
        for i in range(1, 11):
            curvature_features.append(f'curvature_change_rate_{i}')
        names.extend(curvature_features)
        
        # 时间特征 (30个)
        time_features = [
            'mean_duration', 'std_duration', 'max_duration', 'min_duration',
            'median_duration', 'range_duration', 'skew_duration', 'kurtosis_duration',
            'iqr_duration', 'mad_duration'
        ]
        # 时间分位数特征
        for i in range(1, 10):
            time_features.append(f'duration_percentile_{i*10}')
        # 时间变化率特征
        for i in range(1, 11):
            time_features.append(f'duration_change_rate_{i}')
        names.extend(time_features)
        
        # 距离特征 (30个)
        distance_features = [
            'mean_distance', 'std_distance', 'max_distance', 'min_distance',
            'median_distance', 'range_distance', 'skew_distance', 'kurtosis_distance',
            'iqr_distance', 'mad_distance'
        ]
        # 距离分位数特征
        for i in range(1, 10):
            distance_features.append(f'distance_percentile_{i*10}')
        # 距离变化率特征
        for i in range(1, 11):
            distance_features.append(f'distance_change_rate_{i}')
        names.extend(distance_features)
        
        # 频率域特征 (20个)
        freq_features = [
            'fft_mean', 'fft_std', 'fft_max', 'fft_min',
            'fft_median', 'fft_range', 'fft_skew', 'fft_kurtosis',
            'fft_iqr', 'fft_mad'
        ]
        # 频率分位数特征
        for i in range(1, 10):
            freq_features.append(f'fft_percentile_{i*10}')
        names.extend(freq_features)
        
        return names
    
    def extract_features(self, events):
        """从事件序列中提取特征"""
        if not events:
            return np.zeros(len(self.feature_names))
            
        # 提取鼠标移动事件
        mouse_moves = [event for event in events if event[3] == 'mouse_move']
        if len(mouse_moves) < 2:
            return np.zeros(len(self.feature_names))
            
        # 计算基本移动特征
        dx_list = []
        dy_list = []
        speed_list = []
        angle_list = []
        duration_list = []
        distance_list = []
        
        for i in range(1, len(mouse_moves)):
            prev_x, prev_y = eval(mouse_moves[i-1][4])
            curr_x, curr_y = eval(mouse_moves[i][4])
            prev_time = float(mouse_moves[i-1][2])
            curr_time = float(mouse_moves[i][2])
            
            # 计算位移
            dx = curr_x - prev_x
            dy = curr_y - prev_y
            dx_list.append(dx)
            dy_list.append(dy)
            
            # 计算时间差
            duration = curr_time - prev_time
            duration_list.append(duration)
            
            # 计算距离
            distance = np.sqrt(dx**2 + dy**2)
            distance_list.append(distance)
            
            # 计算速度
            if duration > 0:
                speed = distance / duration
                speed_list.append(speed)
            
            # 计算角度
            if dx != 0 or dy != 0:
                angle = np.arctan2(dy, dx)
                angle_list.append(angle)
        
        # 计算加速度
        acceleration_list = []
        for i in range(1, len(speed_list)):
            if duration_list[i] > 0:
                acc = (speed_list[i] - speed_list[i-1]) / duration_list[i]
                acceleration_list.append(acc)
        
        # 计算曲率
        curvature_list = []
        for i in range(1, len(angle_list)):
            if duration_list[i] > 0:
                curvature = (angle_list[i] - angle_list[i-1]) / duration_list[i]
                curvature_list.append(curvature)
        
        # 计算频率域特征
        if len(speed_list) > 0:
            fft_features = np.abs(fft(speed_list))
        else:
            fft_features = np.zeros(10)
        
        # 计算所有特征
        features = []
        
        # 基础运动特征
        features.extend(self._calculate_statistics(dx_list))
        features.extend(self._calculate_statistics(dy_list))
        
        # 速度特征
        features.extend(self._calculate_statistics(speed_list))
        features.extend(self._calculate_percentiles(speed_list))
        features.extend(self._calculate_change_rates(speed_list))
        
        # 加速度特征
        features.extend(self._calculate_statistics(acceleration_list))
        features.extend(self._calculate_percentiles(acceleration_list))
        features.extend(self._calculate_change_rates(acceleration_list))
        
        # 角度特征
        features.extend(self._calculate_statistics(angle_list))
        features.extend(self._calculate_percentiles(angle_list))
        features.extend(self._calculate_change_rates(angle_list))
        
        # 曲率特征
        features.extend(self._calculate_statistics(curvature_list))
        features.extend(self._calculate_percentiles(curvature_list))
        features.extend(self._calculate_change_rates(curvature_list))
        
        # 时间特征
        features.extend(self._calculate_statistics(duration_list))
        features.extend(self._calculate_percentiles(duration_list))
        features.extend(self._calculate_change_rates(duration_list))
        
        # 距离特征
        features.extend(self._calculate_statistics(distance_list))
        features.extend(self._calculate_percentiles(distance_list))
        features.extend(self._calculate_change_rates(distance_list))
        
        # 频率域特征
        features.extend(self._calculate_statistics(fft_features))
        features.extend(self._calculate_percentiles(fft_features))
        
        return np.array(features)
    
    def _calculate_statistics(self, data):
        """计算基本统计特征"""
        if not data:
            return [0] * 10
            
        return [
            np.mean(data),
            np.std(data),
            np.max(data),
            np.min(data),
            np.median(data),
            np.ptp(data),
            stats.skew(data),
            stats.kurtosis(data),
            stats.iqr(data),
            stats.median_abs_deviation(data)
        ]
    
    def _calculate_percentiles(self, data):
        """计算分位数特征"""
        if not data:
            return [0] * 9
            
        return [np.percentile(data, i*10) for i in range(1, 10)]
    
    def _calculate_change_rates(self, data):
        """计算变化率特征"""
        if len(data) < 2:
            return [0] * 10
            
        changes = np.diff(data)
        rates = changes / data[:-1]
        
        return [
            np.mean(rates),
            np.std(rates),
            np.max(rates),
            np.min(rates),
            np.median(rates),
            np.ptp(rates),
            stats.skew(rates),
            stats.kurtosis(rates),
            stats.iqr(rates),
            stats.median_abs_deviation(rates)
        ]
    
    def get_feature_names(self):
        return self.feature_names 