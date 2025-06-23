#!/usr/bin/env python3
"""
简单的用户行为监控主程序
支持快捷键控制不同阶段：数据采集->特征处理->模型训练->在线预测->异常告警
"""

import time
import threading
import signal
import sys
from pathlib import Path
import os
import traceback

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader
from src.core.data_collector.windows_mouse_collector import WindowsMouseCollector
from src.core.feature_engineer.simple_feature_processor import SimpleFeatureProcessor
from src.core.model_trainer.simple_model_trainer import SimpleModelTrainer
from src.core.predictor.simple_predictor import SimplePredictor
from src.core.alert.alert_service import AlertService
from src.core.user_manager import UserManager

class SimpleMonitor:
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigLoader()
        
        self.logger.debug("=== SimpleMonitor 初始化开始 ===")
        self.logger.debug(f"项目根目录: {project_root}")
        self.logger.debug(f"当前工作目录: {os.getcwd()}")
        
        # 初始化各个模块
        self.logger.debug("正在初始化用户管理器...")
        self.user_manager = UserManager()
        
        self.logger.debug("正在初始化特征处理器...")
        self.feature_processor = SimpleFeatureProcessor()
        
        self.logger.debug("正在初始化模型训练器...")
        self.model_trainer = SimpleModelTrainer()
        
        self.logger.debug("正在初始化预测器...")
        self.predictor = SimplePredictor()
        
        self.logger.debug("正在初始化告警服务...")
        self.alert_service = AlertService()
        
        # 运行状态
        self.is_running = False
        self.is_collecting = False
        self.is_predicting = False
        self.current_user_id = None
        
        # 线程
        self.monitoring_thread = None
        
        # 注册用户管理器的回调函数
        self.logger.debug("正在注册用户管理器回调函数...")
        self._register_user_callbacks()
        
        self.logger.info("=== 简单监控系统初始化完成 ===")
        self.logger.debug("=== SimpleMonitor 初始化结束 ===")

    def _register_user_callbacks(self):
        """注册用户管理器的回调函数"""
        self.logger.debug("开始注册回调函数...")
        
        callbacks = {
            'start_collection': self._on_start_collection,
            'stop_collection': self._on_stop_collection,
            'process_features': self._on_process_features,
            'train_model': self._on_train_model,
            'start_prediction': self._on_start_prediction,
            'stop_prediction': self._on_stop_prediction,
            'retrain_model': self._on_retrain_model,
            'show_status': self._on_show_status,
            'quit_system': self._on_quit_system
        }
        
        for callback_name, callback_func in callbacks.items():
            self.logger.debug(f"注册回调函数: {callback_name}")
            self.user_manager.register_callback(callback_name, callback_func)
        
        self.logger.debug("所有回调函数注册完成")

    def _on_start_collection(self, user_id):
        """开始数据采集回调"""
        self.logger.info(f"=== 开始数据采集回调 ===")
        self.logger.debug(f"回调参数 - user_id: {user_id}")
        self.logger.info(f"开始数据采集 - 用户: {user_id}")
        self.start_data_collection(user_id)

    def _on_stop_collection(self, user_id):
        """停止数据采集回调"""
        self.logger.info(f"=== 停止数据采集回调 ===")
        self.logger.debug(f"回调参数 - user_id: {user_id}")
        self.logger.info(f"停止数据采集 - 用户: {user_id}")
        self.stop_data_collection()

    def _on_process_features(self):
        """处理特征回调"""
        self.logger.info(f"=== 处理特征回调 ===")
        self.logger.debug("开始处理特征...")
        self.process_features()

    def _on_train_model(self):
        """训练模型回调"""
        self.logger.info(f"=== 训练模型回调 ===")
        self.logger.debug("开始训练模型...")
        self.train_model()

    def _on_start_prediction(self):
        """开始预测回调"""
        self.logger.info(f"=== 开始预测回调 ===")
        self.logger.debug("开始在线预测...")
        self.start_prediction()

    def _on_stop_prediction(self):
        """停止预测回调"""
        self.logger.info(f"=== 停止预测回调 ===")
        self.logger.debug("停止在线预测...")
        self.stop_prediction()

    def _on_retrain_model(self, user_id):
        """重新训练模型回调"""
        self.logger.info(f"=== 重新训练模型回调 ===")
        self.logger.debug(f"回调参数 - user_id: {user_id}")
        self.logger.info(f"开始重新训练模型 - 用户: {user_id}")
        self.retrain_model(user_id)

    def _on_show_status(self):
        """显示状态回调"""
        self.logger.info(f"=== 显示状态回调 ===")
        self.logger.debug("显示系统状态...")
        self.show_system_status()

    def _on_quit_system(self):
        """退出系统回调"""
        self.logger.info(f"=== 退出系统回调 ===")
        self.logger.debug("收到退出信号，正在关闭...")
        print("\n[系统] 收到退出信号，正在关闭...")
        self.stop_all_services()
        sys.exit(0)

    def setup_signal_handlers(self):
        """设置信号处理器"""
        self.logger.debug("设置信号处理器...")
        
        def signal_handler(signum, frame):
            self.logger.info(f"收到信号 {signum}，正在停止监控...")
            self.logger.debug(f"信号处理器 - signum: {signum}, frame: {frame}")
            self.stop_all_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        self.logger.debug("信号处理器设置完成")

    def start_monitoring(self):
        """开始监控系统"""
        self.logger.info("=== 开始监控系统 ===")
        
        if self.is_running:
            self.logger.warning("监控系统已在运行中")
            return False
        
        # 获取当前用户ID
        self.current_user_id = self.user_manager.get_current_user_id()
        self.logger.debug(f"当前用户ID: {self.current_user_id}")
        
        # 设置信号处理器
        self.setup_signal_handlers()
        
        # 启动用户管理器的键盘监听
        self.logger.debug("启动键盘监听器...")
        self.user_manager.start_keyboard_listener()
        
        # 设置运行状态
        self.is_running = True
        
        self.logger.info(f"监控系统启动成功，当前用户: {self.current_user_id}")
        self.logger.debug("=== 监控系统启动完成 ===")
        return True

    def stop_monitoring(self):
        """停止监控系统"""
        self.logger.info("=== 停止监控系统 ===")
        
        if not self.is_running:
            self.logger.debug("监控系统未在运行")
            return
        
        self.logger.info("正在停止监控系统...")
        
        # 停止所有服务
        self.stop_all_services()
        
        # 停止用户管理器
        self.logger.debug("停止键盘监听器...")
        self.user_manager.stop_keyboard_listener()
        
        # 设置运行状态
        self.is_running = False
        
        self.logger.info("监控系统已停止")
        self.logger.debug("=== 监控系统停止完成 ===")

    def start_data_collection(self, user_id=None):
        """开始数据采集"""
        self.logger.info("=== 开始数据采集 ===")
        self.logger.debug(f"参数 - user_id: {user_id}, is_collecting: {self.is_collecting}")
        
        if self.is_collecting:
            self.logger.warning("数据采集已在运行中")
            return False
        
        if user_id is None:
            user_id = self.current_user_id
            self.logger.debug(f"使用当前用户ID: {user_id}")
        
        try:
            # 初始化鼠标采集器
            self.logger.debug("初始化鼠标采集器...")
            self.mouse_collector = WindowsMouseCollector(user_id)
            
            # 启动数据采集
            self.logger.debug("启动数据采集...")
            if self.mouse_collector.start_collection():
                self.is_collecting = True
                self.current_user_id = user_id
                self.logger.info(f"数据采集启动成功 - 用户: {user_id}")
                print(f"[系统] 数据采集已启动 - 用户: {user_id}")
                self.logger.debug("=== 数据采集启动完成 ===")
                return True
            else:
                self.logger.error("数据采集启动失败")
                return False
                
        except Exception as e:
            self.logger.error(f"启动数据采集失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            return False

    def stop_data_collection(self):
        """停止数据采集"""
        self.logger.info("=== 停止数据采集 ===")
        self.logger.debug(f"当前状态 - is_collecting: {self.is_collecting}")
        
        if not self.is_collecting:
            self.logger.warning("数据采集未在运行")
            return
        
        try:
            if self.mouse_collector:
                self.logger.debug("停止鼠标采集器...")
                self.mouse_collector.stop_collection()
                self.is_collecting = False
                self.logger.info("数据采集已停止")
                print("[系统] 数据采集已停止")
                self.logger.debug("=== 数据采集停止完成 ===")
                
        except Exception as e:
            self.logger.error(f"停止数据采集失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")

    def process_features(self):
        """处理特征"""
        self.logger.info("=== 处理特征 ===")
        self.logger.debug(f"当前用户ID: {self.current_user_id}")
        
        try:
            if not self.current_user_id:
                self.logger.error("没有当前用户ID")
                print("[系统] 错误: 没有当前用户ID")
                return False
            
            # 处理当前会话的特征
            session_id = self.mouse_collector.session_id if self.mouse_collector else None
            self.logger.debug(f"会话ID: {session_id}")
            
            if not session_id:
                self.logger.error("没有会话ID")
                print("[系统] 错误: 没有会话ID")
                return False
            
            self.logger.debug("开始处理会话特征...")
            success = self.feature_processor.process_session_features(
                self.current_user_id, session_id
            )
            
            if success:
                self.logger.info("特征处理完成")
                print("[系统] 特征处理完成")
                self.logger.debug("=== 特征处理完成 ===")
                return True
            else:
                self.logger.error("特征处理失败")
                print("[系统] 特征处理失败")
                return False
                
        except Exception as e:
            self.logger.error(f"特征处理出错: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            print(f"[系统] 特征处理出错: {str(e)}")
            return False

    def train_model(self):
        """训练模型"""
        self.logger.info("=== 训练模型 ===")
        self.logger.debug(f"当前用户ID: {self.current_user_id}")
        
        try:
            if not self.current_user_id:
                self.logger.error("没有当前用户ID")
                print("[系统] 错误: 没有当前用户ID")
                return False
            
            self.logger.debug("开始训练用户模型...")
            success = self.model_trainer.train_user_model(self.current_user_id)
            
            if success:
                self.logger.info("模型训练完成")
                print("[系统] 模型训练完成")
                self.logger.debug("=== 模型训练完成 ===")
                return True
            else:
                self.logger.error("模型训练失败")
                print("[系统] 模型训练失败")
                return False
                
        except Exception as e:
            self.logger.error(f"模型训练出错: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            print(f"[系统] 模型训练出错: {str(e)}")
            return False

    def start_prediction(self):
        """开始在线预测"""
        self.logger.info("=== 开始在线预测 ===")
        self.logger.debug(f"当前状态 - is_predicting: {self.is_predicting}")
        
        if self.is_predicting:
            self.logger.warning("在线预测已在运行中")
            return False
        
        try:
            # 设置异常检测回调
            def anomaly_callback(user_id, predictions):
                self.logger.debug(f"异常检测回调 - user_id: {user_id}, predictions_count: {len(predictions)}")
                anomalies = [p for p in predictions if not p['is_normal']]
                if anomalies:
                    self.logger.warning(f"检测到 {len(anomalies)} 个异常行为")
                    self.logger.debug(f"异常详情: {anomalies}")
                    print(f"[系统] 检测到 {len(anomalies)} 个异常行为")
                    # 发送告警
                    for anomaly in anomalies:
                        self.alert_service.send_alert(
                            user_id=user_id,
                            alert_type="behavior_anomaly",
                            message=f"检测到异常行为: 异常分数 {anomaly['anomaly_score']:.3f}",
                            severity="warning",
                            data=anomaly
                        )
            
            # 启动连续预测
            self.logger.debug("启动连续预测...")
            success = self.predictor.start_continuous_prediction(
                self.current_user_id, 
                callback=anomaly_callback
            )
            
            if success:
                self.is_predicting = True
                self.logger.info("在线预测启动成功")
                print("[系统] 在线预测已启动")
                self.logger.debug("=== 在线预测启动完成 ===")
                return True
            else:
                self.logger.error("在线预测启动失败")
                print("[系统] 在线预测启动失败")
                return False
                
        except Exception as e:
            self.logger.error(f"启动在线预测出错: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            print(f"[系统] 启动在线预测出错: {str(e)}")
            return False

    def stop_prediction(self):
        """停止在线预测"""
        self.logger.info("=== 停止在线预测 ===")
        self.logger.debug(f"当前状态 - is_predicting: {self.is_predicting}")
        
        if not self.is_predicting:
            self.logger.warning("在线预测未在运行")
            return
        
        try:
            self.logger.debug("停止连续预测...")
            self.predictor.stop_continuous_prediction()
            self.is_predicting = False
            self.logger.info("在线预测已停止")
            print("[系统] 在线预测已停止")
            self.logger.debug("=== 在线预测停止完成 ===")
            
        except Exception as e:
            self.logger.error(f"停止在线预测失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")

    def retrain_model(self, user_id):
        """重新训练模型"""
        self.logger.info("=== 重新训练模型 ===")
        self.logger.debug(f"参数 - user_id: {user_id}")
        
        try:
            self.logger.info(f"开始重新训练用户 {user_id} 的模型")
            
            # 处理所有会话的特征
            self.logger.debug("处理所有用户会话的特征...")
            success_count = self.feature_processor.process_all_user_sessions(user_id)
            self.logger.debug(f"成功处理 {success_count} 个会话")
            
            if success_count > 0:
                # 重新训练模型
                self.logger.debug("重新训练模型...")
                success = self.model_trainer.train_user_model(user_id)
                if success:
                    self.logger.info("模型重新训练完成")
                    print(f"[系统] 用户 {user_id} 模型重新训练完成")
                    self.logger.debug("=== 重新训练完成 ===")
                    return True
            
            self.logger.error("模型重新训练失败")
            print(f"[系统] 用户 {user_id} 模型重新训练失败")
            return False
            
        except Exception as e:
            self.logger.error(f"重新训练模型出错: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            print(f"[系统] 重新训练模型出错: {str(e)}")
            return False

    def stop_all_services(self):
        """停止所有服务"""
        self.logger.info("=== 停止所有服务 ===")
        
        # 停止数据采集
        self.logger.debug("停止数据采集...")
        self.stop_data_collection()
        
        # 停止预测
        self.logger.debug("停止预测...")
        self.stop_prediction()
        
        self.logger.debug("=== 所有服务停止完成 ===")

    def show_system_status(self):
        """显示系统状态"""
        self.logger.info("=== 显示系统状态 ===")
        
        status = {
            'is_running': self.is_running,
            'current_user_id': self.current_user_id,
            'is_collecting': self.is_collecting,
            'is_predicting': self.is_predicting,
            'session_id': self.mouse_collector.session_id if self.mouse_collector else None
        }
        
        self.logger.debug(f"系统状态: {status}")
        
        # 获取异常统计
        if self.current_user_id:
            try:
                anomaly_stats = self.predictor.get_anomaly_statistics(self.current_user_id)
                status['anomaly_stats'] = anomaly_stats
                self.logger.debug(f"异常统计: {anomaly_stats}")
            except Exception as e:
                self.logger.debug(f"获取异常统计失败: {str(e)}")
        
        print("\n=== 系统状态 ===")
        print(f"运行状态: {'运行中' if status['is_running'] else '已停止'}")
        print(f"当前用户: {status['current_user_id']}")
        print(f"数据采集: {'运行中' if status['is_collecting'] else '已停止'}")
        print(f"在线预测: {'运行中' if status['is_predicting'] else '已停止'}")
        print(f"会话ID: {status['session_id']}")
        
        if 'anomaly_stats' in status and status['anomaly_stats']:
            stats = status['anomaly_stats']
            print(f"异常统计 (24小时): {stats.get('anomaly_count', 0)}/{stats.get('total_count', 0)} ({stats.get('anomaly_rate', 0):.2f}%)")
        
        print("================\n")
        self.logger.debug("=== 系统状态显示完成 ===")

def main():
    """主函数"""
    print("=== 用户行为监控系统 ===")
    print("快捷键说明:")
    print("  Ctrl+Alt+C: 开始数据采集")
    print("  Ctrl+Alt+S: 停止数据采集")
    print("  Ctrl+Alt+F: 处理特征")
    print("  Ctrl+Alt+T: 训练模型")
    print("  Ctrl+Alt+P: 开始预测")
    print("  Ctrl+Alt+X: 停止预测")
    print("  Ctrl+Alt+R: 重新训练")
    print("  Ctrl+Alt+I: 显示状态")
    print("  Ctrl+Alt+Q: 退出系统")
    print()
    print("按 Ctrl+C 退出")
    print()
    
    # 创建监控实例
    monitor = SimpleMonitor()
    
    try:
        # 启动监控系统
        if monitor.start_monitoring():
            print("监控系统启动成功！")
            print("当前用户:", monitor.current_user_id)
            print("请使用快捷键控制各个阶段...")
            print()
            
            # 主循环
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n正在退出...")
    except Exception as e:
        print(f"系统错误: {str(e)}")
        monitor.logger.error(f"主程序异常: {str(e)}")
        monitor.logger.debug(f"异常详情: {traceback.format_exc()}")
    finally:
        monitor.stop_monitoring()
        print("系统已退出")

if __name__ == "__main__":
    main() 