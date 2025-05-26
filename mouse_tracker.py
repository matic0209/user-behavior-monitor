from pynput import mouse
import time
from datetime import datetime
import sqlite3
import os

class MouseEventTracker:
    def __init__(self):
        self.is_tracking = False
        self.start_time = None
        self.mouse_listener = None
        
        # 创建内存数据库连接
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        
        # 创建事件表
        self.cursor.execute('''
            CREATE TABLE mouse_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_timestamp TEXT,
                client_timestamp REAL,
                button TEXT,
                state TEXT,
                x INTEGER,
                y INTEGER
            )
        ''')
        self.conn.commit()
        
    def start_tracking(self):
        if self.is_tracking:
            return
            
        self.is_tracking = True
        self.start_time = time.time()
        
        # 清空表
        self.cursor.execute('DELETE FROM mouse_events')
        self.conn.commit()
        
        # 启动鼠标监听器
        self.mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll
        )
        self.mouse_listener.start()
        
    def stop_tracking(self):
        if not self.is_tracking:
            return
            
        self.is_tracking = False
        if self.mouse_listener:
            self.mouse_listener.stop()
            
    def _on_move(self, x, y):
        if not self.is_tracking:
            return
            
        record_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        client_time = time.time() - self.start_time
        
        self._save_event(
            record_time,
            client_time,
            'none',
            'move',
            x,
            y
        )
        
    def _on_click(self, x, y, button, pressed):
        if not self.is_tracking:
            return
            
        record_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        client_time = time.time() - self.start_time
        
        self._save_event(
            record_time,
            client_time,
            str(button),
            'pressed' if pressed else 'released',
            x,
            y
        )
        
    def _on_scroll(self, x, y, dx, dy):
        if not self.is_tracking:
            return
            
        record_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        client_time = time.time() - self.start_time
        
        self._save_event(
            record_time,
            client_time,
            'scroll',
            f'scroll_{"up" if dy > 0 else "down"}',
            x,
            y
        )
        
    def _save_event(self, record_timestamp, client_timestamp, button, state, x, y):
        # 将事件保存到数据库
        self.cursor.execute('''
            INSERT INTO mouse_events 
            (record_timestamp, client_timestamp, button, state, x, y)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (record_timestamp, client_timestamp, button, state, x, y))
        self.conn.commit()
        
    def get_event_stream(self):
        """获取所有事件"""
        self.cursor.execute('SELECT * FROM mouse_events ORDER BY id')
        return self.cursor.fetchall()
    
    def get_events_by_time_range(self, start_time, end_time):
        """获取指定时间范围内的事件"""
        self.cursor.execute('''
            SELECT * FROM mouse_events 
            WHERE client_timestamp BETWEEN ? AND ?
            ORDER BY id
        ''', (start_time, end_time))
        return self.cursor.fetchall()
    
    def get_events_by_type(self, event_type):
        """获取指定类型的事件"""
        self.cursor.execute('''
            SELECT * FROM mouse_events 
            WHERE state = ?
            ORDER BY id
        ''', (event_type,))
        return self.cursor.fetchall()
    
    def get_event_count(self):
        """获取事件总数"""
        self.cursor.execute('SELECT COUNT(*) FROM mouse_events')
        return self.cursor.fetchone()[0]
    
    def clear_events(self):
        """清除所有事件"""
        self.cursor.execute('DELETE FROM mouse_events')
        self.conn.commit()
    
    def __del__(self):
        """清理数据库连接"""
        if hasattr(self, 'conn'):
            self.conn.close()

# 使用示例
if __name__ == "__main__":
    tracker = MouseEventTracker()
    
    print("开始追踪鼠标事件...")
    tracker.start_tracking()
    
    try:
        # 保持程序运行，直到用户按下 Ctrl+C
        while True:
            time.sleep(1)
            # 每5秒打印一次事件统计
            if int(time.time()) % 5 == 0:
                print(f"已记录 {tracker.get_event_count()} 个事件")
    except KeyboardInterrupt:
        print("\n停止追踪鼠标事件...")
        tracker.stop_tracking()
        
        # 打印最后10个事件
        print("\n最后10个事件:")
        events = tracker.get_event_stream()
        for event in events[-10:]:
            print(f"ID: {event[0]}, 时间: {event[1]}, 按钮: {event[3]}, 状态: {event[4]}, 坐标: ({event[5]}, {event[6]})") 