"""
集中日志管理模块
提供统一的日志配置和管理功能
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


class LoggerManager:
    """日志管理器"""

    _loggers = {}

    @classmethod
    def get_logger(cls, name: str, log_dir: str = "logs") -> logging.Logger:
        """
        获取或创建logger实例

        Args:
            name: logger名称（通常使用 __name__）
            log_dir: 日志目录

        Returns:
            配置好的logger实例
        """
        if name in cls._loggers:
            return cls._loggers[name]

        # 创建日志目录
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 创建logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # 避免重复添加handler
        if logger.handlers:
            cls._loggers[name] = logger
            return logger

        # 文件handler - 所有日志
        today = datetime.now().strftime("%Y-%m-%d")
        all_log_file = os.path.join(log_dir, f"app_{today}.log")
        file_handler = RotatingFileHandler(
            all_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # 文件handler - 错误日志
        error_log_file = os.path.join(log_dir, f"error_{today}.log")
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)

        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 设置格式
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加handlers
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        logger.addHandler(console_handler)

        cls._loggers[name] = logger
        return logger


# 便捷函数
def get_logger(name: str = None) -> logging.Logger:
    """
    获取logger的便捷函数

    Args:
        name: logger名称，如果为None则使用调用者的模块名

    Returns:
        logger实例
    """
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')

    return LoggerManager.get_logger(name)


if __name__ == "__main__":
    # 测试日志系统
    logger = get_logger(__name__)

    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    logger.critical("这是一条严重错误信息")

    print("\n日志已写入 logs 目录")
