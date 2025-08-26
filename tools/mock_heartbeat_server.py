#!/usr/bin/env python3
"""
模拟心跳服务器
用于测试心跳功能
"""

import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class HeartbeatHandler(BaseHTTPRequestHandler):
    """心跳请求处理器"""
    
    def do_POST(self):
        """处理POST请求"""
        try:
            # 解析URL
            parsed_url = urlparse(self.path)
            
            # 检查是否是心跳请求
            if parsed_url.path == '/heartbeat':
                # 读取请求数据
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                # 解析JSON数据
                try:
                    data = json.loads(post_data.decode('utf-8'))
                    print(f"收到心跳请求: {data}")
                    
                    # 检查数据格式
                    if isinstance(data, dict) and 'type' in data:
                        # 发送成功响应
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        
                        response_data = {
                            "status": "success",
                            "message": "heartbeat received",
                            "timestamp": time.time(),
                            "received_data": data
                        }
                        
                        self.wfile.write(json.dumps(response_data).encode('utf-8'))
                        print(f"[SUCCESS] 心跳响应成功: {response_data}")
                        
                    else:
                        # 数据格式错误
                        self.send_response(400)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        
                        error_data = {
                            "status": "error",
                            "message": "Invalid data format",
                            "expected": {"type": "number"}
                        }
                        
                        self.wfile.write(json.dumps(error_data).encode('utf-8'))
                        print(f"[ERROR] 心跳数据格式错误: {data}")
                        
                except json.JSONDecodeError as e:
                    # JSON解析错误
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    
                    error_data = {
                        "status": "error",
                        "message": "Invalid JSON format",
                        "error": str(e)
                    }
                    
                    self.wfile.write(json.dumps(error_data).encode('utf-8'))
                    print(f"[ERROR] JSON解析错误: {e}")
                    
            else:
                # 路径不存在
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                
                error_data = {
                    "status": "error",
                    "message": "Endpoint not found",
                    "path": parsed_url.path
                }
                
                self.wfile.write(json.dumps(error_data).encode('utf-8'))
                print(f"[ERROR] 路径不存在: {parsed_url.path}")
                
        except Exception as e:
            # 服务器内部错误
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            error_data = {
                "status": "error",
                "message": "Internal server error",
                "error": str(e)
            }
            
            self.wfile.write(json.dumps(error_data).encode('utf-8'))
            print(f"[ERROR] 服务器内部错误: {e}")
    
    def do_GET(self):
        """处理GET请求"""
        # 解析URL
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == '/':
            # 根路径，返回服务器信息
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            info_data = {
                "status": "running",
                "server": "Mock Heartbeat Server",
                "version": "1.0.0",
                "endpoints": {
                    "POST /heartbeat": "Send heartbeat signal",
                    "GET /": "Server information"
                },
                "timestamp": time.time()
            }
            
            self.wfile.write(json.dumps(info_data, indent=2).encode('utf-8'))
            print(f"[INFO] 服务器信息请求")
            
        else:
            # 路径不存在
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            error_data = {
                "status": "error",
                "message": "Endpoint not found",
                "path": parsed_url.path
            }
            
            self.wfile.write(json.dumps(error_data).encode('utf-8'))
            print(f"[ERROR] 路径不存在: {parsed_url.path}")
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def start_server(host='127.0.0.1', port=26002):
    """启动心跳服务器"""
    try:
        server = HTTPServer((host, port), HeartbeatHandler)
        print(f"[START] 心跳服务器启动成功!")
        print(f"[ADDR] 地址: http://{host}:{port}")
        print(f"[ENDP] 支持的端点:")
        print(f"   - POST /heartbeat: 接收心跳信号")
        print(f"   - GET /: 服务器信息")
        print(f"[STOP] 按 Ctrl+C 停止服务器")
        print("=" * 50)
        
        # 启动服务器
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n[STOP] 收到停止信号，正在关闭服务器...")
        server.shutdown()
        print("[DONE] 服务器已关闭")
    except Exception as e:
        print(f"[ERROR] 服务器启动失败: {e}")

def main():
    """主函数"""
    print("模拟心跳服务器")
    print("=" * 30)
    
    # 启动服务器
    start_server()

if __name__ == "__main__":
    main() 