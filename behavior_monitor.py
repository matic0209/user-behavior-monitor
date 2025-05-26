import sys
import time
import threading
import queue
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                            QSystemTrayIcon, QMenu, QAction, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont
from pynput import mouse, keyboard
from feature_engineering import FeatureExtractor
from behavior_classifier import BehaviorClassifier, BehaviorAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('behavior_monitor.log'),
        logging.StreamHandler()
    ]
)

class EventCollector(QObject):
    """事件收集器"""
    event_signal = pyqtSignal(tuple)
    
    def __init__(self):
        super().__init__()
        self.events = []
        self.is_collecting = False
        self.mouse_listener = None
        self.keyboard_listener = None
        
    def start(self):
        """开始收集事件"""
        self.is_collecting = True
        self.events = []
        
        # 启动鼠标监听
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self.mouse_listener.start()
        
        # 启动键盘监听
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()
        
    def stop(self):
        """停止收集事件"""
        self.is_collecting = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            
    def _on_mouse_move(self, x, y):
        """处理鼠标移动事件"""
        if self.is_collecting:
            event = ('mouse_move', 'user1', str(time.time()), 'mouse_move', f'({x}, {y})')
            self.events.append(event)
            self.event_signal.emit(event)
            
    def _on_mouse_click(self, x, y, button, pressed):
        """处理鼠标点击事件"""
        if self.is_collecting:
            event = ('mouse_click', 'user1', str(time.time()), 
                    f'mouse_{button}_{"press" if pressed else "release"}', 
                    f'({x}, {y})')
            self.events.append(event)
            self.event_signal.emit(event)
            
    def _on_mouse_scroll(self, x, y, dx, dy):
        """处理鼠标滚动事件"""
        if self.is_collecting:
            event = ('mouse_scroll', 'user1', str(time.time()), 
                    'mouse_scroll', f'({dx}, {dy})')
            self.events.append(event)
            self.event_signal.emit(event)
            
    def _on_key_press(self, key):
        """处理键盘按下事件"""
        if self.is_collecting:
            event = ('key_press', 'user1', str(time.time()), 
                    'key_press', str(key))
            self.events.append(event)
            self.event_signal.emit(event)
            
    def _on_key_release(self, key):
        """处理键盘释放事件"""
        if self.is_collecting:
            event = ('key_release', 'user1', str(time.time()), 
                    'key_release', str(key))
            self.events.append(event)
            self.event_signal.emit(event)

class BehaviorMonitor(QMainWindow):
    """行为监控主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle('用户行为监控系统')
        self.setGeometry(100, 100, 800, 600)
        
        # 初始化组件
        self.event_collector = EventCollector()
        self.feature_extractor = FeatureExtractor()
        self.classifier = BehaviorClassifier()
        self.analyzer = BehaviorAnalyzer(self.classifier)
        
        # 创建UI
        self._create_ui()
        
        # 创建系统托盘图标
        self._create_tray_icon()
        
        # 初始化定时器
        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self._analyze_behavior)
        self.analysis_timer.start(5000)  # 每5秒分析一次
        
        # 事件队列
        self.event_queue = queue.Queue()
        
        # 启动事件收集
        self.event_collector.event_signal.connect(self._on_event)
        self.event_collector.start()
        
    def _create_ui(self):
        """创建用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        layout = QVBoxLayout(central_widget)
        
        # 状态显示
        status_layout = QHBoxLayout()
        self.status_label = QLabel('监控状态: 运行中')
        self.status_label.setFont(QFont('Arial', 12))
        status_layout.addWidget(self.status_label)
        
        # 控制按钮
        self.start_button = QPushButton('开始监控')
        self.stop_button = QPushButton('停止监控')
        self.start_button.clicked.connect(self._start_monitoring)
        self.stop_button.clicked.connect(self._stop_monitoring)
        status_layout.addWidget(self.start_button)
        status_layout.addWidget(self.stop_button)
        
        layout.addLayout(status_layout)
        
        # 事件日志
        self.event_log = QTextEdit()
        self.event_log.setReadOnly(True)
        layout.addWidget(self.event_log)
        
        # 行为分析结果
        self.analysis_log = QTextEdit()
        self.analysis_log.setReadOnly(True)
        layout.addWidget(self.analysis_log)
        
    def _create_tray_icon(self):
        """创建系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('icon.png'))  # 需要添加图标文件
        
        # 创建托盘菜单
        tray_menu = QMenu()
        show_action = QAction('显示', self)
        quit_action = QAction('退出', self)
        
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self._quit_application)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
    def _on_event(self, event):
        """处理新事件"""
        self.event_queue.put(event)
        self.event_log.append(f"{datetime.now().strftime('%H:%M:%S')} - {event}")
        
    def _analyze_behavior(self):
        """分析行为"""
        if self.event_queue.empty():
            return
            
        # 获取最近的事件
        events = []
        while not self.event_queue.empty():
            events.append(self.event_queue.get())
            
        # 提取特征
        features = self.feature_extractor.extract_features(events)
        
        # 分析行为
        result = self.analyzer.analyze_behavior(features)
        
        # 显示分析结果
        self.analysis_log.append(
            f"\n{datetime.now().strftime('%H:%M:%S')} - 行为分析结果:\n"
            f"类型: {result['behavior_type']}\n"
            f"置信度: {result['confidence']:.2f}\n"
            f"是否异常: {'是' if result['is_anomaly'] else '否'}\n"
        )
        
        # 如果检测到异常，显示警告
        if result['is_anomaly']:
            self._show_alert(result)
            
    def _show_alert(self, result):
        """显示警告"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle('行为异常警告')
        msg.setText(f'检测到{result["behavior_type"]}!')
        msg.setInformativeText(result['behavior_description'])
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
        # 同时显示系统托盘通知
        self.tray_icon.showMessage(
            '行为异常警告',
            f'检测到{result["behavior_type"]}!\n{result["behavior_description"]}',
            QSystemTrayIcon.Warning,
            5000
        )
        
    def _start_monitoring(self):
        """开始监控"""
        self.event_collector.start()
        self.status_label.setText('监控状态: 运行中')
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
    def _stop_monitoring(self):
        """停止监控"""
        self.event_collector.stop()
        self.status_label.setText('监控状态: 已停止')
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
    def _quit_application(self):
        """退出应用"""
        self.event_collector.stop()
        QApplication.quit()
        
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            '用户行为监控系统',
            '应用程序已最小化到系统托盘',
            QSystemTrayIcon.Information,
            2000
        )

def main():
    app = QApplication(sys.argv)
    window = BehaviorMonitor()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 