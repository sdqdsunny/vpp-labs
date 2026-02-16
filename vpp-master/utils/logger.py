"""
日志配置和工具

支持JSON格式和标准格式的日志输出
"""

import logging
import json
import sys
from datetime import datetime
from config import Config

config = Config()


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record):
        """将日志记录格式化为JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # 添加请求ID（如果存在）
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        # 添加额外字段
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # 添加异常信息和堆栈跟踪
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            log_data['stack_trace'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class StandardFormatter(logging.Formatter):
    """标准格式的日志格式化器"""
    
    def format(self, record):
        """将日志记录格式化为标准格式"""
        return (
            f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] '
            f'[{record.levelname}] '
            f'[{record.name}] '
            f'{record.getMessage()}'
        )


def setup_logger(name):
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称（通常是__name__）
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 设置日志级别
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # 选择格式化器
    if config.LOG_FORMAT.lower() == 'json':
        formatter = JSONFormatter()
    else:
        formatter = StandardFormatter()
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# 创建全局日志记录器
logger = setup_logger(__name__)
