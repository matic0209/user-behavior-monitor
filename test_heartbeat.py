#!/usr/bin/env python3
"""
心跳功能测试脚本
用于测试心跳上报功能是否正常工作
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import time
import sys

def test_heartbeat():
    """测试心跳功能"""
    heartbeat_url = "http://127.0.0.1:26002/heartbeat"
    heartbeat_data = {"type": 4}
    
    print("=== 心跳功能测试 ===")
    print(f"目标地址: {heartbeat_url}")
    print(f"发送数据: {heartbeat_data}")
    print("=" * 30)
    
    try:
        # 准备请求数据
        data = json.dumps(heartbeat_data).encode('utf-8')
        headers = {
            'Content-Type': 'application/json'
        }
        
        # 创建请求
        req = urllib.request.Request(
            heartbeat_url,
            data=data,
            headers=headers,
            method='POST'
        )
        
        print("正在发送心跳请求...")
        
        # 发送请求
        with urllib.request.urlopen(req, timeout=10) as response:
            response_code = response.getcode()
            response_data = response.read()
            
            print(f"[SUCCESS] 心跳发送成功!")
            print(f"状态码: {response_code}")
            print(f"响应数据: {response_data.decode('utf-8')}")
            
            return True
            
    except urllib.error.URLError as e:
        print(f"[ERROR] 心跳发送失败 (网络错误): {str(e)}")
        print("可能的原因:")
        print("1. 目标服务器未启动")
        print("2. 网络连接问题")
        print("3. 防火墙阻止")
        return False
    except Exception as e:
        print(f"[ERROR] 心跳发送失败: {str(e)}")
        return False

def test_continuous_heartbeat():
    """测试连续心跳"""
    print("\n=== 连续心跳测试 ===")
    print("将每30秒发送一次心跳，按Ctrl+C停止")
    print("=" * 30)
    
    interval = 30  # 30秒间隔
    count = 0
    
    try:
        while True:
            count += 1
            print(f"\n第 {count} 次心跳发送...")
            
            if test_heartbeat():
                print(f"[SUCCESS] 第 {count} 次心跳成功")
            else:
                print(f"[ERROR] 第 {count} 次心跳失败")
            
            print(f"等待 {interval} 秒后发送下一次心跳...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n测试停止，共发送 {count} 次心跳")
        return count

def main():
    """主函数"""
    print("心跳功能测试工具")
    print("=" * 30)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        test_continuous_heartbeat()
    else:
        # 单次测试
        success = test_heartbeat()
        if success:
            print("\n[SUCCESS] 心跳功能测试通过")
            sys.exit(0)
        else:
            print("\n[ERROR] 心跳功能测试失败")
            sys.exit(1)

if __name__ == "__main__":
    main() 