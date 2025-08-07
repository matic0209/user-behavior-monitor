#!/usr/bin/env python3
"""
心跳功能演示脚本
展示心跳功能在主程序中的集成
"""

import time
import threading
import json
import urllib.request
import urllib.parse
import urllib.error
import sys

class HeartbeatDemo:
    """心跳功能演示类"""
    
    def __init__(self):
        """初始化演示"""
        self.heartbeat_url = "http://127.0.0.1:26002/heartbeat"
        self.heartbeat_interval = 10  # 10秒间隔，便于演示
        self.heartbeat_thread = None
        self.last_heartbeat_time = 0
        self.is_running = False
        
        # 统计信息
        self.stats = {
            'heartbeat_sent': 0,
            'heartbeat_failed': 0
        }
        
        print("=== 心跳功能演示 ===")
        print(f"心跳地址: {self.heartbeat_url}")
        print(f"心跳间隔: {self.heartbeat_interval} 秒")
        print("=" * 30)

    def _send_heartbeat(self):
        """发送心跳请求"""
        try:
            heartbeat_data = {"type": 4}
            
            # 准备请求数据
            data = json.dumps(heartbeat_data).encode('utf-8')
            headers = {
                'Content-Type': 'application/json'
            }
            
            # 创建请求
            req = urllib.request.Request(
                self.heartbeat_url,
                data=data,
                headers=headers,
                method='POST'
            )
            
            # 发送请求
            with urllib.request.urlopen(req, timeout=5) as response:
                response_code = response.getcode()
                if response_code == 200:
                    self.stats['heartbeat_sent'] += 1
                    print(f"✅ 心跳发送成功 (第{self.stats['heartbeat_sent']}次)")
                    return True
                else:
                    print(f"❌ 心跳发送失败，状态码: {response_code}")
                    self.stats['heartbeat_failed'] += 1
                    return False
                    
        except urllib.error.URLError as e:
            print(f"❌ 心跳发送失败 (网络错误): {str(e)}")
            self.stats['heartbeat_failed'] += 1
            return False
        except Exception as e:
            print(f"❌ 心跳发送失败: {str(e)}")
            self.stats['heartbeat_failed'] += 1
            return False

    def _heartbeat_worker(self):
        """心跳工作线程"""
        print(f"🚀 心跳线程启动，间隔: {self.heartbeat_interval} 秒")
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # 检查是否需要发送心跳
                if current_time - self.last_heartbeat_time >= self.heartbeat_interval:
                    self._send_heartbeat()
                    self.last_heartbeat_time = current_time
                
                # 等待一段时间
                time.sleep(1)  # 每1秒检查一次
                
            except Exception as e:
                print(f"❌ 心跳线程异常: {str(e)}")
                time.sleep(5)  # 异常时等待更长时间

    def _start_heartbeat(self):
        """启动心跳线程"""
        try:
            if self.heartbeat_thread is None or not self.heartbeat_thread.is_alive():
                self.heartbeat_thread = threading.Thread(
                    target=self._heartbeat_worker,
                    daemon=True,
                    name="HeartbeatThread"
                )
                self.heartbeat_thread.start()
                print("✅ 心跳线程已启动")
                return True
            else:
                print("ℹ️ 心跳线程已在运行")
                return True
        except Exception as e:
            print(f"❌ 启动心跳线程失败: {str(e)}")
            return False

    def _stop_heartbeat(self):
        """停止心跳线程"""
        try:
            if self.heartbeat_thread and self.heartbeat_thread.is_alive():
                print("🛑 正在停止心跳线程...")
                return True
        except Exception as e:
            print(f"❌ 停止心跳线程失败: {str(e)}")
            return False

    def _get_heartbeat_stats(self):
        """获取心跳统计信息"""
        stats = {
            'heartbeat_sent': self.stats.get('heartbeat_sent', 0),
            'heartbeat_failed': self.stats.get('heartbeat_failed', 0),
            'success_rate': 0.0
        }
        
        total = stats['heartbeat_sent'] + stats['heartbeat_failed']
        if total > 0:
            stats['success_rate'] = (stats['heartbeat_sent'] / total) * 100
        
        return stats

    def start(self):
        """启动演示"""
        print("🚀 启动心跳功能演示...")
        self.is_running = True
        
        # 启动心跳线程
        self._start_heartbeat()
        
        print("📋 演示说明:")
        print("   - 系统将每10秒发送一次心跳")
        print("   - 心跳数据格式: {\"type\": 4}")
        print("   - 按 Ctrl+C 停止演示")
        print("=" * 30)
        
        try:
            # 主循环
            while self.is_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号...")
            self.stop()

    def stop(self):
        """停止演示"""
        print("🛑 正在停止演示...")
        
        # 停止心跳线程
        self._stop_heartbeat()
        
        self.is_running = False
        
        # 显示统计信息
        stats = self._get_heartbeat_stats()
        print("\n📊 心跳统计信息:")
        print(f"   - 发送成功: {stats['heartbeat_sent']} 次")
        print(f"   - 发送失败: {stats['heartbeat_failed']} 次")
        print(f"   - 成功率: {stats['success_rate']:.1f}%")
        
        print("✅ 演示结束")

def main():
    """主函数"""
    print("心跳功能演示")
    print("=" * 30)
    print("此演示展示了心跳功能如何集成到主程序中")
    print("请确保模拟心跳服务器正在运行:")
    print("python3 mock_heartbeat_server.py")
    print("=" * 30)
    
    # 检查服务器是否运行
    try:
        import urllib.request
        response = urllib.request.urlopen('http://127.0.0.1:26002/', timeout=5)
        print("✅ 心跳服务器正在运行")
    except:
        print("❌ 心跳服务器未运行")
        print("请先启动模拟服务器: python3 mock_heartbeat_server.py")
        return 1
    
    # 创建并启动演示
    demo = HeartbeatDemo()
    demo.start()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 