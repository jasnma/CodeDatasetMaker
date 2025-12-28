#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志模块
提供统一的日志记录功能
"""

import logging
import os
import sys
from datetime import datetime

# 创建logs目录（如果不存在）
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# 配置日志格式
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 创建日志记录器
def get_logger(name: str = "CodeDatasetMaker", log_file: str = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径，如果为None则使用默认路径
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建logger
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 设置日志级别
    logger.setLevel(logging.DEBUG)
    
    # 创建格式化器
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 创建文件处理器
    if log_file is None:
        log_file = os.path.join(LOGS_DIR, f"{name}.log")
    
    # 确保日志文件所在的目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# 创建默认的日志记录器
default_logger = get_logger()

# 便捷函数
def debug(message: str):
    """记录调试信息"""
    default_logger.debug(message)

def info(message: str):
    """记录一般信息"""
    default_logger.info(message)

def warning(message: str):
    """记录警告信息"""
    default_logger.warning(message)

def error(message: str):
    """记录错误信息"""
    default_logger.error(message)

def critical(message: str):
    """记录严重错误信息"""
    default_logger.critical(message)

# AI调用专用日志记录器
ai_logger = get_logger("AI_Call")

def ai_debug(message: str):
    """记录AI调用调试信息"""
    ai_logger.debug(message)

def ai_info(message: str):
    """记录AI调用一般信息"""
    ai_logger.info(message)

def ai_warning(message: str):
    """记录AI调用警告信息"""
    ai_logger.warning(message)

def ai_error(message: str):
    """记录AI调用错误信息"""
    ai_logger.error(message)

def ai_critical(message: str):
    """记录AI调用严重错误信息"""
    ai_logger.critical(message)
