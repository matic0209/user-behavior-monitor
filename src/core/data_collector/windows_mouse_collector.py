import time
import threading
import sqlite3
import uuid
from datetime import datetime
import traceback
from pathlib import Path

# Windows特定的导入
try:
    import win32api
    import win32gui
    import win32con
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False

from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader

class WindowsMouseCollector:
    def __init__(self, user_id):
        self.logger = Logger()
        self.config = ConfigLoader()
        
        self.logger.debug("=== WindowsMouseCollector 初始化开始 ===")
        self.logger.debug(f"参数 - user_id: {user_id}")
        
        self.user_id = user_id
        self.session_id = None
        self.is_collecting = False
        self.collection_thread = None
        
        # 数据库连接 - 使用配置文件中的数据库路径
        self.db_path = Path(self.config.get_paths()['database'])
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self.logger.debug("初始化数据库...")
        self._init_database()
        
        self.logger.info(f"鼠标采集器初始化完成 - 用户: {user_id}")
        self.logger.debug("=== WindowsMouseCollector 初始化结束 ===")

    def _init_database(self):
        """初始化数据库"""
        self.logger.debug("=== 初始化数据库 ===")
        
        try:
            self.logger.debug(f"数据库路径: {self.db_path}")
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 创建鼠标事件表
            self.logger.debug("创建鼠标事件表...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mouse_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    x INTEGER NOT NULL,
                    y INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    button TEXT,
                    wheel_delta INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建特征表（如果不存在）
            self.logger.debug("创建特征表...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    feature_vector TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            self.logger.debug("创建数据库索引...")
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_session ON mouse_events(user_id, session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON mouse_events(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_features_user_session ON features(user_id, session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_features_timestamp ON features(timestamp)')
            
            conn.commit()
            conn.close()
            
            self.logger.debug("数据库初始化完成")
            self.logger.debug("=== 数据库初始化结束 ===")
            
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            raise

    def start_collection(self):
        """开始数据采集"""
        self.logger.info("=== 开始数据采集 ===")
        self.logger.debug(f"当前状态 - is_collecting: {self.is_collecting}")
        
        if self.is_collecting:
            self.logger.warning("数据采集已在运行中")
            return False
        
        if not WINDOWS_AVAILABLE:
            self.logger.error("Windows API不可用，无法进行数据采集")
            return False
        
        try:
            # 生成会话ID
            self.session_id = str(uuid.uuid4())
            self.logger.debug(f"生成会话ID: {self.session_id}")
            
            # 创建采集线程
            self.logger.debug("创建数据采集线程...")
            self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
            self.is_collecting = True
            self.collection_thread.start()
            
            self.logger.info(f"数据采集启动成功 - 用户: {self.user_id}, 会话: {self.session_id}")
            self.logger.debug("=== 数据采集启动完成 ===")
            return True
            
        except Exception as e:
            self.logger.error(f"启动数据采集失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            self.is_collecting = False
            return False

    def stop_collection(self):
        """停止数据采集"""
        self.logger.info("=== 停止数据采集 ===")
        self.logger.debug(f"当前状态 - is_collecting: {self.is_collecting}")
        
        if not self.is_collecting:
            self.logger.debug("数据采集未在运行")
            return
        
        try:
            self.is_collecting = False
            
            if self.collection_thread and self.collection_thread.is_alive():
                self.logger.debug("等待采集线程结束...")
                self.collection_thread.join(timeout=2)
            
            self.logger.info(f"数据采集已停止 - 用户: {self.user_id}, 会话: {self.session_id}")
            self.logger.debug("=== 数据采集停止完成 ===")
            
        except Exception as e:
            self.logger.error(f"停止数据采集失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")

    def _collection_loop(self):
        """数据采集循环"""
        self.logger.debug("=== 数据采集循环开始 ===")
        self.logger.debug(f"采集参数 - user_id: {self.user_id}, session_id: {self.session_id}")
        
        try:
            # 获取采集间隔
            data_collection_config = self.config.get_data_collection_config()
            interval = data_collection_config.get('collection_interval', 0.1)
            self.logger.debug(f"采集间隔: {interval}秒")
            
            # 获取最大缓冲区大小
            max_buffer_size = data_collection_config.get('max_buffer_size', 10000)
            self.logger.debug(f"最大缓冲区大小: {max_buffer_size}")
            # 每会话目标样本数（达到后自动停止）
            target_samples = data_collection_config.get('target_samples_per_session', None)
            if target_samples is not None:
                try:
                    target_samples = int(target_samples)
                except Exception:
                    target_samples = None
            
            # 数据缓冲区
            buffer = []
            last_save_time = time.time()
            save_interval = 5.0  # 每5秒保存一次数据
            total_collected = 0
            
            self.logger.info("开始鼠标数据采集循环...")
            
            while self.is_collecting:
                try:
                    # 获取鼠标位置
                    cursor_pos = win32api.GetCursorPos()
                    x, y = cursor_pos
                    
                    # 获取当前时间戳
                    timestamp = time.time()
                    
                    # 创建鼠标事件记录
                    event_data = {
                        'user_id': self.user_id,
                        'session_id': self.session_id,
                        'timestamp': timestamp,
                        'x': x,
                        'y': y,
                        'event_type': 'move',
                        'button': None,
                        'wheel_delta': 0
                    }
                    
                    # 添加到缓冲区
                    buffer.append(event_data)
                    total_collected += 1
                    
                    # 检查是否需要保存数据
                    if len(buffer) >= max_buffer_size or (time.time() - last_save_time) >= save_interval:
                        self.logger.debug(f"保存数据到数据库 - 缓冲区大小: {len(buffer)}")
                        self._save_events_to_db(buffer)
                        buffer.clear()
                        last_save_time = time.time()
                        
                        # 显示采集进度
                        self.logger.info(f"📊 已采集 {total_collected} 个数据点")

                    # 达到每会话目标样本数后自动停止
                    if target_samples is not None and total_collected >= target_samples:
                        self.logger.info(f"达到目标样本数 {target_samples}，自动停止采集")
                        # 先保存缓冲区
                        if buffer:
                            self._save_events_to_db(buffer)
                            buffer.clear()
                        self.is_collecting = False
                        break
                    
                    # 等待下一次采集
                    time.sleep(interval)
                    
                except Exception as e:
                    self.logger.error(f"数据采集循环异常: {str(e)}")
                    self.logger.debug(f"异常详情: {traceback.format_exc()}")
                    time.sleep(interval)
            
            # 保存剩余数据
            if buffer:
                self.logger.debug(f"保存剩余数据 - 缓冲区大小: {len(buffer)}")
                self._save_events_to_db(buffer)
            
            self.logger.info(f"数据采集循环结束 - 总共采集 {total_collected} 个数据点")
            self.logger.debug("=== 数据采集循环结束 ===")
            
        except Exception as e:
            self.logger.error(f"数据采集循环严重异常: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")

    def _save_events_to_db(self, events):
        """保存事件数据到数据库"""
        self.logger.debug(f"=== 保存事件数据到数据库 ===")
        self.logger.debug(f"事件数量: {len(events)}")
        
        if not events:
            self.logger.debug("没有事件数据需要保存")
            return
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 批量插入数据
            self.logger.debug("开始批量插入数据...")
            cursor.executemany('''
                INSERT INTO mouse_events 
                (user_id, session_id, timestamp, x, y, event_type, button, wheel_delta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                (event['user_id'], event['session_id'], event['timestamp'],
                 event['x'], event['y'], event['event_type'], 
                 event['button'], event['wheel_delta'])
                for event in events
            ])
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"💾 成功保存 {len(events)} 个事件到数据库")
            self.logger.debug(f"数据库路径: {self.db_path}")
            self.logger.debug(f"用户ID: {events[0]['user_id']}")
            self.logger.debug(f"会话ID: {events[0]['session_id']}")
            self.logger.debug("=== 保存事件数据完成 ===")
            
        except Exception as e:
            self.logger.error(f"保存事件数据失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")

    def get_session_data(self, session_id=None):
        """获取会话数据"""
        self.logger.debug("=== 获取会话数据 ===")
        self.logger.debug(f"参数 - session_id: {session_id}")
        
        if session_id is None:
            session_id = self.session_id
            self.logger.debug(f"使用当前会话ID: {session_id}")
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 查询会话数据
            self.logger.debug("查询会话数据...")
            cursor.execute('''
                SELECT timestamp, x, y, event_type, button, wheel_delta
                FROM mouse_events
                WHERE user_id = ? AND session_id = ?
                ORDER BY timestamp
            ''', (self.user_id, session_id))
            
            rows = cursor.fetchall()
            conn.close()
            
            # 转换为字典格式
            events = []
            for row in rows:
                events.append({
                    'timestamp': row[0],
                    'x': row[1],
                    'y': row[2],
                    'event_type': row[3],
                    'button': row[4],
                    'wheel_delta': row[5]
                })
            
            self.logger.debug(f"获取到 {len(events)} 个事件")
            self.logger.debug("=== 获取会话数据完成 ===")
            return events
            
        except Exception as e:
            self.logger.error(f"获取会话数据失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            return []

    def get_user_sessions(self):
        """获取用户的所有会话"""
        self.logger.debug("=== 获取用户会话列表 ===")
        self.logger.debug(f"用户ID: {self.user_id}")
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 查询用户的所有会话
            self.logger.debug("查询用户会话...")
            cursor.execute('''
                SELECT DISTINCT session_id, 
                       MIN(timestamp) as start_time,
                       MAX(timestamp) as end_time,
                       COUNT(*) as event_count
                FROM mouse_events
                WHERE user_id = ?
                GROUP BY session_id
                ORDER BY start_time DESC
            ''', (self.user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # 转换为字典格式
            sessions = []
            for row in rows:
                sessions.append({
                    'session_id': row[0],
                    'start_time': row[1],
                    'end_time': row[2],
                    'event_count': row[3],
                    'duration': row[2] - row[1] if row[2] and row[1] else 0
                })
            
            self.logger.debug(f"获取到 {len(sessions)} 个会话")
            self.logger.debug("=== 获取用户会话列表完成 ===")
            return sessions
            
        except Exception as e:
            self.logger.error(f"获取用户会话失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            return []

    def get_collection_status(self):
        """获取采集状态"""
        self.logger.debug("=== 获取采集状态 ===")
        
        try:
            status = {
                'user_id': self.user_id,
                'session_id': self.session_id,
                'is_collecting': self.is_collecting,
                'thread_alive': self.collection_thread.is_alive() if self.collection_thread else False
            }
            
            # 获取当前会话的事件数量
            if self.session_id:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM mouse_events 
                    WHERE user_id = ? AND session_id = ?
                ''', (self.user_id, self.session_id))
                event_count = cursor.fetchone()[0]
                conn.close()
                status['current_session_events'] = event_count
                self.logger.debug(f"当前会话事件数量: {event_count}")
            
            self.logger.debug(f"采集状态: {status}")
            self.logger.debug("=== 获取采集状态完成 ===")
            return status
            
        except Exception as e:
            self.logger.error(f"获取采集状态失败: {str(e)}")
            self.logger.debug(f"异常详情: {traceback.format_exc()}")
            return {} 