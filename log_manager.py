#!/usr/bin/env python3
"""
日志管理工具
用于查看和控制日志文件大小
"""

import os
import shutil
import time
from pathlib import Path
from datetime import datetime

class LogManager:
    def __init__(self):
        self.log_dir = Path.cwd() / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def get_log_info(self):
        """获取日志文件信息"""
        print("=== 日志文件信息 ===")
        
        if not self.log_dir.exists():
            print("日志目录不存在")
            return
        
        total_size = 0
        file_count = 0
        log_files = []
        
        for log_file in self.log_dir.glob('*.log*'):
            size = log_file.stat().st_size
            modified_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            total_size += size
            file_count += 1
            
            log_files.append({
                'name': log_file.name,
                'size': size,
                'modified': modified_time
            })
        
        # 按大小排序
        log_files.sort(key=lambda x: x['size'], reverse=True)
        
        print(f"日志目录: {self.log_dir}")
        print(f"总文件数: {file_count}")
        print(f"总大小: {total_size/1024/1024:.1f} MB")
        print("\n文件详情:")
        
        for file_info in log_files:
            size_mb = file_info['size'] / 1024 / 1024
            print(f"  {file_info['name']}: {size_mb:.1f} MB ({file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')})")

    def cleanup_old_logs(self, days=7, max_files=50):
        """清理旧日志文件"""
        print(f"=== 清理旧日志文件 (超过{days}天，最多保留{max_files}个文件) ===")
        
        if not self.log_dir.exists():
            print("日志目录不存在")
            return
        
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)
        
        deleted_count = 0
        deleted_size = 0
        
        # 删除超过指定天数的文件
        for log_file in self.log_dir.glob('*.log*'):
            if log_file.stat().st_mtime < cutoff_time:
                size = log_file.stat().st_size
                log_file.unlink()
                deleted_count += 1
                deleted_size += size
                print(f"已删除: {log_file.name} ({size/1024:.1f} KB)")
        
        # 限制文件总数
        log_files = list(self.log_dir.glob('*.log'))
        if len(log_files) > max_files:
            # 按修改时间排序，删除最旧的文件
            log_files.sort(key=lambda x: x.stat().st_mtime)
            files_to_delete = log_files[:-max_files]
            
            for file in files_to_delete:
                size = file.stat().st_size
                file.unlink()
                deleted_count += 1
                deleted_size += size
                print(f"已删除: {file.name} ({size/1024:.1f} KB)")
        
        print(f"\n清理完成:")
        print(f"  删除文件数: {deleted_count}")
        print(f"  释放空间: {deleted_size/1024/1024:.1f} MB")

    def compress_logs(self):
        """压缩日志文件"""
        print("=== 压缩日志文件 ===")
        
        if not self.log_dir.exists():
            print("日志目录不存在")
            return
        
        compressed_count = 0
        
        for log_file in self.log_dir.glob('*.log'):
            # 跳过已经是压缩文件的
            if log_file.name.endswith('.gz'):
                continue
            
            # 检查文件大小，只压缩大于1MB的文件
            if log_file.stat().st_size > 1024 * 1024:
                try:
                    import gzip
                    
                    # 创建压缩文件
                    compressed_file = log_file.with_suffix('.log.gz')
                    
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # 删除原文件
                    original_size = log_file.stat().st_size
                    compressed_size = compressed_file.stat().st_size
                    log_file.unlink()
                    
                    compressed_count += 1
                    print(f"已压缩: {log_file.name} ({original_size/1024:.1f} KB -> {compressed_size/1024:.1f} KB)")
                    
                except ImportError:
                    print("gzip模块不可用，无法压缩文件")
                    break
                except Exception as e:
                    print(f"压缩文件 {log_file.name} 时出错: {e}")
        
        print(f"\n压缩完成: 共压缩 {compressed_count} 个文件")

    def set_log_level(self, level='INFO'):
        """设置日志级别"""
        print(f"=== 设置日志级别为 {level} ===")
        
        # 这里可以修改日志配置文件或环境变量
        # 由于我们的日志系统是动态创建的，这个功能主要用于参考
        print("日志级别设置功能需要重启程序才能生效")
        print("建议的日志级别:")
        print("  DEBUG: 最详细的日志信息")
        print("  INFO: 一般信息")
        print("  WARNING: 警告信息")
        print("  ERROR: 错误信息")

    def monitor_log_size(self, max_size_mb=100):
        """监控日志大小"""
        print(f"=== 监控日志大小 (最大 {max_size_mb} MB) ===")
        
        if not self.log_dir.exists():
            print("日志目录不存在")
            return
        
        total_size = 0
        for log_file in self.log_dir.glob('*.log*'):
            total_size += log_file.stat().st_size
        
        total_size_mb = total_size / 1024 / 1024
        
        print(f"当前日志总大小: {total_size_mb:.1f} MB")
        
        if total_size_mb > max_size_mb:
            print(f"⚠️  警告: 日志大小超过限制 ({total_size_mb:.1f} MB > {max_size_mb} MB)")
            print("建议执行清理操作")
            return False
        else:
            print(f"✅ 日志大小正常 ({total_size_mb:.1f} MB < {max_size_mb} MB)")
            return True

def main():
    """主函数"""
    import sys
    
    log_manager = LogManager()
    
    if len(sys.argv) < 2:
        print("日志管理工具")
        print("=" * 40)
        print("使用方法:")
        print("  python log_manager.py info          # 查看日志信息")
        print("  python log_manager.py cleanup       # 清理旧日志")
        print("  python log_manager.py compress      # 压缩日志文件")
        print("  python log_manager.py monitor       # 监控日志大小")
        print("  python log_manager.py set-level     # 设置日志级别")
        return
    
    command = sys.argv[1]
    
    if command == 'info':
        log_manager.get_log_info()
    elif command == 'cleanup':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        max_files = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        log_manager.cleanup_old_logs(days, max_files)
    elif command == 'compress':
        log_manager.compress_logs()
    elif command == 'monitor':
        max_size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        log_manager.monitor_log_size(max_size)
    elif command == 'set-level':
        level = sys.argv[2] if len(sys.argv) > 2 else 'INFO'
        log_manager.set_log_level(level)
    else:
        print(f"未知命令: {command}")

if __name__ == "__main__":
    main()
