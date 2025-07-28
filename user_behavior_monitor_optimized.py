#!/usr/bin/env python3
"""
用户行为异常检测系统 - 优化版本
专门针对长期运行进行优化
"""

import sys
import os
import time
import signal
import threading
import psutil
import gc
import json
from pathlib import Path
import traceback
import win32gui
import win32con
import win32api
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader
from src.core.user_manager import UserManager
from src.core.data_collector.windows_mouse_collector import WindowsMouseCollector
from src.core.feature_engineer.simple_feature_processor import SimpleFeatureProcessor
from src.core.model_trainer.simple_model_trainer import SimpleModelTrainer
from src.core.predictor.simple_predictor import SimplePredictor
from src.core.alert.alert_service import AlertService

# 检查Windows API是否可用
WINDOWS_AVAILABLE = True
try:
    import win32api
    import win32con
except ImportError:
    WINDOWS_AVAILABLE = False
    print("警告: Windows API 不可用，无法执行强制登出或锁屏操作。")

# 检查GUI是否可用
GUI_AVAILABLE = True
try:
    import tkinter
    import tkinter.messagebox
except ImportError:
    GUI_AVAILABLE = False
    print("警告: GUI 不可用，无法显示告警弹窗。")

class OptimizedWindowsBehaviorMonitor:
    """优化的Windows用户行为监控系统"""
    
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigLoader()
        
        # 加载优化配置
        self.optimization_config = self._load_optimization_config()
        
        # 系统状态
        self.is_running = False
        self.is_collecting = False
        self.is_predicting = False
        self.current_user_id = None
        
        # 性能监控
        self.start_time = time.time()
        self.memory_usage = []
        self.cpu_usage = []
        self.restart_count = 0
        self.max_restart_attempts = self.optimization_config.get('reliability', {}).get('max_restart_attempts', 3)
        
        # 初始化组件
        self._initialize_components()
        
        # 注册信号处理器
        self._register_signal_handlers()
        
        self.logger.info("优化版用户行为监控系统初始化完成")
        self.logger.info(f"内存管理: {'启用' if self.optimization_config.get('memory_management', {}).get('enable_garbage_collection', True) else '禁用'}")
        self.logger.info(f"自动重启: {'启用' if self.optimization_config.get('reliability', {}).get('auto_restart_on_crash', True) else '禁用'}")
        self.logger.info(f"日志轮转: {'启用' if self.optimization_config.get('logging', {}).get('log_rotation', True) else '禁用'}")

    def _load_optimization_config(self):
        """加载优化配置"""
        try:
            config_file = Path(__file__).parent / "optimization_config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 默认优化配置
                return {
                    "memory_management": {
                        "enable_garbage_collection": True,
                        "gc_interval": 300,  # 5分钟
                        "max_memory_usage": "512MB"
                    },
                    "performance": {
                        "enable_caching": True,
                        "cache_size": 1000,
                        "prediction_batch_size": 100
                    },
                    "reliability": {
                        "auto_restart_on_crash": True,
                        "max_restart_attempts": 3,
                        "restart_delay": 30
                    },
                    "logging": {
                        "log_rotation": True,
                        "max_log_files": 10,
                        "max_log_size": "10MB",
                        "compress_old_logs": True
                    }
                }
        except Exception as e:
            self.logger.error(f"加载优化配置失败: {str(e)}")
            return {}

    def _initialize_components(self):
        """初始化系统组件"""
        try:
            # 用户管理
            self.user_manager = UserManager()
            self.current_user_id = self.user_manager.current_user_id
            
            # 数据采集器
            self.data_collector = WindowsMouseCollector()
            
            # 特征处理器
            self.feature_processor = SimpleFeatureProcessor()
            
            # 模型训练器
            self.model_trainer = SimpleModelTrainer()
            
            # 预测器
            self.predictor = SimplePredictor()
            
            # 告警服务
            self.alert_service = AlertService()
            
            self.logger.info("系统组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {str(e)}")
            raise

    def _register_signal_handlers(self):
        """注册信号处理器"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}，正在安全退出...")
        self.stop()

    def _monitor_performance(self):
        """性能监控"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()
            
            self.memory_usage.append(memory_info.rss / 1024 / 1024)  # MB
            self.cpu_usage.append(cpu_percent)
            
            # 保持最近100个数据点
            if len(self.memory_usage) > 100:
                self.memory_usage.pop(0)
            if len(self.cpu_usage) > 100:
                self.cpu_usage.pop(0)
            
            # 检查内存使用
            current_memory = self.memory_usage[-1]
            max_memory = self.optimization_config.get('memory_management', {}).get('max_memory_usage', '512MB')
            max_memory_mb = int(max_memory.replace('MB', ''))
            
            if current_memory > max_memory_mb:
                self.logger.warning(f"内存使用过高: {current_memory:.1f}MB > {max_memory_mb}MB")
                self._perform_garbage_collection()
            
            # 每10分钟记录一次性能数据
            if len(self.memory_usage) % 600 == 0:  # 10分钟 * 60秒
                avg_memory = sum(self.memory_usage) / len(self.memory_usage)
                avg_cpu = sum(self.cpu_usage) / len(self.cpu_usage)
                self.logger.info(f"性能统计 - 平均内存: {avg_memory:.1f}MB, 平均CPU: {avg_cpu:.1f}%")
                
        except Exception as e:
            self.logger.error(f"性能监控失败: {str(e)}")

    def _perform_garbage_collection(self):
        """执行垃圾回收"""
        try:
            if self.optimization_config.get('memory_management', {}).get('enable_garbage_collection', True):
                before_memory = psutil.Process().memory_info().rss / 1024 / 1024
                gc.collect()
                after_memory = psutil.Process().memory_info().rss / 1024 / 1024
                freed_memory = before_memory - after_memory
                
                self.logger.info(f"垃圾回收完成，释放内存: {freed_memory:.1f}MB")
                
        except Exception as e:
            self.logger.error(f"垃圾回收失败: {str(e)}")

    def _auto_restart_on_crash(self):
        """崩溃时自动重启"""
        try:
            if self.restart_count >= self.max_restart_attempts:
                self.logger.error(f"重启次数已达上限 ({self.max_restart_attempts})，停止自动重启")
                return False
            
            self.restart_count += 1
            restart_delay = self.optimization_config.get('reliability', {}).get('restart_delay', 30)
            
            self.logger.warning(f"系统崩溃，{restart_delay}秒后自动重启 (第{self.restart_count}次)")
            time.sleep(restart_delay)
            
            # 重新初始化组件
            self._initialize_components()
            return True
            
        except Exception as e:
            self.logger.error(f"自动重启失败: {str(e)}")
            return False

    def start(self):
        """启动系统"""
        try:
            self.logger.info("正在启动优化版Windows用户行为异常检测系统...")
            
            # 启动用户管理
            self.user_manager.start_keyboard_listener()
            self.is_running = True
            
            # 显示系统信息
            self._show_system_info()
            
            # 启动性能监控线程
            self._start_performance_monitoring()
            
            # 启动自动流程
            self._start_auto_workflow()
            
            self.logger.info("系统启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"系统启动失败: {str(e)}")
            if self.optimization_config.get('reliability', {}).get('auto_restart_on_crash', True):
                return self._auto_restart_on_crash()
            return False

    def _show_system_info(self):
        """显示系统信息"""
        print("\n" + "="*60)
        print("优化版Windows用户行为异常检测系统 v1.2.0")
        print("="*60)
        print("优化特性:")
        print("✓ 内存管理优化")
        print("✓ 性能监控")
        print("✓ 自动垃圾回收")
        print("✓ 崩溃自动重启")
        print("✓ 日志轮转")
        print("="*60)
        print("系统将自动执行以下流程:")
        print("1. 自动采集鼠标行为数据")
        print("2. 自动训练异常检测模型")
        print("3. 自动开始异常检测")
        print("="*60)
        print("快捷键说明 (连续输入4次):")
        print("  rrrr: 重新采集和训练")
        print("  aaaa: 手动触发告警弹窗")
        print("  qqqq: 退出系统")
        print("="*60)
        print("当前用户:", self.user_manager.current_user_id)
        print("系统状态: 优化运行中")
        print("="*60 + "\n")

    def _start_performance_monitoring(self):
        """启动性能监控"""
        def monitor_loop():
            while self.is_running:
                try:
                    self._monitor_performance()
                    time.sleep(1)  # 每秒监控一次
                except Exception as e:
                    self.logger.error(f"性能监控异常: {str(e)}")
                    time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        self.logger.info("性能监控已启动")

    def _start_auto_workflow(self):
        """启动自动工作流程"""
        try:
            self.logger.info("启动自动工作流程...")
            
            # 第一阶段：自动数据采集
            self._auto_data_collection()
            
            # 第二阶段：自动特征处理
            self._auto_feature_processing()
            
            # 第三阶段：自动模型训练
            self._auto_model_training()
            
            # 第四阶段：自动异常检测
            self._auto_anomaly_detection()
            
        except Exception as e:
            self.logger.error(f"自动工作流程失败: {str(e)}")
            if self.optimization_config.get('reliability', {}).get('auto_restart_on_crash', True):
                self._auto_restart_on_crash()

    def _auto_data_collection(self):
        """自动数据采集"""
        try:
            self.logger.info("=== 第一阶段：自动数据采集 ===")
            
            # 启动数据采集
            self.data_collector.start_collection()
            self.is_collecting = True
            
            # 采集时间：最多5分钟或达到1000个数据点
            max_collection_time = 300  # 5分钟
            min_data_points = 1000
            
            start_time = time.time()
            while self.is_running and self.is_collecting:
                current_time = time.time()
                elapsed_time = current_time - start_time
                
                # 检查采集的数据点数量
                collected_data = self.data_collector.get_collected_data()
                data_count = len(collected_data) if collected_data else 0
                
                self.logger.info(f"数据采集进度: {data_count} 个数据点, 已用时 {elapsed_time:.1f} 秒")
                
                # 检查是否达到停止条件
                if elapsed_time >= max_collection_time:
                    self.logger.info(f"数据采集时间达到上限 ({max_collection_time} 秒)")
                    break
                elif data_count >= min_data_points:
                    self.logger.info(f"数据采集数量达到要求 ({min_data_points} 个数据点)")
                    break
                
                time.sleep(10)  # 每10秒检查一次
            
            # 停止数据采集
            if self.is_collecting:
                self.data_collector.stop_collection()
                self.is_collecting = False
            
            self.logger.info("数据采集完成")
            
        except Exception as e:
            self.logger.error(f"自动数据采集失败: {str(e)}")
            raise

    def _auto_feature_processing(self):
        """自动特征处理"""
        try:
            self.logger.info("=== 第二阶段：自动特征处理 ===")
            
            # 获取采集的数据
            collected_data = self.data_collector.get_collected_data()
            if not collected_data:
                self.logger.warning("没有采集到数据，跳过特征处理")
                return
            
            # 处理特征
            features = self.feature_processor.process_features(collected_data)
            
            if features is not None and len(features) > 0:
                self.logger.info(f"特征处理完成，生成 {len(features)} 个特征")
            else:
                self.logger.warning("特征处理失败或没有生成有效特征")
            
        except Exception as e:
            self.logger.error(f"自动特征处理失败: {str(e)}")
            raise

    def _auto_model_training(self):
        """自动模型训练"""
        try:
            self.logger.info("=== 第三阶段：自动模型训练 ===")
            
            # 获取处理后的特征
            features = self.feature_processor.get_processed_features()
            if not features:
                self.logger.warning("没有可用的特征数据，跳过模型训练")
                return
            
            # 训练模型
            model_path = self.model_trainer.train_model(features)
            
            if model_path and Path(model_path).exists():
                self.logger.info(f"模型训练完成，模型保存至: {model_path}")
            else:
                self.logger.warning("模型训练失败")
            
        except Exception as e:
            self.logger.error(f"自动模型训练失败: {str(e)}")
            raise

    def _auto_anomaly_detection(self):
        """自动异常检测"""
        try:
            self.logger.info("=== 第四阶段：自动异常检测 ===")
            
            # 加载训练好的模型
            model_path = self.model_trainer.get_latest_model_path()
            if not model_path or not Path(model_path).exists():
                self.logger.warning("没有找到训练好的模型，跳过异常检测")
                return
            
            # 启动连续预测
            self.predictor.load_model(model_path)
            self.predictor.start_continuous_prediction(
                data_collector=self.data_collector,
                alert_service=self.alert_service,
                user_id=self.current_user_id
            )
            self.is_predicting = True
            
            self.logger.info("异常检测已启动，系统进入监控模式")
            
            # 保持系统运行
            while self.is_running:
                time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"自动异常检测失败: {str(e)}")
            raise

    def stop(self):
        """停止系统"""
        try:
            self.logger.info("正在停止系统...")
            
            # 停止数据采集
            if self.is_collecting and self.data_collector:
                self.logger.info("停止数据采集...")
                self.data_collector.stop_collection()
                self.is_collecting = False
            
            # 停止预测
            if self.is_predicting:
                self.logger.info("停止异常检测...")
                self.predictor.stop_continuous_prediction()
                self.is_predicting = False
            
            # 停止用户管理
            if self.user_manager:
                self.logger.info("停止用户管理...")
                self.user_manager.stop_keyboard_listener()
            
            # 保存系统状态
            self._save_system_state()
            
            # 执行垃圾回收
            self._perform_garbage_collection()
            
            self.is_running = False
            self.logger.info("系统已安全停止")
            
        except Exception as e:
            self.logger.error(f"停止系统时出现错误: {str(e)}")

    def _save_system_state(self):
        """保存系统状态"""
        try:
            state = {
                'timestamp': time.time(),
                'uptime': time.time() - self.start_time,
                'restart_count': self.restart_count,
                'memory_usage': self.memory_usage[-10:] if self.memory_usage else [],
                'cpu_usage': self.cpu_usage[-10:] if self.cpu_usage else [],
                'is_collecting': self.is_collecting,
                'is_predicting': self.is_predicting,
                'current_user_id': self.current_user_id
            }
            
            state_file = Path('data/system_state.json')
            state_file.parent.mkdir(exist_ok=True)
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            self.logger.info("系统状态已保存")
            
        except Exception as e:
            self.logger.error(f"保存系统状态失败: {str(e)}")

def main():
    """主函数"""
    try:
        # 创建监控系统实例
        monitor = OptimizedWindowsBehaviorMonitor()
        
        # 启动系统
        if monitor.start():
            print("系统启动成功，按 Ctrl+C 退出")
        else:
            print("系统启动失败")
            return 1
            
    except KeyboardInterrupt:
        print("\n收到退出信号，正在安全退出...")
        if 'monitor' in locals():
            monitor.stop()
    except Exception as e:
        print(f"系统运行异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 