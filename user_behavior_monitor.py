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

# 检查Windows API是否可用
WINDOWS_AVAILABLE = True
try:
    import win32api
    import win32con
except ImportError:
    WINDOWS_AVAILABLE = False
    print("警告: Windows API 不可用，无法执行强制登出或锁屏操作。")


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
            
            # 数据采集模块 - 延迟创建，需要时再初始化
            self.logger.debug("数据采集模块将在需要时初始化...")
            self.data_collector = None
            
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
            self.user_manager.start_keyboard_listener()
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
                
                # 检查数据量是否足够
                data_count = self._get_data_count()
                self.logger.info(f"当前数据量: {data_count} 个数据点")
                
                if data_count < self.min_data_points:
                    self.logger.warning(f"数据量不足 ({data_count} < {self.min_data_points})，跳过特征处理")
                    self.logger.info("建议：继续使用鼠标，系统将自动重新采集数据")
                    return False
                
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
            
            self.logger.info(f"开始自动数据采集 - 用户: {self.current_user_id}")
            
            # 创建数据采集器（如果还没有创建）
            if self.data_collector is None:
                self.logger.debug("创建数据采集器...")
                self.data_collector = WindowsMouseCollector(self.current_user_id)
            
            # 启动数据采集
            success = self.data_collector.start_collection()
            
            if not success:
                return False
            
            # 获取数据采集器生成的会话ID
            self.current_session_id = self.data_collector.session_id
            self.logger.info(f"使用会话ID: {self.current_session_id}")
            
            self.is_collecting = True
            self.stats['collection_sessions'] += 1
            
            # 等待足够的数据
            start_time = time.time()
            max_wait_time = self.collection_timeout * 2  # 增加最大等待时间
            
            while time.time() - start_time < max_wait_time:
                # 检查数据量
                data_count = self._get_data_count()
                self.logger.debug(f"当前数据量: {data_count}/{self.min_data_points}")
                
                if data_count >= self.min_data_points:
                    self.logger.info(f"✅ 已采集 {data_count} 个数据点，达到要求")
                    break
                
                # 每10秒显示一次进度
                elapsed = time.time() - start_time
                if int(elapsed) % 10 == 0:
                    self.logger.info(f"⏳ 数据采集中... ({data_count}/{self.min_data_points}) - 已等待 {int(elapsed)} 秒")
                
                time.sleep(2)  # 每2秒检查一次
            else:
                self.logger.warning(f"⚠️ 采集超时，已采集 {self._get_data_count()} 个数据点")
                self.logger.info("💡 建议：继续使用鼠标，系统将自动重新采集")
            
            # 停止采集
            self.data_collector.stop_collection()
            self.is_collecting = False
            
            # 最终检查数据量
            final_count = self._get_data_count()
            if final_count >= self.min_data_points:
                self.logger.info(f"✅ 数据采集完成，共 {final_count} 个数据点")
                return True
            else:
                self.logger.warning(f"⚠️ 数据量不足 ({final_count} < {self.min_data_points})")
                return False
            
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
            
            success = self.model_trainer.train_user_model(self.current_user_id)
            
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
    def _on_retrain_model(self, user_id=None):
        """重新训练回调"""
        self.logger.info("用户请求重新采集和训练")
        self._restart_workflow()

    def _on_trigger_alert(self, user_id=None):
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
            # 记录手动触发告警的开始
            self.logger.info("=== 手动触发告警测试开始 ===")
            self.logger.info(f"当前用户ID: {self.current_user_id}")
            self.logger.info(f"当前会话ID: {self.user_manager.get_current_user_info().get('session_id', 'unknown')}")
            
            # 模拟异常数据
            anomaly_data = {
                'anomaly_score': 0.95,
                'probability': 0.05,
                'prediction': 0,
                'is_normal': False,
                'trigger_type': 'manual_test',
                'timestamp': time.time()
            }
            
            # 发送告警
            alert_success = self.alert_service.send_alert(
                user_id=self.current_user_id or "manual_test",
                alert_type="behavior_anomaly",
                message="手动触发告警测试 - 用户行为异常检测",
                severity="warning",
                data=anomaly_data
            )
            
            if alert_success:
                self.logger.info("✅ 手动告警触发成功")
                self.logger.info("📋 告警详情:")
                self.logger.info(f"   - 异常分数: {anomaly_data['anomaly_score']:.3f}")
                self.logger.info(f"   - 触发类型: {anomaly_data['trigger_type']}")
                self.logger.info(f"   - 时间戳: {datetime.fromtimestamp(anomaly_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 检查是否需要执行系统操作
                if self.alert_service.enable_system_actions:
                    self.logger.info("🔒 系统将根据配置执行安全操作（锁屏/登出）")
                    self._handle_post_alert_actions(anomaly_data)
                else:
                    self.logger.info("⚠️ 系统操作已禁用，仅记录告警")
                
                # 记录告警统计
                self._log_alert_statistics()
                
            else:
                self.logger.warning("⚠️ 手动告警触发失败或处于冷却期")
            
            self.logger.info("=== 手动触发告警测试完成 ===")
            
        except Exception as e:
            self.logger.error(f"手动触发告警失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")

    def _handle_post_alert_actions(self, anomaly_data):
        """处理告警后的系统操作"""
        try:
            anomaly_score = anomaly_data.get('anomaly_score', 0)
            
            # 检查是否需要强制登出
            force_logout_enabled = self.config.get_alert_config().get('force_logout', False)
            
            if force_logout_enabled and anomaly_score >= 0.9:
                self.logger.warning("🚨 异常分数过高，将执行强制登出")
                self._force_user_logout()
            elif anomaly_score >= self.alert_service.lock_screen_threshold:
                self.logger.warning("🔒 异常分数达到锁屏阈值，将执行锁屏")
                # 锁屏操作已在告警服务中处理
            else:
                self.logger.info("📝 仅记录告警，不执行系统操作")
                
        except Exception as e:
            self.logger.error(f"处理告警后操作失败: {str(e)}")

    def _force_user_logout(self):
        """强制用户登出"""
        try:
            self.logger.warning("🔄 开始强制用户登出流程...")
            
            # 1. 停止数据采集
            if self.is_collecting and self.data_collector:
                self.logger.info("停止数据采集...")
                self.data_collector.stop_collection()
                self.is_collecting = False
            
            # 2. 停止预测
            if self.is_predicting:
                self.logger.info("停止异常检测...")
                self.predictor.stop_continuous_prediction()
                self.is_predicting = False
            
            # 3. 保存当前状态
            self.logger.info("保存系统状态...")
            self._save_system_state()
            
            # 4. 执行登出操作
            if WINDOWS_AVAILABLE:
                self.logger.warning("🚪 执行Windows强制登出...")
                try:
                    # 使用Windows API强制登出
                    import win32api
                    import win32con
                    win32api.ExitWindowsEx(win32con.EWX_LOGOFF, 0)
                    self.logger.info("Windows强制登出命令已发送")
                except Exception as e:
                    self.logger.error(f"Windows强制登出失败: {str(e)}")
                    # 备用方案：锁屏
                    self.alert_service._lock_screen()
            else:
                self.logger.warning("🔒 无法执行强制登出，改为锁屏")
                self.alert_service._lock_screen()
            
            # 5. 记录登出日志
            self.logger.warning("📋 强制登出完成，系统状态:")
            self.logger.warning(f"   - 数据采集: {'运行中' if self.is_collecting else '已停止'}")
            self.logger.warning(f"   - 异常检测: {'运行中' if self.is_predicting else '已停止'}")
            self.logger.warning(f"   - 系统运行: {'运行中' if self.is_running else '已停止'}")
            
        except Exception as e:
            self.logger.error(f"强制用户登出失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")

    def _save_system_state(self):
        """保存系统状态"""
        try:
            state = {
                'timestamp': time.time(),
                'user_id': self.current_user_id,
                'session_id': self.user_manager.get_current_user_info().get('session_id'),
                'is_collecting': self.is_collecting,
                'is_predicting': self.is_predicting,
                'is_running': self.is_running,
                'data_count': self._get_data_count() if self.data_collector else 0,
                'last_alert_time': time.time()
            }
            
            # 保存到文件
            state_file = Path("data/system_state.json")
            state_file.parent.mkdir(exist_ok=True)
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"系统状态已保存到: {state_file}")
            
        except Exception as e:
            self.logger.error(f"保存系统状态失败: {str(e)}")

    def _log_alert_statistics(self):
        """记录告警统计信息"""
        try:
            if self.current_user_id:
                stats = self.alert_service.get_alert_statistics(self.current_user_id, hours=1)
                if stats:
                    self.logger.info("📊 最近1小时告警统计:")
                    self.logger.info(f"   - 总告警数: {stats.get('total_alerts', 0)}")
                    for alert_type, count in stats.get('alerts_by_type', {}).items():
                        self.logger.info(f"   - {alert_type}: {count} 条")
                        
        except Exception as e:
            self.logger.error(f"记录告警统计失败: {str(e)}")

    def stop(self):
        """停止系统"""
        try:
            self.logger.info("正在停止系统...")
            
            # 停止各个模块
            if self.is_collecting and self.data_collector:
                self.data_collector.stop_collection()
                self.is_collecting = False
            
            if self.is_predicting:
                self.predictor.stop_continuous_prediction()
                self.is_predicting = False
            
            # 停止用户管理
            if hasattr(self, 'user_manager'):
                self.user_manager.stop_keyboard_listener()
            
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