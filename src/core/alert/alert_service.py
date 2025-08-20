import time
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import sys
import platform
import subprocess
import threading
import os

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader

# Windows API导入
try:
    import win32api
    import win32con
    import win32gui
    import win32security
    import ctypes
    from ctypes import wintypes
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    print("警告: Windows API不可用")

# GUI库导入
try:
    import tkinter as tk
    from tkinter import messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("警告: tkinter不可用")

class AlertService:
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigLoader()
        self.db_path = Path(self.config.get_paths()['data']) / 'mouse_data.db'
        
        # 告警配置
        self.alert_config = self.config.get_alert_config()
        self.enable_system_actions = self.alert_config.get('enable_system_actions', True)
        self.lock_screen_threshold = self.alert_config.get('lock_screen_threshold', 0.8)
        self.alert_cooldown = self.alert_config.get('alert_cooldown', 60)  # 60秒冷却时间
        self.show_warning_dialog = self.alert_config.get('show_warning_dialog', True)
        self.warning_duration = self.alert_config.get('warning_duration', 10)  # 警告显示时间（秒）
        
        # 新增：多种告警方式配置
        self.enable_console_alert = self.alert_config.get('enable_console_alert', True)
        self.enable_sound_alert = self.alert_config.get('enable_sound_alert', True)
        self.enable_log_alert = self.alert_config.get('enable_log_alert', True)
        self.enable_system_notification = self.alert_config.get('enable_system_notification', True)
        self.enable_file_alert = self.alert_config.get('enable_file_alert', True) # 新增文件告警
        
        # 检查当前运行环境（按需求：不再检测GUI环境，强制允许弹窗）
        self.is_system_user = os.getuid() == 0 if hasattr(os, 'getuid') else False
        self.has_display = True
        self.can_show_gui = True
        
        # 告警状态
        self.last_alert_time = {}
        self.alert_count = {}
        
        self.logger.info("告警服务初始化完成")
        self.logger.info(f"系统操作: {'启用' if self.enable_system_actions else '禁用'}")
        self.logger.info(f"锁屏阈值: {self.lock_screen_threshold}")
        self.logger.info(f"弹窗警告: {'启用' if self.show_warning_dialog else '禁用'}")
        self.logger.info(f"警告持续时间: {self.warning_duration}秒")
        self.logger.info(f"当前用户: {'system用户' if self.is_system_user else '普通用户'}")
        self.logger.info(f"显示环境: 可用 (强制)")
        self.logger.info(f"GUI可用: 是 (强制)")
        self.logger.info(f"控制台告警: {'启用' if self.enable_console_alert else '禁用'}")
        self.logger.info(f"声音告警: {'启用' if self.enable_sound_alert else '禁用'}")
        self.logger.info(f"日志告警: {'启用' if self.enable_log_alert else '禁用'}")
        self.logger.info(f"文件告警: {'启用' if self.enable_file_alert else '禁用'}")

    def send_alert(self, user_id, alert_type, message, severity="warning", data=None, bypass_cooldown=False):
        """发送告警"""
        try:
            current_time = time.time()
            
            # 检查冷却时间（手动触发可以绕过）
            if not bypass_cooldown and user_id in self.last_alert_time:
                time_since_last = current_time - self.last_alert_time[user_id]
                if time_since_last < self.alert_cooldown:
                    self.logger.debug(f"告警冷却中，剩余 {self.alert_cooldown - time_since_last:.1f} 秒")
                    return False
            
            # 记录告警
            self.last_alert_time[user_id] = current_time
            self.alert_count[user_id] = self.alert_count.get(user_id, 0) + 1
            
            # 保存告警到数据库
            self._save_alert_to_db(user_id, alert_type, message, severity, data)
            
            # 多种告警方式
            self._send_multiple_alerts(user_id, alert_type, message, severity, data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"发送告警失败: {str(e)}")
            return False

    def _send_multiple_alerts(self, user_id, alert_type, message, severity, data):
        """发送多种形式的告警"""
        try:
            # 1. 控制台告警（如果控制台可见）
            if self.enable_console_alert and self._is_console_visible():
                self._send_console_alert(user_id, alert_type, message, severity, data)
            
            # 2. 日志告警（始终可用）
            if self.enable_log_alert:
                self._send_log_alert(user_id, alert_type, message, severity, data)
            
            # 3. 文件告警（写入专门的告警文件）
            if self.enable_file_alert:
                self._send_file_alert(user_id, alert_type, message, severity, data)
            
            # 4. 声音告警
            if self.enable_sound_alert:
                self._send_sound_alert(severity)
            
            # 5. 系统通知
            if self.enable_system_notification:
                self._send_system_notification(user_id, alert_type, message, severity)
            
            # 6. GUI弹窗（按需：不检测环境，直接弹窗）
            if self.show_warning_dialog:
                self._send_gui_alert(user_id, alert_type, message, severity, data)
            
            # 7. 执行系统操作
            if self.enable_system_actions:
                self._execute_system_action(alert_type, severity, data)
            
        except Exception as e:
            self.logger.error(f"发送多种告警失败: {str(e)}")

    def _is_console_visible(self):
        """检查控制台是否可见"""
        try:
            # 检查是否在交互式环境中
            if hasattr(sys, 'ps1'):
                return True
            
            # 检查是否有TTY
            if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
                return True
            
            # 检查是否在后台运行
            if platform.system() == 'Windows':
                # Windows下检查是否有控制台窗口
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    return kernel32.GetConsoleWindow() != 0
                except:
                    return False
            else:
                # Linux/Mac下检查进程组
                try:
                    return os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno())
                except:
                    return False
                    
        except Exception:
            return False

    def _send_file_alert(self, user_id, alert_type, message, severity, data):
        """发送文件告警"""
        try:
            # 创建告警文件目录
            alert_dir = Path('logs/alerts')
            alert_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成告警文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            alert_file = alert_dir / f"alert_{timestamp}.txt"
            
            # 创建告警内容
            alert_content = f"""
================================================================================
🚨 安全告警 - {severity.upper()}
================================================================================
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
用户: {user_id}
类型: {alert_type}
消息: {message}
异常分数: {data.get('anomaly_score', 'N/A') if data else 'N/A'}
严重程度: {severity}
================================================================================

⚠️  请立即检查系统安全状态
⚠️  此告警已记录到文件: {alert_file}
⚠️  如需查看详细日志，请检查: logs/monitor_*.log

================================================================================
"""
            
            # 写入告警文件
            with open(alert_file, 'w', encoding='utf-8') as f:
                f.write(alert_content)
            
            # 同时写入实时告警文件
            realtime_alert_file = alert_dir / 'realtime_alerts.txt'
            with open(realtime_alert_file, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {severity.upper()}: {message}\n")
            
            self.logger.info(f"告警已写入文件: {alert_file}")
            
        except Exception as e:
            self.logger.error(f"文件告警失败: {str(e)}")

    def _send_system_log_alert(self, user_id, alert_type, message, severity, data):
        """发送系统日志告警"""
        try:
            if platform.system() == 'Windows':
                # Windows系统日志
                self._send_windows_event_log(user_id, alert_type, message, severity)
            else:
                # Linux/Mac系统日志
                self._send_syslog_alert(user_id, alert_type, message, severity)
                
        except Exception as e:
            self.logger.error(f"系统日志告警失败: {str(e)}")

    def _send_windows_event_log(self, user_id, alert_type, message, severity):
        """发送Windows事件日志"""
        try:
            if WINDOWS_AVAILABLE:
                import win32evtlog
                import win32evtlogutil
                
                # 映射严重程度到Windows事件级别
                severity_map = {
                    'critical': win32evtlog.EVENTLOG_ERROR_TYPE,
                    'warning': win32evtlog.EVENTLOG_WARNING_TYPE,
                    'info': win32evtlog.EVENTLOG_INFORMATION_TYPE
                }
                
                event_type = severity_map.get(severity.lower(), win32evtlog.EVENTLOG_WARNING_TYPE)
                
                # 创建事件日志消息
                event_msg = f"用户行为监控告警 - 用户: {user_id}, 类型: {alert_type}, 消息: {message}"
                
                # 写入事件日志
                win32evtlogutil.ReportEvent(
                    'UserBehaviorMonitor',
                    1001,  # 事件ID
                    eventType=event_type,
                    strings=[event_msg]
                )
                
        except Exception as e:
            self.logger.error(f"Windows事件日志失败: {str(e)}")

    def _send_syslog_alert(self, user_id, alert_type, message, severity):
        """发送syslog告警"""
        try:
            import subprocess
            
            # 映射严重程度到syslog级别
            severity_map = {
                'critical': 'emerg',
                'warning': 'warning',
                'info': 'info'
            }
            
            log_level = severity_map.get(severity.lower(), 'warning')
            
            # 使用logger命令发送到syslog
            log_message = f"UserBehaviorMonitor[{os.getpid()}]: 用户: {user_id}, 类型: {alert_type}, 消息: {message}"
            
            subprocess.run([
                'logger', 
                '-p', f'user.{log_level}',
                log_message
            ], check=False)
            
        except Exception as e:
            self.logger.error(f"syslog告警失败: {str(e)}")

    def _send_console_alert(self, user_id, alert_type, message, severity, data):
        """发送控制台告警"""
        try:
            # 创建醒目的控制台告警
            alert_border = "=" * 80
            alert_header = f"🚨 安全告警 - {severity.upper()}"
            alert_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            console_message = f"""
{alert_border}
{alert_header}
{alert_border}
时间: {alert_time}
用户: {user_id}
类型: {alert_type}
消息: {message}
异常分数: {data.get('anomaly_score', 'N/A') if data else 'N/A'}
{alert_border}
"""
            
            # 根据严重程度使用不同的颜色（如果支持）
            if severity.lower() == 'critical':
                print(f"\033[91m{console_message}\033[0m")  # 红色
            elif severity.lower() == 'warning':
                print(f"\033[93m{console_message}\033[0m")  # 黄色
            else:
                print(console_message)
                
        except Exception as e:
            self.logger.error(f"控制台告警失败: {str(e)}")

    def _send_log_alert(self, user_id, alert_type, message, severity, data):
        """发送日志告警"""
        try:
            log_message = f"告警 - 用户: {user_id}, 类型: {alert_type}, 严重程度: {severity}, 消息: {message}"
            if data:
                log_message += f", 数据: {json.dumps(data, ensure_ascii=False)}"
            
            self.logger.warning(log_message)
            
        except Exception as e:
            self.logger.error(f"日志告警失败: {str(e)}")

    def _send_sound_alert(self, severity):
        """发送声音告警"""
        try:
            # 根据严重程度播放不同的声音
            if severity.lower() == 'critical':
                # 播放紧急声音
                self._play_sound('critical')
            elif severity.lower() == 'warning':
                # 播放警告声音
                self._play_sound('warning')
            else:
                # 播放普通告警声音
                self._play_sound('alert')
                
        except Exception as e:
            self.logger.error(f"声音告警失败: {str(e)}")

    def _play_sound(self, sound_type):
        """播放声音"""
        try:
            if platform.system() == 'Windows':
                # Windows系统使用内置声音
                if sound_type == 'critical':
                    import winsound
                    winsound.MessageBeep(winsound.MB_ICONHAND)
                elif sound_type == 'warning':
                    import winsound
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                else:
                    import winsound
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
            else:
                # Linux/Mac系统使用命令行工具
                if sound_type == 'critical':
                    subprocess.run(['echo', '-e', '\a\a\a'], check=False)
                elif sound_type == 'warning':
                    subprocess.run(['echo', '-e', '\a\a'], check=False)
                else:
                    subprocess.run(['echo', '-e', '\a'], check=False)
                    
        except Exception as e:
            self.logger.error(f"播放声音失败: {str(e)}")

    def _send_system_notification(self, user_id, alert_type, message, severity):
        """发送系统通知"""
        try:
            if platform.system() == 'Windows':
                # Windows系统通知
                if WINDOWS_AVAILABLE:
                    self._send_windows_notification(user_id, alert_type, message, severity)
            else:
                # Linux/Mac系统通知
                self._send_linux_notification(user_id, alert_type, message, severity)
                
        except Exception as e:
            self.logger.error(f"系统通知失败: {str(e)}")

    def _send_windows_notification(self, user_id, alert_type, message, severity):
        """发送Windows系统通知"""
        try:
            if WINDOWS_AVAILABLE:
                # 使用Windows API发送通知
                title = f"安全告警 - {severity.upper()}"
                content = f"用户: {user_id}\n类型: {alert_type}\n消息: {message}"
                
                # 这里可以集成Windows通知API
                # 暂时使用简单的消息框
                if GUI_AVAILABLE:
                    try:
                        import tkinter as tk
                        from tkinter import messagebox
                        root = tk.Tk()
                        root.withdraw()  # 隐藏主窗口
                        messagebox.showwarning(title, content)
                        root.destroy()
                    except:
                        pass
                        
        except Exception as e:
            self.logger.error(f"Windows通知失败: {str(e)}")

    def _send_linux_notification(self, user_id, alert_type, message, severity):
        """发送Linux系统通知"""
        try:
            # 尝试使用notify-send命令
            title = f"安全告警 - {severity.upper()}"
            content = f"用户: {user_id}\n类型: {alert_type}\n消息: {message}"
            
            # 根据严重程度设置不同的图标
            if severity.lower() == 'critical':
                icon = 'dialog-error'
            elif severity.lower() == 'warning':
                icon = 'dialog-warning'
            else:
                icon = 'dialog-information'
            
            subprocess.run([
                'notify-send', 
                '--icon', icon,
                '--urgency', 'critical' if severity.lower() == 'critical' else 'normal',
                title, 
                content
            ], check=False)
            
        except Exception as e:
            self.logger.error(f"Linux通知失败: {str(e)}")

    def _send_gui_alert(self, user_id, alert_type, message, severity, data):
        """发送GUI弹窗告警"""
        try:
            if self.can_show_gui and data and 'anomaly_score' in data:
                self._show_warning_dialog(data['anomaly_score'])
            else:
                self.logger.info("GUI告警跳过：环境不支持或数据不完整")
                
        except Exception as e:
            self.logger.error(f"GUI告警失败: {str(e)}")

    def _save_alert_to_db(self, user_id, alert_type, message, severity, data):
        """保存告警到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建告警表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    data TEXT,
                    timestamp REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 插入告警记录
            cursor.execute('''
                INSERT INTO alerts (user_id, alert_type, message, severity, data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                alert_type,
                message,
                severity,
                json.dumps(data) if data else None,
                time.time()
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"告警已保存到数据库")
            
        except Exception as e:
            self.logger.error(f"保存告警到数据库失败: {str(e)}")

    def _execute_system_action(self, alert_type, severity, data):
        """执行系统操作"""
        try:
            if alert_type == "behavior_anomaly":
                # 检查异常分数是否达到锁屏阈值
                anomaly_score = data.get('anomaly_score', 0) if data else 0
                
                if anomaly_score >= self.lock_screen_threshold:
                    self.logger.warning(f"异常分数 {anomaly_score:.3f} 达到锁屏阈值 {self.lock_screen_threshold}")
                    self._show_lock_warning_and_execute(anomaly_score)
                else:
                    self.logger.info(f"异常分数 {anomaly_score:.3f} 未达到锁屏阈值 {self.lock_screen_threshold}")
                    
        except Exception as e:
            self.logger.error(f"执行系统操作失败: {str(e)}")

    def _show_lock_warning_and_execute(self, anomaly_score):
        """显示锁屏警告并执行锁屏"""
        try:
            # 显示警告弹窗（不检测环境，直接弹窗）
            if self.show_warning_dialog:
                self._show_warning_dialog(anomaly_score)
            else:
                # 直接锁屏提示
                self._show_console_warning(anomaly_score)
                self._lock_screen()
                
        except Exception as e:
            self.logger.error(f"显示锁屏警告失败: {str(e)}")
            # 如果警告失败，直接锁屏
            self._lock_screen()

    def _show_console_warning(self, anomaly_score):
        """显示控制台警告"""
        try:
            warning_border = "!" * 80
            warning_message = f"""
{warning_border}
🚨 严重安全警告 - 异常行为检测
{warning_border}
异常分数: {anomaly_score:.3f}
锁屏阈值: {self.lock_screen_threshold}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️  系统将在 {self.warning_duration} 秒后自动锁屏
⚠️  请确保已保存所有工作
⚠️  此警告无法关闭

{warning_border}
"""
            
            # 如果控制台可见，显示倒计时
            if self._is_console_visible():
                print(f"\033[91m{warning_message}\033[0m")  # 红色显示
                
                # 倒计时
                for i in range(self.warning_duration, 0, -1):
                    print(f"\033[93m⏰ 剩余时间: {i} 秒\033[0m")
                    time.sleep(1)
            else:
                # 如果控制台不可见，写入文件并等待
                self._send_file_alert(
                    user_id='system',
                    alert_type='lock_screen_warning',
                    message=f'异常分数 {anomaly_score:.3f} 达到锁屏阈值，系统将在 {self.warning_duration} 秒后锁屏',
                    severity='critical',
                    data={'anomaly_score': anomaly_score}
                )
                
                # 等待指定时间
                time.sleep(self.warning_duration)
                
        except Exception as e:
            self.logger.error(f"显示控制台警告失败: {str(e)}")

    def _show_warning_dialog(self, anomaly_score):
        """显示警告对话框"""
        try:
            # 创建警告窗口
            warning_window = tk.Tk()
            warning_window.title("🚨 安全警告 - 异常行为检测")
            warning_window.geometry("600x500")
            warning_window.configure(bg='#ff4444')
            
            # 设置窗口置顶
            warning_window.attributes('-topmost', True)
            warning_window.focus_force()
            
            # 禁用窗口关闭按钮
            warning_window.protocol("WM_DELETE_WINDOW", self._prevent_close)
            
            # 禁用基本的关闭快捷键
            warning_window.bind('<Alt-F4>', self._prevent_close)
            warning_window.bind('<Escape>', self._prevent_close)
            warning_window.bind('<Control-W>', self._prevent_close)
            warning_window.bind('<Control-Q>', self._prevent_close)
            
            # 禁用鼠标右键菜单
            warning_window.bind('<Button-3>', self._prevent_close)
            
            # 创建主框架
            main_frame = tk.Frame(warning_window, bg='#ff4444')
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # 创建警告内容
            title_label = tk.Label(
                main_frame,
                text="🚨 严重安全警告",
                font=("Arial", 20, "bold"),
                fg="white",
                bg="#ff4444"
            )
            title_label.pack(pady=(20, 10))
            
            # 异常分数显示
            score_frame = tk.Frame(main_frame, bg='#ff4444')
            score_frame.pack(pady=10)
            
            score_label = tk.Label(
                score_frame,
                text=f"异常分数: {anomaly_score:.3f}",
                font=("Arial", 16, "bold"),
                fg="yellow",
                bg="#ff4444"
            )
            score_label.pack()
            
            # 警告消息
            message_label = tk.Label(
                main_frame,
                text="检测到异常用户行为\n\n系统将在倒计时结束后自动锁屏\n\n请确保已保存所有工作\n\n⚠️ 此窗口无法关闭",
                font=("Arial", 14),
                fg="white",
                bg="#ff4444",
                justify="center"
            )
            message_label.pack(pady=20)
            
            # 倒计时标签
            countdown_label = tk.Label(
                main_frame,
                text=f"剩余时间: {self.warning_duration} 秒",
                font=("Arial", 18, "bold"),
                fg="yellow",
                bg="#ff4444"
            )
            countdown_label.pack(pady=15)
            
            # 按钮框架
            button_frame = tk.Frame(main_frame, bg='#ff4444')
            button_frame.pack(pady=20)
            
            # 立即锁屏按钮
            lock_now_button = tk.Button(
                button_frame,
                text="🔒 立即锁屏",
                font=("Arial", 16, "bold"),
                bg="#f44336",
                fg="white",
                relief="raised",
                bd=3,
                command=lambda: self._lock_screen_now(warning_window)
            )
            lock_now_button.pack(pady=10)
            
            # 安全提示
            info_label = tk.Label(
                main_frame,
                text="🔒 安全模式：此窗口无法关闭，系统将自动锁屏",
                font=("Arial", 12),
                fg="yellow",
                bg="#ff4444"
            )
            info_label.pack(pady=10)
            
            # 系统信息
            system_info = tk.Label(
                main_frame,
                text=f"系统时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                font=("Arial", 10),
                fg="lightgray",
                bg="#ff4444"
            )
            system_info.pack(pady=5)
            
            # 倒计时和自动锁屏
            self._start_countdown(warning_window, countdown_label, self.warning_duration)
            
            # 启动GUI事件循环
            warning_window.mainloop()
            
        except Exception as e:
            self.logger.error(f"显示警告对话框失败: {str(e)}")
            # 如果GUI失败，直接锁屏
            self._lock_screen()

    def _start_countdown(self, window, label, remaining_time):
        """开始倒计时"""
        try:
            if remaining_time > 0:
                # 更新倒计时显示
                label.config(text=f"剩余时间: {remaining_time} 秒")
                
                # 根据剩余时间调整颜色
                if remaining_time <= 5:
                    label.config(fg="red", font=("Arial", 20, "bold"))
                elif remaining_time <= 10:
                    label.config(fg="orange", font=("Arial", 19, "bold"))
                else:
                    label.config(fg="yellow", font=("Arial", 18, "bold"))
                
                # 记录倒计时日志
                if remaining_time % 10 == 0 or remaining_time <= 5:
                    self.logger.info(f"安全警告倒计时: {remaining_time} 秒")
                    print(f"[系统] 安全警告倒计时: {remaining_time} 秒")
                
                # 继续倒计时
                window.after(1000, lambda: self._start_countdown(window, label, remaining_time - 1))
            else:
                # 时间到，执行锁屏
                self.logger.warning("安全警告倒计时结束，执行锁屏")
                print("[系统] 倒计时结束，正在锁屏...")
                
                # 显示最终警告
                label.config(text="正在锁屏...", fg="red", font=("Arial", 20, "bold"))
                
                # 延迟一秒后锁屏，让用户看到最终状态
                window.after(1000, lambda: self._execute_lock_screen(window))
                
        except Exception as e:
            self.logger.error(f"倒计时异常: {str(e)}")
            # 如果倒计时失败，直接锁屏
            self._execute_lock_screen(window)

    def _cancel_lock_screen(self, window):
        """取消锁屏 - 已禁用，用户无法取消"""
        # 此功能已禁用，用户无法取消锁屏
        pass

    def _lock_screen_now(self, window):
        """立即锁屏"""
        try:
            self.logger.warning("用户选择立即锁屏")
            print("[系统] 用户选择立即锁屏")
            
            # 显示锁屏确认
            for widget in window.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label) and "剩余时间" in child.cget("text"):
                            child.config(text="正在锁屏...", fg="red", font=("Arial", 20, "bold"))
                            break
            
            # 延迟一秒后执行锁屏，让用户看到确认信息
            window.after(1000, lambda: self._execute_lock_screen(window))
            
        except Exception as e:
            self.logger.error(f"立即锁屏失败: {str(e)}")
            # 如果失败，直接锁屏
            self._execute_lock_screen(window)

    def _execute_lock_screen(self, window):
        """执行锁屏操作并关闭窗口"""
        try:
            self.logger.warning("执行最终锁屏操作...")
            print("[系统] 执行最终锁屏操作...")
            
            # 关闭警告窗口
            try:
                window.destroy()
                self.logger.info("警告窗口已关闭")
            except Exception as e:
                self.logger.error(f"关闭警告窗口失败: {str(e)}")
            
            # 执行锁屏
            self._lock_screen()
            
        except Exception as e:
            self.logger.error(f"执行最终锁屏失败: {str(e)}")
            # 如果失败，尝试直接锁屏
            try:
                self._lock_screen()
            except Exception as e2:
                self.logger.error(f"备用锁屏也失败: {str(e2)}")

    def _prevent_close(self, event=None):
        """阻止窗口关闭"""
        # 此方法用于阻止用户关闭警告窗口
        self.logger.info("用户尝试关闭警告窗口，已阻止")
        print("[系统] 警告：此窗口无法关闭！")
        return "break"  # 阻止事件传播

    def _lock_screen(self):
        """锁屏操作"""
        try:
            self.logger.warning("执行锁屏操作...")
            print("[系统] 检测到严重异常行为，正在锁屏...")
            
            if platform.system() == "Windows" and WINDOWS_AVAILABLE:
                # Windows锁屏
                self._lock_screen_windows()
            else:
                # 其他系统锁屏
                self._lock_screen_generic()
                
        except Exception as e:
            self.logger.error(f"锁屏操作失败: {str(e)}")

    def _lock_screen_windows(self):
        """Windows系统锁屏"""
        try:
            # 方法1: 使用rundll32
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=True)
            self.logger.info("Windows锁屏成功 (rundll32)")
            
        except subprocess.CalledProcessError:
            try:
                # 方法2: 使用Windows API
                if WINDOWS_AVAILABLE:
                    win32api.LockWorkStation()
                    self.logger.info("Windows锁屏成功 (API)")
                else:
                    self.logger.error("Windows API不可用")
                    
            except Exception as e:
                self.logger.error(f"Windows锁屏失败: {str(e)}")

    def _lock_screen_generic(self):
        """通用锁屏方法"""
        try:
            if platform.system() == "Linux":
                # Linux锁屏：尝试常见桌面环境命令，兼容 UKUI/麒麟、GNOME、Deepin 等
                candidates = [
                    # UKUI / Ubuntu Kylin
                    ['ukui-screensaver-command', '--lock'],
                    ['qdbus', 'org.ukui.ScreenSaver', '/ScreenSaver', 'Lock'],
                    ['dbus-send', '--session', '--dest=org.ukui.ScreenSaver', '--type=method_call', '/ScreenSaver', 'org.ukui.ScreenSaver.Lock'],
                    # 通用/其他 DE 回退
                    ['gnome-screensaver-command', '--lock'],
                    ['qdbus', 'org.freedesktop.ScreenSaver', '/ScreenSaver', 'Lock'],
                    ['xdg-screensaver', 'lock'],
                    ['loginctl', 'lock-session'],
                    ['dm-tool', 'lock'],
                ]
                success = False
                for cmd in candidates:
                    try:
                        subprocess.run(cmd, check=True)
                        self.logger.info(f"Linux锁屏成功: {' '.join(cmd)}")
                        success = True
                        break
                    except Exception:
                        continue
                if not success:
                    self.logger.warning("未找到可用的锁屏命令，已跳过")
            elif platform.system() == "Darwin":
                # macOS锁屏
                subprocess.run(['pmset', 'displaysleepnow'], check=True)
                self.logger.info("macOS锁屏成功")
            else:
                self.logger.warning(f"不支持的操作系统: {platform.system()}")
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"锁屏命令执行失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"通用锁屏失败: {str(e)}")

    def get_alert_statistics(self, user_id, hours=24):
        """获取告警统计信息"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 统计告警数量
            cursor.execute('''
                SELECT COUNT(*) FROM alerts 
                WHERE user_id = ? AND timestamp > ?
            ''', (user_id, cutoff_time))
            
            total_alerts = cursor.fetchone()[0]
            
            # 按类型统计
            cursor.execute('''
                SELECT alert_type, COUNT(*) FROM alerts 
                WHERE user_id = ? AND timestamp > ?
                GROUP BY alert_type
            ''', (user_id, cutoff_time))
            
            alerts_by_type = dict(cursor.fetchall())
            
            conn.close()
            
            stats = {
                'total_alerts': total_alerts,
                'alerts_by_type': alerts_by_type,
                'time_period_hours': hours
            }
            
            self.logger.info(f"用户 {user_id} 告警统计: {total_alerts} 条告警")
            return stats
            
        except Exception as e:
            self.logger.error(f"获取告警统计失败: {str(e)}")
            return {}

    def clear_alert_history(self, user_id=None):
        """清除告警历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('DELETE FROM alerts WHERE user_id = ?', (user_id,))
                self.logger.info(f"清除用户 {user_id} 的告警历史")
            else:
                cursor.execute('DELETE FROM alerts')
                self.logger.info("清除所有告警历史")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"清除告警历史失败: {str(e)}")

    def force_logout(self):
        """强制用户登出"""
        try:
            self.logger.warning("🚪 开始强制用户登出...")
            
            if WINDOWS_AVAILABLE:
                try:
                    # 使用Windows API强制登出
                    win32api.ExitWindowsEx(win32con.EWX_LOGOFF, 0)
                    self.logger.info("Windows强制登出命令已发送")
                    return True
                except Exception as e:
                    self.logger.error(f"Windows强制登出失败: {str(e)}")
                    # 备用方案：锁屏
                    self.logger.warning("改为执行锁屏操作")
                    self._lock_screen()
                    return True
            else:
                self.logger.warning("Windows API不可用，改为锁屏")
                self._lock_screen()
                return True
                
        except Exception as e:
            self.logger.error(f"强制登出失败: {str(e)}")
            return False

    def get_alert_summary(self, user_id=None, hours=24):
        """获取告警摘要"""
        try:
            stats = self.get_alert_statistics(user_id, hours)
            
            summary = {
                'total_alerts': stats.get('total_alerts', 0),
                'alerts_by_type': stats.get('alerts_by_type', {}),
                'time_period_hours': hours,
                'last_alert_time': None,
                'alert_trend': 'normal'
            }
            
            # 获取最后一次告警时间
            if user_id:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT timestamp FROM alerts 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', (user_id,))
                result = cursor.fetchone()
                if result:
                    summary['last_alert_time'] = result[0]
                conn.close()
            
            # 判断告警趋势
            if summary['total_alerts'] == 0:
                summary['alert_trend'] = 'none'
            elif summary['total_alerts'] >= 5:
                summary['alert_trend'] = 'high'
            elif summary['total_alerts'] >= 2:
                summary['alert_trend'] = 'medium'
            else:
                summary['alert_trend'] = 'low'
            
            return summary
            
        except Exception as e:
            self.logger.error(f"获取告警摘要失败: {str(e)}")
            return {} 