import pynput
from pynput import mouse
import time
import logging
import queue
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MouseEventCapture:
    def __init__(self, event_queue):
        """
        初始化鼠标事件捕获器
        
        参数:
        event_queue: 事件队列，用于存储捕获的事件
        """
        self.event_queue = event_queue
        self.running = False
        self.listener = None
        
        # 事件类型映射
        self.event_types = {
            'move': 1,
            'click': 2,
            'scroll': 3,
            'drag': 4,
            'release': 5
        }
        
        logging.info("MouseEventCapture initialized")
    
    def on_move(self, x, y):
        """鼠标移动事件处理"""
        if self.running:
            event = {
                'timestamp': time.time(),
                'screen_x': x,
                'screen_y': y,
                'event_type': self.event_types['move']
            }
            self.event_queue.put(event)
    
    def on_click(self, x, y, button, pressed):
        """鼠标点击事件处理"""
        if self.running:
            event = {
                'timestamp': time.time(),
                'screen_x': x,
                'screen_y': y,
                'event_type': self.event_types['click'] if pressed else self.event_types['release']
            }
            self.event_queue.put(event)
    
    def on_scroll(self, x, y, dx, dy):
        """鼠标滚动事件处理"""
        if self.running:
            event = {
                'timestamp': time.time(),
                'screen_x': x,
                'screen_y': y,
                'event_type': self.event_types['scroll']
            }
            self.event_queue.put(event)
    
    def start(self):
        """启动事件捕获"""
        self.running = True
        self.listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        self.listener.start()
        logging.info("Mouse event capture started")
    
    def stop(self):
        """停止事件捕获"""
        self.running = False
        if self.listener:
            self.listener.stop()
        logging.info("Mouse event capture stopped")

# 使用示例
if __name__ == "__main__":
    # 创建事件队列
    event_queue = queue.Queue()
    
    # 初始化事件捕获器
    capture = MouseEventCapture(event_queue)
    
    # 启动事件捕获
    capture.start()
    
    try:
        # 主循环
        while True:
            try:
                # 从队列中获取事件
                event = event_queue.get_nowait()
                print(f"Event: {event}")
            except queue.Empty:
                pass
            
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping event capture...")
        capture.stop() 