import logging
import os
from datetime import datetime
from pathlib import Path

class Logger:
    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self.setup_logger()

    def setup_logger(self):
        """设置日志记录器"""
        # 创建日志目录
        log_dir = Path.cwd() / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取当前时间作为文件名的一部分
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 配置根日志记录器 - 发布版默认INFO
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # 清除现有的处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 创建文件处理器 - 详细日志（发布版INFO级别）
        log_file = log_dir / f'monitor_{timestamp}.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        detailed_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s'
        )
        file_handler.setFormatter(detailed_format)
        
        # 创建文件处理器 - 错误日志
        error_file = log_dir / f'error_{timestamp}.log'
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s\n'
            'Exception: %(exc_info)s\n'
        )
        error_handler.setFormatter(error_format)
        
        # 创建控制台处理器 - 显示INFO及以上级别
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        console_handler.setFormatter(console_format)
        
        # 发布版：不写入专门的debug文件
        
        # 添加处理器到日志记录器
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        logger.addHandler(console_handler)
        # 发布版不添加debug文件处理器
        
        self._logger = logger
        
        # 记录日志系统初始化信息
        self._logger.info("=== 日志系统初始化完成 ===")
        self._logger.info(f"日志目录: {log_dir}")
        self._logger.info(f"主日志文件: {log_file}")
        self._logger.info(f"错误日志文件: {error_file}")
        self._logger.info(f"日志级别: INFO (文件) / INFO (控制台)")
        self._logger.info("=== 日志系统初始化完成 ===")

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
        """记录异常日志（自动包含异常信息）"""
        self._logger.exception(message) 