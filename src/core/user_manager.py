import time
import threading
import json
import os
from datetime import datetime
from pathlib import Path
import sys
import platform
import traceback

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader

try:
    from pynput import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("警告: pynput未安装，无法监听键盘快捷键")

# Windows特定的导入
try:
    import win32api
    import win32con
    import win32gui
    import win32process
    import win32security
    import win32ts
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False

class UserManager:
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigLoader()
        
        self.logger.debug("=== UserManager 初始化开始 ===")
        
        # 用户配置文件路径 - 使用配置文件中的路径
        self.user_config_path = Path(self.config.get_paths()['user_config'])
        self.user_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 当前用户信息
        self.current_user_id = None
        self.current_session_id = None
        self.user_start_time = None
        self.current_username = None
        
        # 键盘监听器
        self.keyboard_listener = None
        self.is_listening = False
        
        # 快捷键配置 - 修改为更直观的快捷键
        self.hotkeys = {
            'start_collection': {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.KeyCode.from_char('C')},  # Ctrl+Alt+C 开始采集
            'stop_collection': {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.KeyCode.from_char('S')},   # Ctrl+Alt+S 停止采集
            'process_features': {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.KeyCode.from_char('F')},  # Ctrl+Alt+F 处理特征
            'train_model': {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.KeyCode.from_char('T')},      # Ctrl+Alt+T 训练模型
            'start_prediction': {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.KeyCode.from_char('P')}, # Ctrl+Alt+P 开始预测
            'stop_prediction': {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.KeyCode.from_char('X')},  # Ctrl+Alt+X 停止预测
            'retrain_model': {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.KeyCode.from_char('R')},    # Ctrl+Alt+R 重新训练
            'show_status': {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.KeyCode.from_char('I')},      # Ctrl+Alt+I 显示状态
            'quit_system': {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.KeyCode.from_char('Q')}       # Ctrl+Alt+Q 退出系统
        }
        
        # 当前按下的键
        self.pressed_keys = set()
        
        # 回调函数
        self.callbacks = {
            'start_collection': None,
            'stop_collection': None,
            'process_features': None,
            'train_model': None,
            'start_prediction': None,
            'stop_prediction': None,
            'retrain_model': None,
            'show_status': None,
            'quit_system': None
        }
        
        # 初始化用户
        self._load_user_config()
        self._initialize_current_user()
        
        self.logger.info("用户管理器初始化完成")
        self.logger.debug("=== UserManager 初始化结束 ===")

    def _get_windows_username(self):
        """获取Windows登录用户名"""
        try:
            # 尝试多种方式获取Windows用户名
            username = os.getenv('USERNAME') or os.getenv('USER') or os.getenv('LOGNAME')
            
            if not username:
                # 如果环境变量中没有，尝试从系统获取
                if platform.system() == 'Windows':
                    import getpass
                    username = getpass.getuser()
                else:
                    username = 'unknown_user'
            
            return username
            
        except Exception as e:
            self.logger.error(f"获取Windows用户名失败: {str(e)}")
            return 'unknown_user'

    def _generate_user_id(self, is_retrain=False):
        """生成用户ID"""
        try:
            # 获取Windows用户名
            username = self._get_windows_username()
            
            # 生成时间戳
            timestamp = int(time.time())
            
            if is_retrain:
                # 重新训练时，在用户名后添加retrain标识
                user_id = f"{username}_retrain_{timestamp}"
            else:
                # 正常情况，使用用户名和时间戳
                user_id = f"{username}_{timestamp}"
            
            return user_id
            
        except Exception as e:
            self.logger.error(f"生成用户ID失败: {str(e)}")
            return f"user_{int(time.time())}"

    def _load_user_config(self):
        """加载用户配置"""
        try:
            if self.user_config_path.exists():
                with open(self.user_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_user_id = config.get('current_user_id')
                    self.logger.info(f"加载用户配置: {self.current_user_id}")
            else:
                self.current_user_id = None
                self.logger.info("用户配置文件不存在，将创建新用户")
        except Exception as e:
            self.logger.error(f"加载用户配置失败: {str(e)}")
            self.current_user_id = None

    def _save_user_config(self):
        """保存用户配置"""
        try:
            config = {
                'current_user_id': self.current_user_id,
                'last_updated': datetime.now().isoformat(),
                'platform': platform.system(),
                'username': self._get_windows_username()
            }
            
            with open(self.user_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"用户配置已保存: {self.current_user_id}")
        except Exception as e:
            self.logger.error(f"保存用户配置失败: {str(e)}")

    def _initialize_current_user(self):
        """初始化当前用户"""
        if not self.current_user_id:
            self.create_new_user()
        else:
            self.start_new_session()

    def create_new_user(self, username=None):
        """创建新用户"""
        try:
            # 生成新的用户ID
            self.current_user_id = self._generate_user_id(is_retrain=False)
            
            # 创建新会话
            self.start_new_session()
            
            # 保存配置
            self._save_user_config()
            
            self.logger.info(f"创建新用户: {self.current_user_id}")
            
            # 触发回调
            if self.callbacks['start_collection']:
                self.callbacks['start_collection'](self.current_user_id)
            
            return self.current_user_id
            
        except Exception as e:
            self.logger.error(f"创建新用户失败: {str(e)}")
            return None

    def create_retrain_user(self):
        """创建重新训练用户"""
        try:
            # 生成重新训练的用户ID
            retrain_user_id = self._generate_user_id(is_retrain=True)
            
            # 保存当前用户ID
            old_user_id = self.current_user_id
            
            # 设置新的用户ID
            self.current_user_id = retrain_user_id
            
            # 创建新会话
            self.start_new_session()
            
            # 保存配置
            self._save_user_config()
            
            self.logger.info(f"创建重新训练用户: {retrain_user_id} (原用户: {old_user_id})")
            
            # 触发回调
            if self.callbacks['retrain_model']:
                self.callbacks['retrain_model'](retrain_user_id)
            
            return retrain_user_id
            
        except Exception as e:
            self.logger.error(f"创建重新训练用户失败: {str(e)}")
            return None

    def start_new_session(self):
        """开始新会话"""
        try:
            timestamp = int(time.time())
            self.current_session_id = f"session_{timestamp}"
            self.user_start_time = timestamp
            
            self.logger.info(f"开始新会话: {self.current_session_id} (用户: {self.current_user_id})")
            
            return self.current_session_id
            
        except Exception as e:
            self.logger.error(f"开始新会话失败: {str(e)}")
            return None

    def switch_user(self, user_id=None):
        """切换用户"""
        try:
            if user_id:
                self.current_user_id = user_id
            else:
                # 如果没有指定用户ID，创建新用户
                self.create_new_user()
                return
            
            # 开始新会话
            self.start_new_session()
            
            # 保存配置
            self._save_user_config()
            
            self.logger.info(f"切换到用户: {self.current_user_id}")
            
            # 触发回调
            if self.callbacks['switch_user']:
                self.callbacks['switch_user'](self.current_user_id)
            
        except Exception as e:
            self.logger.error(f"切换用户失败: {str(e)}")

    def get_current_user_info(self):
        """获取当前用户信息"""
        return {
            'user_id': self.current_user_id,
            'session_id': self.current_session_id,
            'start_time': self.user_start_time,
            'duration': time.time() - self.user_start_time if self.user_start_time else 0,
            'username': self._get_windows_username(),
            'platform': platform.system()
        }

    def get_current_user_id(self):
        """获取当前用户ID"""
        self.logger.debug("=== 获取当前用户ID ===")
        
        if self.current_user_id:
            self.logger.debug(f"返回缓存的用户ID: {self.current_user_id}")
            return self.current_user_id
        
        try:
            # 获取当前Windows用户名
            self.logger.debug("获取当前Windows用户名...")
            if WINDOWS_AVAILABLE:
                username = win32api.GetUserName()
                self.logger.debug(f"Windows用户名: {username}")
            else:
                username = os.getenv('USERNAME') or os.getenv('USER') or 'unknown'
                self.logger.debug(f"环境变量用户名: {username}")
            
            self.current_username = username
            
            # 生成用户ID
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            user_id = f"{username}_{timestamp}"
            self.current_user_id = user_id
            
            self.logger.info(f"生成用户ID: {user_id}")
            self.logger.debug(f"用户名: {username}, 时间戳: {timestamp}")
            self.logger.debug("=== 获取当前用户ID完成 ===")
            return user_id
            
        except Exception as e:
            self.logger.error(f"获取当前用户ID失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            # 使用默认用户ID
            default_id = f"default_user_{int(time.time())}"
            self.current_user_id = default_id
            self.logger.warning(f"使用默认用户ID: {default_id}")
            return default_id

    def set_current_user(self, user_id):
        """设置当前用户"""
        try:
            self.current_user_id = user_id
            self.start_new_session()
            self._save_user_config()
            self.logger.info(f"设置当前用户: {user_id}")
        except Exception as e:
            self.logger.error(f"设置当前用户失败: {str(e)}")

    def get_user_list(self):
        """获取用户列表"""
        try:
            # 从数据库获取所有用户
            from src.core.data_collector.windows_mouse_collector import WindowsMouseCollector
            
            collector = WindowsMouseCollector()
            db_path = collector.db_path
            
            if not db_path.exists():
                return []
            
            conn = collector.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT user_id, 
                       MIN(timestamp) as first_seen,
                       MAX(timestamp) as last_seen,
                       COUNT(*) as total_events,
                       COUNT(DISTINCT session_id) as total_sessions
                FROM mouse_events 
                GROUP BY user_id
                ORDER BY last_seen DESC
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'user_id': row[0],
                    'first_seen': row[1],
                    'last_seen': row[2],
                    'total_events': row[3],
                    'total_sessions': row[4],
                    'is_current': row[0] == self.current_user_id
                })
            
            conn.close()
            return users
            
        except Exception as e:
            self.logger.error(f"获取用户列表失败: {str(e)}")
            return []

    def register_callback(self, event_name, callback_func):
        """注册回调函数"""
        self.logger.debug(f"注册回调函数: {event_name}")
        self.callbacks[event_name] = callback_func
        self.logger.debug(f"回调函数 {event_name} 注册成功")

    def start_keyboard_listener(self):
        """启动键盘监听器"""
        self.logger.debug("=== 启动键盘监听器 ===")
        
        if self.is_listening:
            self.logger.warning("键盘监听器已在运行中")
            return
        
        try:
            # 创建键盘监听线程
            self.logger.debug("创建键盘监听线程...")
            self.keyboard_listener = threading.Thread(target=self._keyboard_listener_loop, daemon=True)
            self.is_listening = True
            self.keyboard_listener.start()
            
            self.logger.info("键盘监听器启动成功")
            self.logger.debug("=== 键盘监听器启动完成 ===")
            
        except Exception as e:
            self.logger.error(f"启动键盘监听器失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            self.is_listening = False

    def stop_keyboard_listener(self):
        """停止键盘监听器"""
        self.logger.debug("=== 停止键盘监听器 ===")
        
        if not self.is_listening:
            self.logger.debug("键盘监听器未在运行")
            return
        
        try:
            self.is_listening = False
            if self.keyboard_listener and self.keyboard_listener.is_alive():
                self.logger.debug("等待键盘监听线程结束...")
                self.keyboard_listener.join(timeout=2)
            
            self.logger.info("键盘监听器已停止")
            self.logger.debug("=== 键盘监听器停止完成 ===")
            
        except Exception as e:
            self.logger.error(f"停止键盘监听器失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")

    def _keyboard_listener_loop(self):
        """键盘监听循环"""
        self.logger.debug("=== 键盘监听循环开始 ===")
        
        try:
            # 导入键盘监听库
            self.logger.debug("导入键盘监听库...")
            from pynput import keyboard
            
            def on_press(key):
                try:
                    # 更新修饰键状态
                    if key == keyboard.Key.ctrl:
                        self._ctrl_pressed = True
                        self.logger.debug("Ctrl键按下")
                    elif key == keyboard.Key.alt:
                        self._alt_pressed = True
                        self.logger.debug("Alt键按下")
                    elif hasattr(key, 'char'):
                        # 字符键
                        self.logger.debug(f"按下字符键: {key.char}")
                        # 检测Ctrl+Alt组合键
                        if self._ctrl_pressed and self._alt_pressed:
                            self._handle_hotkey(key)
                    else:
                        # 特殊键
                        self.logger.debug(f"按下特殊键: {key}")
                            
                except Exception as e:
                    self.logger.error(f"键盘事件处理失败: {str(e)}")
                    self.logger.debug(f"异常详情: {traceback.format_exc()}")

            def on_release(key):
                try:
                    # 更新修饰键状态
                    if key == keyboard.Key.ctrl:
                        self._ctrl_pressed = False
                        self.logger.debug("Ctrl键释放")
                    elif key == keyboard.Key.alt:
                        self._alt_pressed = False
                        self.logger.debug("Alt键释放")
                        
                except Exception as e:
                    self.logger.error(f"键盘释放事件处理失败: {str(e)}")
                    self.logger.debug(f"异常详情: {traceback.format_exc()}")

            # 初始化修饰键状态
            self._ctrl_pressed = False
            self._alt_pressed = False
            
            # 创建监听器
            self.logger.debug("创建键盘监听器...")
            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                self.logger.info("键盘监听器运行中...")
                listener.join()
                
        except ImportError:
            self.logger.error("pynput库未安装，无法启动键盘监听")
            print("[错误] 请安装pynput库: pip install pynput")
        except Exception as e:
            self.logger.error(f"键盘监听循环异常: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
        finally:
            self.logger.debug("=== 键盘监听循环结束 ===")

    def _handle_hotkey(self, key):
        """处理快捷键"""
        self.logger.debug(f"处理快捷键: {key}")
        
        try:
            # 获取当前用户ID
            current_user_id = self.get_current_user_id()
            
            # 快捷键映射
            if hasattr(key, 'char'):
                char = key.char.lower()
                self.logger.debug(f"检测到字符键: {char}")
                
                if char == 'c':
                    self.logger.info("检测到快捷键: Ctrl+Alt+C (开始数据采集)")
                    self._trigger_callback('start_collection', current_user_id)
                elif char == 's':
                    self.logger.info("检测到快捷键: Ctrl+Alt+S (停止数据采集)")
                    self._trigger_callback('stop_collection', current_user_id)
                elif char == 'f':
                    self.logger.info("检测到快捷键: Ctrl+Alt+F (处理特征)")
                    self._trigger_callback('process_features')
                elif char == 't':
                    self.logger.info("检测到快捷键: Ctrl+Alt+T (训练模型)")
                    self._trigger_callback('train_model')
                elif char == 'p':
                    self.logger.info("检测到快捷键: Ctrl+Alt+P (开始预测)")
                    self._trigger_callback('start_prediction')
                elif char == 'x':
                    self.logger.info("检测到快捷键: Ctrl+Alt+X (停止预测)")
                    self._trigger_callback('stop_prediction')
                elif char == 'r':
                    self.logger.info("检测到快捷键: Ctrl+Alt+R (重新训练)")
                    retrain_user_id = self.create_retrain_user()
                    self._trigger_callback('retrain_model', retrain_user_id)
                elif char == 'i':
                    self.logger.info("检测到快捷键: Ctrl+Alt+I (显示状态)")
                    self._trigger_callback('show_status')
                elif char == 'q':
                    self.logger.info("检测到快捷键: Ctrl+Alt+Q (退出系统)")
                    self._trigger_callback('quit_system')
                else:
                    self.logger.debug(f"未识别的快捷键: {char}")
            else:
                self.logger.debug(f"特殊键: {key}")
                
        except Exception as e:
            self.logger.error(f"处理快捷键失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")

    def _trigger_callback(self, event_name, *args, **kwargs):
        """触发回调函数"""
        self.logger.debug(f"触发回调函数: {event_name}")
        self.logger.debug(f"回调参数: args={args}, kwargs={kwargs}")
        
        if event_name in self.callbacks:
            try:
                callback_func = self.callbacks[event_name]
                self.logger.debug(f"执行回调函数: {event_name}")
                result = callback_func(*args, **kwargs)
                self.logger.debug(f"回调函数 {event_name} 执行完成")
                return result
            except Exception as e:
                self.logger.error(f"回调函数 {event_name} 执行失败: {str(e)}")
                self.logger.debug(f"异常详情: {traceback.format_exc()}")
        else:
            self.logger.warning(f"未找到回调函数: {event_name}")

    def show_user_status(self):
        """显示用户状态"""
        try:
            user_info = self.get_current_user_info()
            user_list = self.get_user_list()
            
            print("\n=== 用户状态 ===")
            print(f"当前用户: {user_info['user_id']}")
            print(f"当前会话: {user_info['session_id']}")
            print(f"会话时长: {user_info['duration']:.1f} 秒")
            print(f"系统用户: {user_info['username']}")
            print(f"平台: {user_info['platform']}")
            
            print(f"\n用户列表 ({len(user_list)} 个用户):")
            for i, user in enumerate(user_list[:5], 1):  # 只显示前5个
                status = " [当前]" if user['is_current'] else ""
                print(f"{i}. {user['user_id']}{status}")
                print(f"   事件数: {user['total_events']}, 会话数: {user['total_sessions']}")
                print(f"   最后活动: {datetime.fromtimestamp(user['last_seen']).strftime('%Y-%m-%d %H:%M:%S')}")
            
            if len(user_list) > 5:
                print(f"   ... 还有 {len(user_list) - 5} 个用户")
            
        except Exception as e:
            self.logger.error(f"显示用户状态失败: {str(e)}")

    def cleanup_old_users(self, days=30):
        """清理旧用户数据"""
        try:
            from src.core.data_collector.windows_mouse_collector import WindowsMouseCollector
            
            collector = WindowsMouseCollector()
            cutoff_time = time.time() - (days * 24 * 3600)
            
            conn = collector.get_db_connection()
            cursor = conn.cursor()
            
            # 删除旧用户的鼠标事件
            cursor.execute('DELETE FROM mouse_events WHERE timestamp < ?', (cutoff_time,))
            deleted_events = cursor.rowcount
            
            # 删除旧用户的特征数据
            cursor.execute('DELETE FROM features WHERE timestamp < ?', (cutoff_time,))
            deleted_features = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"清理了 {deleted_events} 条鼠标事件和 {deleted_features} 条特征数据")
            
        except Exception as e:
            self.logger.error(f"清理旧用户数据失败: {str(e)}")

    def __del__(self):
        """析构函数"""
        self.stop_keyboard_listener() 