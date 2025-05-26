import sqlite3
import time
from datetime import datetime
import numpy as np
from pynput import mouse, keyboard
import win32gui
import win32con
import threading
from behavior_analyzer import BehaviorAnalyzer
from event_recorder import EventRecorder
from alert_manager import AlertManager

class UserBehaviorMonitor:
    def __init__(self):
        # 初始化数据库
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        
        # 创建事件表
        self.cursor.execute('''
            CREATE TABLE user_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_timestamp TEXT,
                client_timestamp REAL,
                event_type TEXT,
                event_data TEXT,
                window_title TEXT
            )
        ''')
        self.conn.commit()
        
        # 初始化组件
        self.event_recorder = EventRecorder(self.conn)
        self.behavior_analyzer = BehaviorAnalyzer()
        self.alert_manager = AlertManager()
        
        # 状态标志
        self.is_monitoring = False
        self.start_time = None
        
        # 事件监听器
        self.mouse_listener = None
        self.keyboard_listener = None
        
    def start_monitoring(self):
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.start_time = time.time()
        
        # 清空数据库
        self.cursor.execute('DELETE FROM user_events')
        self.conn.commit()
        
        # 启动事件记录器
        self.event_recorder.start_recording()
        
        # 启动行为分析线程
        self.analysis_thread = threading.Thread(target=self._analysis_loop)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
        
    def stop_monitoring(self):
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        self.event_recorder.stop_recording()
        
    def _analysis_loop(self):
        """持续分析用户行为的循环"""
        while self.is_monitoring:
            # 获取最近的事件数据
            self.cursor.execute('''
                SELECT * FROM user_events 
                ORDER BY id DESC LIMIT 1000
            ''')
            recent_events = self.cursor.fetchall()
            
            if recent_events:
                # 进行异常检测
                is_anomaly, confidence = self.behavior_analyzer.detect_anomaly(recent_events)
                
                if is_anomaly:
                    # 触发告警
                    self.alert_manager.trigger_alert(
                        f"检测到异常行为！置信度: {confidence:.2f}",
                        force_logout=True
                    )
            
            time.sleep(1)  # 每秒检查一次
    
    def __del__(self):
        """清理资源"""
        self.stop_monitoring()
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    monitor = UserBehaviorMonitor()
    
    print("开始监控用户行为...")
    monitor.start_monitoring()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止监控...")
        monitor.stop_monitoring() 