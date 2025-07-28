#!/usr/bin/env python3
"""
用户行为异常检测系统 - Windows版本
简化流程：自动采集 → 自动训练 → 自动检测
"""

import sys
import os
import time
import signal
import threading
import psutil
from pathlib import Path
import traceback
import win32gui
import win32con
import win32api

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

class WindowsBehaviorMonitor:
    """Windows用户行为异常检测系统"""
    
    def __init__(self):
        """初始化系统"""
        self.logger = Logger()
        self.config = ConfigLoader()
        
        self.logger.info("=== Windows用户行为异常检测系统启动 ===")
        self.logger.info("版本: v1.2.0 Windows版")
        
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
            self.logger.debug("初始化用户管理模块...")
            self.user_manager = UserManager()
            
            # 数据采集模块
            self.logger.debug("初始化数据采集模块...")
            self.data_collector = WindowsMouseCollector()
            
            # 特征处理模块
            self.logger.debug("初始化特征处理模块...")
            self.feature_processor = SimpleFeatureProcessor()
            
            # 模型训练模块
            self.logger.debug("初始化模型训练模块...")
            self.model_trainer = SimpleModelTrainer()
            
            # 预测模块
            self.logger.debug("初始化预测模块...")
            self.predictor = SimplePredictor()
            
            # 告警模块
            self.logger.debug("初始化告警模块...")
            self.alert_service = AlertService()
            
            # 注册简化的回调函数
            self._register_callbacks()
            
            self.logger.info("所有核心模块初始化完成")
            
        except Exception as e:
            self.logger.error(f"模块初始化失败: {str(e)}")
            raise

    def _register_callbacks(self):
        """注册简化的回调函数"""
        callbacks = {
            'retrain_model': self._on_retrain_model,
            'trigger_alert': self._on_trigger_alert,
            'quit_system': self._on_quit_system
        }
        
        for callback_name, callback_func in callbacks.items():
            self.user_manager.register_callback(callback_name, callback_func)
            self.logger.debug(f"注册回调函数: {callback_name}")

    def _register_signal_handlers(self):
        """注册信号处理器"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}，正在安全退出...")
        self.stop()

    def start(self):
        """启动系统"""
        try:
            self.logger.info("正在启动Windows用户行为异常检测系统...")
            
            # 启动用户管理（简化快捷键）
            self.user_manager.start_listening()
            self.is_running = True
            
            # 显示系统信息
            self._show_system_info()
            
            # 启动自动流程
            self._start_auto_workflow()
            
            self.logger.info("系统启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"系统启动失败: {str(e)}")
            return False

    def _show_system_info(self):
        """显示系统信息"""
        print("\n" + "="*60)
        print("Windows用户行为异常检测系统 v1.2.0")
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
        print("系统状态: 自动运行中")
        print("="*60 + "\n")

    def _start_auto_workflow(self):
        """启动自动工作流程"""
        self.logger.info("启动自动工作流程...")
        
        # 在后台线程中执行自动流程
        workflow_thread = threading.Thread(target=self._auto_workflow, daemon=True)
        workflow_thread.start()

    def _auto_workflow(self):
        """自动工作流程"""
        try:
            # 1. 自动数据采集
            self.logger.info("=== 步骤1: 自动数据采集 ===")
            if self._auto_collect_data():
                self.logger.info("数据采集完成")
                
                # 2. 自动特征处理
                self.logger.info("=== 步骤2: 自动特征处理 ===")
                if self._auto_process_features():
                    self.logger.info("特征处理完成")
                    
                    # 3. 自动模型训练
                    self.logger.info("=== 步骤3: 自动模型训练 ===")
                    if self._auto_train_model():
                        self.logger.info("模型训练完成")
                        
                        # 4. 自动异常检测
                        self.logger.info("=== 步骤4: 自动异常检测 ===")
                        self._auto_start_prediction()
                    else:
                        self.logger.error("模型训练失败")
                else:
                    self.logger.error("特征处理失败")
            else:
                self.logger.error("数据采集失败")
                
        except Exception as e:
            self.logger.error(f"自动工作流程失败: {str(e)}")

    def _auto_collect_data(self):
        """自动数据采集"""
        try:
            self.current_user_id = self.user_manager.current_user_id
            self.current_session_id = f"session_{int(time.time())}"
            
            self.logger.info(f"开始自动数据采集 - 用户: {self.current_user_id}")
            
            # 启动数据采集
            success = self.data_collector.start_collection(self.current_user_id, self.current_session_id)
            
            if not success:
                return False
            
            self.is_collecting = True
            self.stats['collection_sessions'] += 1
            
            # 等待足够的数据
            start_time = time.time()
            while time.time() - start_time < self.collection_timeout:
                # 检查数据量
                data_count = self._get_data_count()
                if data_count >= self.min_data_points:
                    self.logger.info(f"已采集 {data_count} 个数据点，停止采集")
                    break
                
                time.sleep(5)  # 每5秒检查一次
            else:
                self.logger.warning(f"采集超时，已采集 {self._get_data_count()} 个数据点")
            
            # 停止采集
            self.data_collector.stop_collection()
            self.is_collecting = False
            
            return True
            
        except Exception as e:
            self.logger.error(f"自动数据采集失败: {str(e)}")
            return False

    def _get_data_count(self):
        """获取当前数据量"""
        try:
            from src.utils.config.config_loader import ConfigLoader
            config = ConfigLoader()
            db_path = Path(config.get_paths()['data']) / 'mouse_data.db'
            
            if not db_path.exists():
                return 0
            
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM mouse_events 
                WHERE user_id = ? AND session_id = ?
            """, (self.current_user_id, self.current_session_id))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            self.logger.error(f"获取数据量失败: {str(e)}")
            return 0

    def _auto_process_features(self):
        """自动特征处理"""
        try:
            self.logger.info("开始自动特征处理...")
            
            success = self.feature_processor.process_session_features(
                self.current_user_id, self.current_session_id
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"自动特征处理失败: {str(e)}")
            return False

    def _auto_train_model(self):
        """自动模型训练"""
        try:
            self.logger.info("开始自动模型训练...")
            
            success = self.model_trainer.train_model(self.current_user_id)
            
            return success
            
        except Exception as e:
            self.logger.error(f"自动模型训练失败: {str(e)}")
            return False

    def _auto_start_prediction(self):
        """自动开始预测"""
        try:
            self.logger.info("开始自动异常检测...")
            
            # 设置异常检测回调
            def anomaly_callback(user_id, predictions):
                anomalies = [p for p in predictions if not p['is_normal']]
                if anomalies:
                    self.stats['anomalies_detected'] += len(anomalies)
                    self.stats['alerts_sent'] += len(anomalies)
                    
                    self.logger.warning(f"检测到 {len(anomalies)} 个异常行为")
                    
                    # 发送告警
                    for anomaly in anomalies:
                        self.alert_service.send_alert(
                            user_id=user_id,
                            alert_type="behavior_anomaly",
                            message=f"检测到异常行为: 异常分数 {anomaly['anomaly_score']:.3f}",
                            severity="warning",
                            data=anomaly
                        )
            
            # 启动预测
            success = self.predictor.start_continuous_prediction(
                self.current_user_id, callback=anomaly_callback
            )
            
            if success:
                self.is_predicting = True
                self.stats['prediction_sessions'] += 1
                self.logger.info("自动异常检测已启动")
                return True
            else:
                self.logger.error("自动异常检测启动失败")
                return False
                
        except Exception as e:
            self.logger.error(f"自动开始预测失败: {str(e)}")
            return False

    # 简化的回调函数
    def _on_retrain_model(self):
        """重新训练回调"""
        self.logger.info("用户请求重新采集和训练")
        self._restart_workflow()

    def _on_trigger_alert(self):
        """手动触发告警回调"""
        self.logger.info("用户请求手动触发告警")
        self._manual_trigger_alert()

    def _on_quit_system(self):
        """退出系统回调"""
        self.logger.info("用户请求退出系统")
        self.stop()

    def _restart_workflow(self):
        """重新启动工作流程"""
        try:
            self.logger.info("重新启动工作流程...")
            
            # 停止当前预测
            if self.is_predicting:
                self.predictor.stop_continuous_prediction()
                self.is_predicting = False
            
            # 创建新的用户ID
            new_user_id = f"{self.user_manager.current_username}_retrain_{int(time.time())}"
            self.current_user_id = new_user_id
            
            # 重新启动自动流程
            self._start_auto_workflow()
            
        except Exception as e:
            self.logger.error(f"重新启动工作流程失败: {str(e)}")

    def _manual_trigger_alert(self):
        """手动触发告警"""
        try:
            # 模拟异常数据
            anomaly_data = {
                'anomaly_score': 0.95,
                'probability': 0.05,
                'prediction': 0,
                'is_normal': False
            }
            
            # 发送告警
            self.alert_service.send_alert(
                user_id=self.current_user_id or "manual_test",
                alert_type="behavior_anomaly",
                message="手动触发告警测试",
                severity="warning",
                data=anomaly_data
            )
            
            self.logger.info("手动告警触发完成")
            
        except Exception as e:
            self.logger.error(f"手动触发告警失败: {str(e)}")

    def stop(self):
        """停止系统"""
        try:
            self.logger.info("正在停止系统...")
            
            # 停止各个模块
            if self.is_collecting:
                self.data_collector.stop_collection()
                self.is_collecting = False
            
            if self.is_predicting:
                self.predictor.stop_continuous_prediction()
                self.is_predicting = False
            
            # 停止用户管理
            if hasattr(self, 'user_manager'):
                self.user_manager.stop_listening()
            
            self.is_running = False
            self.logger.info("系统已安全停止")
            
        except Exception as e:
            self.logger.error(f"系统停止失败: {str(e)}")

def main():
    """主函数"""
    monitor = None
    
    try:
        # 创建监控实例
        monitor = WindowsBehaviorMonitor()
        
        # 启动系统
        if monitor.start():
            print("系统启动成功！")
            print("系统将在后台自动运行...")
            print("日志文件: logs/monitor_*.log")
            
            # 主循环
            while monitor.is_running:
                time.sleep(1)
                
        else:
            print("系统启动失败")
            return 1
            
    except KeyboardInterrupt:
        print("\n收到中断信号，正在退出...")
    except Exception as e:
        print(f"系统错误: {str(e)}")
        if monitor:
            monitor.logger.error(f"主程序异常: {str(e)}")
            monitor.logger.debug(f"异常详情: {traceback.format_exc()}")
        return 1
    finally:
        if monitor:
            monitor.stop()
        print("系统已退出")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 