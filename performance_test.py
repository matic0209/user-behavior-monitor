import time
import numpy as np
from feature_engineering import FeatureExtractor
import psutil
import os

def generate_test_events(num_events):
    """生成测试事件序列"""
    events = []
    for i in range(num_events):
        x = 100 * np.sin(2 * np.pi * i / 20)
        y = 100 * np.cos(2 * np.pi * i / 20)
        events.append(('mouse_move', 'user1', f'{1000.0 + i}', 'mouse_move', f'({x}, {y})'))
    return events

def get_memory_usage():
    """获取当前进程的内存使用情况"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # 转换为MB

def test_extraction_speed():
    """测试特征提取速度"""
    extractor = FeatureExtractor()
    
    # 测试不同大小的事件序列
    event_sizes = [100, 1000, 10000, 100000]
    
    print("\n特征提取速度测试:")
    print("-" * 50)
    print(f"{'事件数量':<10} {'提取时间(ms)':<15} {'内存使用(MB)':<15}")
    print("-" * 50)
    
    for size in event_sizes:
        events = generate_test_events(size)
        
        # 测量内存使用
        initial_memory = get_memory_usage()
        
        # 测量提取时间
        start_time = time.time()
        features = extractor.extract_features(events)
        end_time = time.time()
        
        # 计算内存增量
        final_memory = get_memory_usage()
        memory_usage = final_memory - initial_memory
        
        # 输出结果
        extraction_time = (end_time - start_time) * 1000  # 转换为毫秒
        print(f"{size:<10} {extraction_time:<15.2f} {memory_usage:<15.2f}")

def test_feature_quality():
    """测试特征质量"""
    extractor = FeatureExtractor()
    
    # 生成不同类型的移动模式
    patterns = {
        '直线运动': [(i*10, i*10) for i in range(100)],
        '圆形运动': [(100*np.sin(2*np.pi*i/20), 100*np.cos(2*np.pi*i/20)) for i in range(100)],
        '随机运动': [(np.random.normal(0, 50), np.random.normal(0, 50)) for _ in range(100)],
        '加速运动': [(i*i, i*i) for i in range(100)],
        '减速运动': [(100-i*i, 100-i*i) for i in range(10)]
    }
    
    print("\n特征质量测试:")
    print("-" * 50)
    print(f"{'移动模式':<15} {'特征方差':<15} {'特征范围':<15}")
    print("-" * 50)
    
    for pattern_name, coordinates in patterns.items():
        events = []
        for i, (x, y) in enumerate(coordinates):
            events.append(('mouse_move', 'user1', f'{1000.0 + i}', 'mouse_move', f'({x}, {y})'))
        
        features = extractor.extract_features(events)
        
        # 计算特征统计信息
        feature_variance = np.var(features)
        feature_range = np.ptp(features)
        
        print(f"{pattern_name:<15} {feature_variance:<15.2f} {feature_range:<15.2f}")

def test_feature_stability():
    """测试特征稳定性"""
    extractor = FeatureExtractor()
    
    # 生成带有噪声的测试数据
    base_events = generate_test_events(1000)
    noise_levels = [0, 0.1, 0.5, 1.0, 2.0]
    
    print("\n特征稳定性测试:")
    print("-" * 50)
    print(f"{'噪声水平':<10} {'特征变化率':<15}")
    print("-" * 50)
    
    # 获取基准特征
    base_features = extractor.extract_features(base_events)
    
    for noise in noise_levels:
        # 添加噪声
        noisy_events = []
        for event in base_events:
            x, y = eval(event[4])
            noisy_x = x + np.random.normal(0, noise)
            noisy_y = y + np.random.normal(0, noise)
            noisy_events.append(('mouse_move', 'user1', event[2], 'mouse_move', f'({noisy_x}, {noisy_y})'))
        
        # 计算带噪声的特征
        noisy_features = extractor.extract_features(noisy_events)
        
        # 计算特征变化率
        feature_change = np.mean(np.abs(noisy_features - base_features) / (np.abs(base_features) + 1e-10))
        
        print(f"{noise:<10.1f} {feature_change:<15.4f}")

if __name__ == '__main__':
    print("开始性能测试...")
    
    # 运行所有测试
    test_extraction_speed()
    test_feature_quality()
    test_feature_stability()
    
    print("\n性能测试完成!") 