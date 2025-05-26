from pynput import mouse, keyboard
import time
from datetime import datetime
import win32gui

class EventRecorder:
    def __init__(self, db_connection):
        self.conn = db_connection
        self.cursor = self.conn.cursor()
        self.is_recording = False
        self.start_time = None
        self.mouse_listener = None
        self.keyboard_listener = None
        
    def start_recording(self):
        if self.is_recording:
            return
            
        self.is_recording = True
        self.start_time = time.time()
        
        # 启动鼠标监听器
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self.mouse_listener.start()
        
        # 启动键盘监听器
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()
        
    def stop_recording(self):
        if not self.is_recording:
            return
            
        self.is_recording = False
        
        if self.mouse_listener:
            self.mouse_listener.stop()
            
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            
    def _get_active_window_title(self):
        """获取当前活动窗口的标题"""
        try:
            return win32gui.GetWindowText(win32gui.GetForegroundWindow())
        except:
            return "Unknown"
            
    def _save_event(self, event_type, event_data):
        """保存事件到数据库"""
        record_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        client_time = time.time() - self.start_time
        window_title = self._get_active_window_title()
        
        self.cursor.execute('''
            INSERT INTO user_events 
            (record_timestamp, client_timestamp, event_type, event_data, window_title)
            VALUES (?, ?, ?, ?, ?)
        ''', (record_time, client_time, event_type, str(event_data), window_title))
        self.conn.commit()
        
    def _on_mouse_move(self, x, y):
        """处理鼠标移动事件"""
        if not self.is_recording:
            return
        self._save_event('mouse_move', (x, y))
        
    def _on_mouse_click(self, x, y, button, pressed):
        """处理鼠标点击事件"""
        if not self.is_recording:
            return
        self._save_event('mouse_click', {
            'x': x,
            'y': y,
            'button': str(button),
            'pressed': pressed
        })
        
    def _on_mouse_scroll(self, x, y, dx, dy):
        """处理鼠标滚轮事件"""
        if not self.is_recording:
            return
        self._save_event('mouse_scroll', {
            'x': x,
            'y': y,
            'dx': dx,
            'dy': dy
        })
        
    def _on_key_press(self, key):
        """处理键盘按下事件"""
        if not self.is_recording:
            return
        self._save_event('key_press', {
            'key': str(key),
            'time': time.time() - self.start_time
        })
        
    def _on_key_release(self, key):
        """处理键盘释放事件"""
        if not self.is_recording:
            return
        self._save_event('key_release', {
            'key': str(key),
            'time': time.time() - self.start_time
        }) 