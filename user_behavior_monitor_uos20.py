#!/usr/bin/env python3
"""
用户行为异常检测系统 - UOS20版本
简化流程：自动采集 → 自动训练 → 自动检测
适配Linux系统，移除Windows特定功能
"""

import sys
import os
import time
import signal
import threading
import psutil
from pathlib import Path
import traceback
import json
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

# 检查GUI是否可用
GUI_AVAILABLE = True
try:
    import tkinter
    import tkinter.messagebox
except ImportError:
    GUI_AVAILABLE = False
    print("警告: GUI 不可用，无法显示告警弹窗。")


class UOS20BehaviorMonitor:
    """UOS20用户行为异常检测系统"""
    
    def __init__(self):
        """初始化系统"""
        self.logger = Logger()
        self.config = ConfigLoader()
        
        self.logger.info("=== UOS20用户行为异常检测系统启动 ===")
        self.logger.info("版本: v1.3.0 UOS20版")
        
        # 系统状态
        self.is_running = False
        self.is_collecting = False
        self.is_training = False
        self.is_predicting = False
        self.current_user_id = None
        self.current_session_id = None
        
        # 自动流程控制
        self.auto_mode = True
        self.min_data_points = 1000  # 最少数据点
        self.collection_timeout = 300  # 采集超时时间（秒）
        
        # 初始化核心模块
        self._init_modules()
        
        # 注册信号处理器
        self._register_signal_handlers()
        
        # 系统统计
        self.stats = {
            'start_time': time.time(),
            'collection_sessions': 0,
            'training_sessions': 0,
            'prediction_sessions': 0,
            'anomalies_detected': 0,
            'alerts_sent': 0
        }
        
        self.logger.info("系统初始化完成")

    def _init_modules(self):
        """初始化核心模块"""
        try:
            self.logger.info("正在初始化核心模块...")
            
            # 用户管理模块
            self.user_manager = UserManager()
            self.logger.info("✓ 用户管理模块初始化完成")
            
            # 数据采集模块
            self.data_collector = WindowsMouseCollector()
            self.logger.info("✓ 数据采集模块初始化完成")
            
            # 特征处理模块
            self.feature_processor = SimpleFeatureProcessor()
            self.logger.info("✓ 特征处理模块初始化完成")
            
            # 模型训练模块
            self.model_trainer = SimpleModelTrainer()
            self.logger.info("✓ 模型训练模块初始化完成")
            
            # 预测模块
            self.predictor = SimplePredictor()
            self.logger.info("✓ 预测模块初始化完成")
            
            # 告警服务模块
            self.alert_service = AlertService()
            self.logger.info("✓ 告警服务模块初始化完成")
            
            # 注册回调函数
            self._register_callbacks()
            
        except Exception as e:
            self.logger.error(f"模块初始化失败: {e}")
            traceback.print_exc()
            raise

    def _register_callbacks(self):
        """注册回调函数"""
        try:
            # 用户管理回调
            self.user_manager.set_retrain_callback(self._on_retrain_model)
            self.user_manager.set_alert_callback(self._on_trigger_alert)
            self.user_manager.set_quit_callback(self._on_quit_system)
            
            self.logger.info("✓ 回调函数注册完成")
            
        except Exception as e:
            self.logger.error(f"回调函数注册失败: {e}")

    def _register_signal_handlers(self):
        """注册信号处理器"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}，正在停止系统...")
        self.stop()

    def start(self):
        """启动系统"""
        try:
            self.logger.info("正在启动系统...")
            
            # 显示系统信息
            self._show_system_info()
            
            # 启动用户管理模块
            self.user_manager.start_keyboard_listener()
            self.logger.info("✓ 键盘监听器已启动")
            
            # 标记系统为运行状态
            self.is_running = True
            
            # 启动自动工作流程
            self._start_auto_workflow()
            
            self.logger.info("系统启动完成，开始自动工作流程")
            
        except Exception as e:
            self.logger.error(f"系统启动失败: {e}")
            traceback.print_exc()
            raise

    def _show_system_info(self):
        """显示系统信息"""
        self.logger.info("=" * 50)
        self.logger.info("系统信息:")
        self.logger.info(f"  操作系统: {os.name}")
        self.logger.info(f"  Python版本: {sys.version}")
        self.logger.info(f"  项目路径: {project_root}")
        self.logger.info(f"  工作目录: {os.getcwd()}")
        self.logger.info(f"  内存使用: {psutil.virtual_memory().percent:.1f}%")
        self.logger.info(f"  CPU使用率: {psutil.cpu_percent(interval=1):.1f}%")
        self.logger.info("=" * 50)

    def _start_auto_workflow(self):
        """启动自动工作流程"""
        if self.auto_mode:
            self.logger.info("启动自动工作流程...")
            workflow_thread = threading.Thread(target=self._auto_workflow, daemon=True)
            workflow_thread.start()
            self.logger.info("✓ 自动工作流程线程已启动")

    def _auto_workflow(self):
        """自动工作流程"""
        try:
            self.logger.info("开始自动工作流程...")
            
            # 第一阶段：自动数据采集
            self.logger.info("第一阶段：开始自动数据采集")
            if self._auto_collect_data():
                self.logger.info("✓ 数据采集完成")
                
                # 第二阶段：自动特征处理
                self.logger.info("第二阶段：开始自动特征处理")
                if self._auto_process_features():
                    self.logger.info("✓ 特征处理完成")
                    
                    # 第三阶段：自动模型训练
                    self.logger.info("第三阶段：开始自动模型训练")
                    if self._auto_train_model():
                        self.logger.info("✓ 模型训练完成")
                        
                        # 第四阶段：自动异常检测
                        self.logger.info("第四阶段：开始自动异常检测")
                        self._auto_start_prediction()
                        self.logger.info("✓ 异常检测已启动")
                        
                        # 保持系统运行
                        while self.is_running and self.is_predicting:
                            time.sleep(1)
                    else:
                        self.logger.error("模型训练失败")
                else:
                    self.logger.error("特征处理失败")
            else:
                self.logger.error("数据采集失败")
                
        except Exception as e:
            self.logger.error(f"自动工作流程异常: {e}")
            traceback.print_exc()

    def _auto_collect_data(self):
        """自动数据采集"""
        try:
            self.is_collecting = True
            self.stats['collection_sessions'] += 1
            
            self.logger.info("开始自动数据采集...")
            self.logger.info(f"最少数据点: {self.min_data_points}")
            self.logger.info(f"采集超时时间: {self.collection_timeout}秒")
            
            # 启动数据采集
            self.data_collector.start_collection()
            
            # 监控采集进度
            start_time = time.time()
            while self.is_collecting:
                current_time = time.time()
                elapsed_time = current_time - start_time
                
                # 检查超时
                if elapsed_time > self.collection_timeout:
                    self.logger.info(f"采集超时，已运行 {elapsed_time:.1f} 秒")
                    break
                
                # 检查数据点数量
                data_count = self._get_data_count()
                if data_count >= self.min_data_points:
                    self.logger.info(f"已达到目标数据点数量: {data_count}")
                    break
                
                # 显示进度
                if int(current_time) % 10 == 0:  # 每10秒显示一次
                    self.logger.info(f"采集进度: {data_count}/{self.min_data_points} 数据点 "
                                   f"({elapsed_time:.1f}/{self.collection_timeout}秒)")
                
                time.sleep(1)
            
            # 停止数据采集
            self.data_collector.stop_collection()
            self.is_collecting = False
            
            final_count = self._get_data_count()
            self.logger.info(f"数据采集完成，共收集 {final_count} 个数据点")
            
            return final_count >= self.min_data_points
            
        except Exception as e:
            self.logger.error(f"自动数据采集失败: {e}")
            self.is_collecting = False
            return False

    def _get_data_count(self):
        """获取数据点数量"""
        try:
            data_dir = project_root / "data"
            if not data_dir.exists():
                return 0
            
            count = 0
            for file in data_dir.glob("*.csv"):
                try:
                    import pandas as pd
                    df = pd.read_csv(file)
                    count += len(df)
                except Exception:
                    continue
            
            return count
        except Exception as e:
            self.logger.error(f"获取数据点数量失败: {e}")
            return 0

    def _auto_process_features(self):
        """自动特征处理"""
        try:
            self.logger.info("开始自动特征处理...")
            
            # 处理特征
            result = self.feature_processor.process_all_data()
            
            if result:
                self.logger.info("✓ 特征处理成功")
                return True
            else:
                self.logger.error("特征处理失败")
                return False
                
        except Exception as e:
            self.logger.error(f"自动特征处理失败: {e}")
            return False

    def _auto_train_model(self):
        """自动模型训练"""
        try:
            self.is_training = True
            self.stats['training_sessions'] += 1
            
            self.logger.info("开始自动模型训练...")
            
            # 训练模型
            result = self.model_trainer.train_model()
            
            self.is_training = False
            
            if result:
                self.logger.info("✓ 模型训练成功")
                return True
            else:
                self.logger.error("模型训练失败")
                return False
                
        except Exception as e:
            self.logger.error(f"自动模型训练失败: {e}")
            self.is_training = False
            return False

    def _auto_start_prediction(self):
        """自动启动异常检测"""
        try:
            self.is_predicting = True
            self.stats['prediction_sessions'] += 1
            
            self.logger.info("启动自动异常检测...")
            
            # 启动预测器
            self.predictor.start_prediction()
            
            # 设置异常回调
            def anomaly_callback(user_id, predictions):
                try:
                    self.logger.info(f"检测到异常行为，用户ID: {user_id}")
                    self.logger.info(f"异常预测结果: {predictions}")
                    
                    # 更新统计
                    self.stats['anomalies_detected'] += 1
                    
                    # 发送告警
                    self._handle_anomaly_detection(user_id, predictions)
                    
                except Exception as e:
                    self.logger.error(f"处理异常检测结果失败: {e}")
            
            self.predictor.set_anomaly_callback(anomaly_callback)
            
            self.logger.info("✓ 异常检测已启动")
            
        except Exception as e:
            self.logger.error(f"启动异常检测失败: {e}")
            self.is_predicting = False

    def _handle_anomaly_detection(self, user_id, predictions):
        """处理异常检测结果"""
        try:
            self.logger.info(f"处理异常检测结果: 用户 {user_id}")
            
            # 发送告警
            alert_result = self.alert_service.send_alert(user_id, predictions)
            
            if alert_result:
                self.stats['alerts_sent'] += 1
                self.logger.info("✓ 告警发送成功")
                
                # 处理告警后的操作
                self._handle_post_alert_actions({
                    'user_id': user_id,
                    'predictions': predictions,
                    'timestamp': time.time()
                })
            else:
                self.logger.error("告警发送失败")
                
        except Exception as e:
            self.logger.error(f"处理异常检测结果失败: {e}")

    def _on_retrain_model(self, user_id=None):
        """重新训练模型回调"""
        self.logger.info("收到重新训练模型请求")
        self._restart_workflow()

    def _on_trigger_alert(self, user_id=None):
        """触发告警回调"""
        self.logger.info("收到手动触发告警请求")
        self._manual_trigger_alert()

    def _on_quit_system(self):
        """退出系统回调"""
        self.logger.info("收到退出系统请求")
        self.stop()

    def _restart_workflow(self):
        """重启工作流程"""
        try:
            self.logger.info("重启工作流程...")
            
            # 停止当前流程
            if self.is_collecting:
                self.data_collector.stop_collection()
                self.is_collecting = False
            
            if self.is_training:
                self.is_training = False
            
            if self.is_predicting:
                self.predictor.stop_prediction()
                self.is_predicting = False
            
            # 等待一段时间
            time.sleep(2)
            
            # 重新启动自动工作流程
            self._start_auto_workflow()
            
            self.logger.info("✓ 工作流程重启完成")
            
        except Exception as e:
            self.logger.error(f"重启工作流程失败: {e}")

    def _manual_trigger_alert(self):
        """手动触发告警"""
        try:
            self.logger.info("手动触发告警测试...")
            
            # 创建测试数据
            test_predictions = {
                'anomaly_score': 0.95,
                'confidence': 0.88,
                'features': {
                    'mouse_speed': 150.5,
                    'click_frequency': 2.3,
                    'movement_pattern': 'irregular'
                }
            }
            
            # 发送测试告警
            alert_result = self.alert_service.send_alert("test_user", test_predictions)
            
            if alert_result:
                self.logger.info("✓ 手动告警测试成功")
                self.stats['alerts_sent'] += 1
            else:
                self.logger.error("手动告警测试失败")
                
        except Exception as e:
            self.logger.error(f"手动触发告警失败: {e}")

    def _handle_post_alert_actions(self, anomaly_data):
        """处理告警后的操作"""
        try:
            self.logger.info("执行告警后操作...")
            
            # 记录异常数据
            self._save_anomaly_data(anomaly_data)
            
            # 记录告警统计
            self._log_alert_statistics()
            
            # 在Linux系统上，可以执行一些系统操作
            # 例如：记录日志、发送通知等
            self.logger.info("告警后操作执行完成")
            
        except Exception as e:
            self.logger.error(f"执行告警后操作失败: {e}")

    def _save_anomaly_data(self, anomaly_data):
        """保存异常数据"""
        try:
            # 创建异常数据目录
            anomaly_dir = project_root / "logs" / "anomalies"
            anomaly_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存异常数据
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"anomaly_{timestamp}.json"
            filepath = anomaly_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(anomaly_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"异常数据已保存: {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存异常数据失败: {e}")

    def _log_alert_statistics(self):
        """记录告警统计"""
        try:
            stats_info = {
                'timestamp': time.time(),
                'anomalies_detected': self.stats['anomalies_detected'],
                'alerts_sent': self.stats['alerts_sent'],
                'uptime': time.time() - self.stats['start_time']
            }
            
            self.logger.info(f"告警统计: {stats_info}")
            
        except Exception as e:
            self.logger.error(f"记录告警统计失败: {e}")

    def stop(self):
        """停止系统"""
        try:
            self.logger.info("正在停止系统...")
            
            # 标记系统为停止状态
            self.is_running = False
            
            # 停止各个模块
            if self.is_collecting:
                self.data_collector.stop_collection()
                self.is_collecting = False
            
            if self.is_training:
                self.is_training = False
            
            if self.is_predicting:
                self.predictor.stop_prediction()
                self.is_predicting = False
            
            # 停止用户管理模块
            self.user_manager.stop_keyboard_listener()
            
            # 保存系统状态
            self._save_system_state()
            
            # 显示最终统计
            self._show_final_statistics()
            
            self.logger.info("系统已停止")
            
        except Exception as e:
            self.logger.error(f"停止系统失败: {e}")

    def _save_system_state(self):
        """保存系统状态"""
        try:
            state = {
                'timestamp': time.time(),
                'uptime': time.time() - self.stats['start_time'],
                'stats': self.stats,
                'is_running': self.is_running,
                'is_collecting': self.is_collecting,
                'is_training': self.is_training,
                'is_predicting': self.is_predicting
            }
            
            state_file = project_root / "logs" / "system_state.json"
            state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"系统状态已保存: {state_file}")
            
        except Exception as e:
            self.logger.error(f"保存系统状态失败: {e}")

    def _show_final_statistics(self):
        """显示最终统计"""
        try:
            uptime = time.time() - self.stats['start_time']
            
            self.logger.info("=" * 50)
            self.logger.info("系统运行统计:")
            self.logger.info(f"  运行时间: {uptime:.1f} 秒")
            self.logger.info(f"  数据采集会话: {self.stats['collection_sessions']}")
            self.logger.info(f"  模型训练会话: {self.stats['training_sessions']}")
            self.logger.info(f"  异常检测会话: {self.stats['prediction_sessions']}")
            self.logger.info(f"  检测到的异常: {self.stats['anomalies_detected']}")
            self.logger.info(f"  发送的告警: {self.stats['alerts_sent']}")
            self.logger.info("=" * 50)
            
        except Exception as e:
            self.logger.error(f"显示最终统计失败: {e}")


def main():
    """主函数"""
    try:
        # 创建监控系统实例
        monitor = UOS20BehaviorMonitor()
        
        # 启动系统
        monitor.start()
        
        # 保持主线程运行
        try:
            while monitor.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n收到中断信号，正在停止系统...")
        
        # 停止系统
        monitor.stop()
        
    except Exception as e:
        print(f"系统运行异常: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 