import time
import threading
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader

try:
    from pynput import mouse
    from pynput.mouse import Controller
    PYNPUT_AVAILABLE = True
except Exception:
    PYNPUT_AVAILABLE = False


class LinuxMouseCollector:
    """Linux/Kylin 平台鼠标采集器

    设计目标：
    - 与 WindowsMouseCollector 保持尽量一致的接口
    - 使用 pynput 进行全局鼠标监听；同时用轮询方式保证采样频率可控
    - 将事件写入同一 SQLite 表结构：mouse_events(user_id, session_id, timestamp, x, y, event_type, button, wheel_delta)
    """

    def __init__(self, user_id):
        self.logger = Logger()
        self.config = ConfigLoader()

        self.user_id = user_id
        self.session_id = None
        self.is_collecting = False
        self.collection_thread = None

        self.db_path = Path(self.config.get_paths()['database'])
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

        # 控制参数
        data_collection_config = self.config.get_data_collection_config()
        self.interval = data_collection_config.get('collection_interval', 0.1)
        self.max_buffer_size = data_collection_config.get('max_buffer_size', 10000)
        target = data_collection_config.get('target_samples_per_session', None)
        try:
            self.target_samples = int(target) if target is not None else None
        except Exception:
            self.target_samples = None

        # 鼠标控制器与监听器
        self._mouse_controller = Controller() if PYNPUT_AVAILABLE else None
        self._mouse_listener = None
        self._last_position = None

    def _init_database(self):
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
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
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_session ON mouse_events(user_id, session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON mouse_events(timestamp)')
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {str(e)}")
            raise

    def start_collection(self):
        if self.is_collecting:
            self.logger.warning("数据采集已在运行中")
            return False

        if not PYNPUT_AVAILABLE:
            self.logger.error("pynput 不可用，无法在 Linux/Kylin 上采集鼠标")
            return False

        try:
            self.session_id = str(uuid.uuid4())
            self.is_collecting = True
            self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
            self.collection_thread.start()
            return True
        except Exception as e:
            self.logger.error(f"启动数据采集失败: {str(e)}")
            self.is_collecting = False
            return False

    def stop_collection(self):
        if not self.is_collecting:
            return
        try:
            self.is_collecting = False
            if self.collection_thread and self.collection_thread.is_alive():
                self.collection_thread.join(timeout=2)
        except Exception as e:
            self.logger.error(f"停止数据采集失败: {str(e)}")

    def _collection_loop(self):
        buffer = []
        last_save_time = time.time()
        save_interval = 5.0
        total_collected = 0

        # 事件监听：点击/滚轮等（移动用轮询采样）
        def on_click(x, y, button, pressed):
            try:
                event = {
                    'user_id': self.user_id,
                    'session_id': self.session_id,
                    'timestamp': time.time(),
                    'x': int(x),
                    'y': int(y),
                    'event_type': 'pressed' if pressed else 'released',
                    'button': str(button),
                    'wheel_delta': 0
                }
                buffer.append(event)
            except Exception:
                pass

        def on_scroll(x, y, dx, dy):
            try:
                event = {
                    'user_id': self.user_id,
                    'session_id': self.session_id,
                    'timestamp': time.time(),
                    'x': int(x),
                    'y': int(y),
                    'event_type': 'scroll',
                    'button': None,
                    'wheel_delta': int(dy)
                }
                buffer.append(event)
            except Exception:
                pass

        self._mouse_listener = mouse.Listener(on_click=on_click, on_scroll=on_scroll)
        try:
            self._mouse_listener.start()
        except Exception:
            # 监听失败不阻断轮询
            self._mouse_listener = None

        try:
            while self.is_collecting:
                try:
                    # 轮询位置，按配置频率采样
                    pos = self._mouse_controller.position if self._mouse_controller else (0, 0)
                    x, y = int(pos[0]), int(pos[1])
                    event = {
                        'user_id': self.user_id,
                        'session_id': self.session_id,
                        'timestamp': time.time(),
                        'x': x,
                        'y': y,
                        'event_type': 'move',
                        'button': None,
                        'wheel_delta': 0
                    }
                    buffer.append(event)
                    total_collected += 1

                    # 保存条件
                    if len(buffer) >= self.max_buffer_size or (time.time() - last_save_time) >= save_interval:
                        self._save_events_to_db(buffer)
                        buffer.clear()
                        last_save_time = time.time()

                    # 达到目标样本，结束
                    if self.target_samples is not None and total_collected >= self.target_samples:
                        if buffer:
                            self._save_events_to_db(buffer)
                            buffer.clear()
                        self.is_collecting = False
                        break

                    time.sleep(self.interval)
                except Exception:
                    time.sleep(self.interval)

            if buffer:
                self._save_events_to_db(buffer)
                buffer.clear()
        finally:
            if self._mouse_listener:
                try:
                    self._mouse_listener.stop()
                except Exception:
                    pass

    def _save_events_to_db(self, events):
        if not events:
            return
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.executemany('''
                INSERT INTO mouse_events (user_id, session_id, timestamp, x, y, event_type, button, wheel_delta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                (e['user_id'], e['session_id'], e['timestamp'], e['x'], e['y'], e['event_type'], e['button'], e['wheel_delta'])
                for e in events
            ])
            conn.commit()
            conn.close()
            self.logger.info(f"💾 成功保存 {len(events)} 个事件到数据库")
        except Exception as e:
            self.logger.error(f"保存事件数据失败: {str(e)}")

    def get_collection_status(self):
        try:
            status = {
                'user_id': self.user_id,
                'session_id': self.session_id,
                'is_collecting': self.is_collecting,
                'thread_alive': self.collection_thread.is_alive() if self.collection_thread else False
            }
            return status
        except Exception as e:
            self.logger.error(f"获取采集状态失败: {str(e)}")
            return {}


