#!/usr/bin/env python3
"""
Linux/麒麟系统输入权限检查脚本
检查pynput等输入监控库的权限和兼容性
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def check_system_info():
    """检查系统信息"""
    print("=" * 50)
    print("系统信息检查")
    print("=" * 50)
    print(f"操作系统: {platform.system()}")
    print(f"发行版: {platform.platform()}")
    print(f"架构: {platform.machine()}")
    print(f"Python版本: {platform.python_version()}")
    
    # 检查是否为Linux
    if platform.system() != 'Linux':
        print("⚠️  警告: 此脚本主要用于Linux/麒麟系统")
        return False
    
    return True

def check_display_environment():
    """检查显示环境"""
    print("\n" + "=" * 50)
    print("显示环境检查")
    print("=" * 50)
    
    # 检查X11
    display = os.environ.get('DISPLAY')
    if display:
        print(f"✓ X11 DISPLAY: {display}")
    else:
        print("✗ 未设置DISPLAY环境变量")
        print("  可能需要: export DISPLAY=:0")
    
    # 检查Wayland
    wayland_display = os.environ.get('WAYLAND_DISPLAY')
    if wayland_display:
        print(f"✓ Wayland DISPLAY: {wayland_display}")
    
    # 检查桌面环境
    desktop = os.environ.get('XDG_CURRENT_DESKTOP')
    if desktop:
        print(f"✓ 桌面环境: {desktop}")
    
    session_type = os.environ.get('XDG_SESSION_TYPE')
    if session_type:
        print(f"✓ 会话类型: {session_type}")

def check_user_permissions():
    """检查用户权限"""
    print("\n" + "=" * 50)
    print("用户权限检查")
    print("=" * 50)
    
    # 检查用户ID
    uid = os.getuid()
    print(f"用户ID: {uid}")
    
    if uid == 0:
        print("⚠️  警告: 当前以root用户运行")
        print("  建议使用普通用户运行，避免权限问题")
    
    # 检查用户组
    try:
        import grp
        groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]
        print(f"用户组: {', '.join(groups)}")
        
        # 检查输入相关组
        input_groups = ['input', 'users', 'audio', 'video']
        missing_groups = []
        for group in input_groups:
            if group in groups:
                print(f"✓ 在 {group} 组中")
            else:
                missing_groups.append(group)
        
        if missing_groups:
            print(f"⚠️  建议加入组: {', '.join(missing_groups)}")
            print(f"  命令: sudo usermod -a -G {','.join(missing_groups)} $USER")
    
    except Exception as e:
        print(f"检查用户组失败: {e}")

def check_input_devices():
    """检查输入设备"""
    print("\n" + "=" * 50)
    print("输入设备检查")
    print("=" * 50)
    
    # 检查/dev/input权限
    input_dir = Path('/dev/input')
    if input_dir.exists():
        print(f"✓ /dev/input 目录存在")
        
        # 列出输入设备
        try:
            devices = list(input_dir.glob('event*'))
            print(f"输入设备数量: {len(devices)}")
            
            # 检查权限
            readable_devices = []
            for device in devices[:5]:  # 只检查前5个
                if os.access(device, os.R_OK):
                    readable_devices.append(device.name)
                    
            if readable_devices:
                print(f"✓ 可读设备: {', '.join(readable_devices)}")
            else:
                print("⚠️  无法读取输入设备")
                print("  可能需要加入input组或调整权限")
                
        except Exception as e:
            print(f"检查输入设备失败: {e}")
    else:
        print("✗ /dev/input 目录不存在")

def check_pynput_compatibility():
    """检查pynput兼容性"""
    print("\n" + "=" * 50)
    print("pynput兼容性检查")
    print("=" * 50)
    
    try:
        import pynput
        print(f"✓ pynput已安装: {pynput.__version__}")
        
        # 测试鼠标监听
        print("测试鼠标监听...")
        try:
            from pynput import mouse
            
            def on_move(x, y):
                print(f"鼠标移动: ({x}, {y})")
                return False  # 停止监听
            
            # 短暂监听测试
            listener = mouse.Listener(on_move=on_move)
            listener.start()
            
            import time
            time.sleep(0.1)  # 等待0.1秒
            listener.stop()
            
            print("✓ 鼠标监听测试成功")
            
        except Exception as e:
            print(f"✗ 鼠标监听测试失败: {e}")
            print("  可能的解决方案:")
            print("  1. 检查X11/Wayland权限")
            print("  2. 加入input组")
            print("  3. 使用sudo运行 (不推荐)")
        
        # 测试键盘监听
        print("测试键盘监听...")
        try:
            from pynput import keyboard
            
            def on_press(key):
                print(f"按键: {key}")
                return False  # 停止监听
            
            # 短暂监听测试
            listener = keyboard.Listener(on_press=on_press)
            listener.start()
            
            time.sleep(0.1)  # 等待0.1秒
            listener.stop()
            
            print("✓ 键盘监听测试成功")
            
        except Exception as e:
            print(f"✗ 键盘监听测试失败: {e}")
            
    except ImportError:
        print("✗ pynput未安装")
        print("  安装命令: pip3 install pynput")
        return False
    
    return True

def check_alternative_libraries():
    """检查替代输入监控库"""
    print("\n" + "=" * 50)
    print("替代库检查")
    print("=" * 50)
    
    # 检查python-evdev (Linux专用)
    try:
        import evdev
        print(f"✓ python-evdev已安装: {evdev.__version__}")
        
        # 列出可用设备
        try:
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            print(f"evdev设备数量: {len(devices)}")
            for device in devices[:3]:  # 只显示前3个
                print(f"  - {device.name} ({device.path})")
        except Exception as e:
            print(f"  获取evdev设备失败: {e}")
            
    except ImportError:
        print("python-evdev未安装")
        print("  安装命令: pip3 install evdev")
    
    # 检查python-xlib
    try:
        import Xlib
        print("✓ python-xlib已安装")
    except ImportError:
        print("python-xlib未安装")
        print("  安装命令: pip3 install python-xlib")

def generate_recommendations():
    """生成建议"""
    print("\n" + "=" * 50)
    print("建议和解决方案")
    print("=" * 50)
    
    print("1. 权限配置:")
    print("   sudo usermod -a -G input,audio,video $USER")
    print("   newgrp input  # 或重新登录")
    print()
    
    print("2. 环境变量:")
    print("   export DISPLAY=:0")
    print("   export XDG_SESSION_TYPE=x11")
    print()
    
    print("3. 麒麟系统特殊配置:")
    print("   # 银河麒麟/中标麒麟可能需要:")
    print("   sudo chmod 644 /dev/input/event*")
    print("   sudo systemctl restart lightdm  # 重启显示管理器")
    print()
    
    print("4. 安全策略:")
    print("   # 检查SELinux/AppArmor状态")
    print("   sestatus  # 或 getenforce")
    print("   sudo setenforce 0  # 临时禁用SELinux")
    print()
    
    print("5. 调试命令:")
    print("   xinput list  # 查看输入设备")
    print("   ls -la /dev/input/  # 查看设备权限")
    print("   id  # 查看当前用户和组")

def main():
    """主函数"""
    print("Linux/麒麟系统输入权限检查工具")
    print("用于诊断pynput等输入监控库的兼容性问题")
    print()
    
    # 系统检查
    if not check_system_info():
        print("⚠️  非Linux系统，某些检查可能不准确")
    
    # 各项检查
    check_display_environment()
    check_user_permissions()
    check_input_devices()
    
    # pynput检查
    pynput_ok = check_pynput_compatibility()
    
    # 替代库检查
    check_alternative_libraries()
    
    # 生成建议
    generate_recommendations()
    
    print("\n" + "=" * 50)
    print("检查完成")
    print("=" * 50)
    
    if pynput_ok:
        print("✅ pynput基本可用")
    else:
        print("❌ pynput存在问题，请参考上述建议")

if __name__ == "__main__":
    main()
