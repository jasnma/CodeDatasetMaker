"""
CodeDatasetMaker包初始化文件
"""

# 导入日志模块
from .logger import get_logger, debug, info, warning, error, critical
from .logger import ai_debug, ai_info, ai_warning, ai_error, ai_critical

__all__ = [
    "get_logger",
    "debug", "info", "warning", "error", "critical",
    "ai_debug", "ai_info", "ai_warning", "ai_error", "ai_critical"
]
