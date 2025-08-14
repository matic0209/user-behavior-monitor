import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
import time

class LoggerWithRotation:
    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerWithRotation, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self.setup_logger()

    def setup_logger(self):
        """设置带轮转功能的日志记录器"""
        # 创建日志目录
        log_dir = Path.cwd() / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 清理旧日志文件
        self._cleanup_old_logs(log_dir)
        
        # 获取当前时间作为文件名的一部分
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 配置根日志记录器
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        
        # 清除现有的处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 创建轮转文件处理器 - 主日志文件 (最大10MB，保留5个备份)
        log_file = log_dir / f'monitor_{timestamp}.log'
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        detailed_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s'
        )
        file_handler.setFormatter(detailed_format)
        
        # 创建轮转文件处理器 - 错误日志 (最大5MB，保留3个备份)
        error_file = log_dir / f'error_{timestamp}.log'
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s'
        )
        error_handler.setFormatter(error_format)
        
        # 创建轮转文件处理器 - 调试日志 (最大5MB，保留3个备份)
        debug_file = log_dir / f'debug_{timestamp}.log'
        debug_handler = RotatingFileHandler(
            debug_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s'
        )
        debug_handler.setFormatter(debug_format)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        console_handler.setFormatter(console_format)
        
        # 添加处理器到日志记录器
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        logger.addHandler(debug_handler)
        logger.addHandler(console_handler)
        
        self._logger = logger
        
        # 记录日志系统初始化信息
        self._logger.info("=== 日志系统初始化完成 (带轮转功能) ===")
        self._logger.info(f"日志目录: {log_dir}")
        self._logger.info(f"主日志文件: {log_file} (最大10MB，保留5个备份)")
        self._logger.info(f"错误日志文件: {error_file} (最大5MB，保留3个备份)")
        self._logger.info(f"调试日志文件: {debug_file} (最大5MB，保留3个备份)")
        self._logger.info(f"日志级别: DEBUG (文件) / INFO (控制台)")
        self._logger.info("=== 日志系统初始化完成 ===")

    def _cleanup_old_logs(self, log_dir):
        """清理旧的日志文件"""
        try:
            # 删除7天前的日志文件
            current_time = time.time()
            cutoff_time = current_time - (7 * 24 * 60 * 60)  # 7天
            
            for log_file in log_dir.glob('*.log*'):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    print(f"已删除旧日志文件: {log_file}")
            
            # 限制日志文件总数
            log_files = list(log_dir.glob('*.log'))
            if len(log_files) > 50:  # 最多保留50个日志文件
                # 按修改时间排序，删除最旧的文件
                log_files.sort(key=lambda x: x.stat().st_mtime)
                files_to_delete = log_files[:-50]
                for file in files_to_delete:
                    file.unlink()
                    print(f"已删除旧日志文件: {file}")
                    
        except Exception as e:
            print(f"清理日志文件时出错: {e}")

    def get_log_size_info(self):
        """获取日志文件大小信息"""
        try:
            log_dir = Path.cwd() / 'logs'
            total_size = 0
            file_count = 0
            
            for log_file in log_dir.glob('*.log*'):
                size = log_file.stat().st_size
                total_size += size
                file_count += 1
                print(f"日志文件: {log_file.name}, 大小: {size/1024:.1f} KB")
            
            print(f"总日志文件数: {file_count}")
            print(f"总日志大小: {total_size/1024/1024:.1f} MB")
            
            return total_size, file_count
            
        except Exception as e:
            print(f"获取日志大小信息时出错: {e}")
            return 0, 0

    def info(self, message):
        """记录信息日志"""
        self._logger.info(message)

    def error(self, message, exc_info=True):
        """记录错误日志，包含异常信息"""
        self._logger.error(message, exc_info=exc_info)

    def warning(self, message):
        """记录警告日志"""
        self._logger.warning(message)

    def debug(self, message):
        """记录调试日志"""
        self._logger.debug(message)

    def critical(self, message, exc_info=True):
        """记录严重错误日志"""
        self._logger.critical(message, exc_info=exc_info)

    def exception(self, message):
        """记录异常日志"""
        self._logger.exception(message)

    def log_memory_usage(self):
        """记录内存使用情况"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            self._logger.info(f"当前内存使用: {memory_mb:.1f} MB")
        except ImportError:
            self._logger.warning("psutil模块不可用，无法记录内存使用情况")

    def log_disk_usage(self):
        """记录磁盘使用情况"""
        try:
            import psutil
            disk_usage = psutil.disk_usage('.')
            total_gb = disk_usage.total / 1024 / 1024 / 1024
            used_gb = disk_usage.used / 1024 / 1024 / 1024
            free_gb = disk_usage.free / 1024 / 1024 / 1024
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            self._logger.info(f"磁盘使用情况: 总容量 {total_gb:.1f} GB, 已使用 {used_gb:.1f} GB, 可用 {free_gb:.1f} GB, 使用率 {usage_percent:.1f}%")
        except ImportError:
            self._logger.warning("psutil模块不可用，无法记录磁盘使用情况")
