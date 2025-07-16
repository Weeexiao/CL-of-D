"""
日志管理模块
负责应用程序的日志记录和管理
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional
from config import config_manager


class LogManager:
    """日志管理器"""
    
    def __init__(self):
        """初始化日志管理器"""
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志配置"""
        # 移除默认的日志处理器
        logger.remove()
        
        # 获取日志文件路径
        log_file = config_manager.get_log_file_path()
        
        # 添加控制台日志处理器
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO",
            colorize=True
        )
        
        # 添加文件日志处理器
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="10 MB",  # 日志文件大小超过10MB时轮转
            retention="30 days",  # 保留30天的日志
            compression="zip",  # 压缩旧日志文件
            encoding="utf-8"
        )
        
        # 添加错误日志文件处理器
        error_log_file = config_manager.get_log_file_path("error.log")
        logger.add(
            error_log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation="5 MB",
            retention="60 days",
            compression="zip",
            encoding="utf-8"
        )
    
    def get_logger(self):
        """获取日志记录器"""
        return logger
    
    def log_classification_start(self, source_folder: str, file_count: int):
        """记录分类开始日志"""
        logger.info(f"开始文件分类 - 源文件夹: {source_folder}, 文件数量: {file_count}")
    
    def log_classification_progress(self, current: int, total: int, filename: str, entry_type: str):
        """记录分类进度日志"""
        progress = (current / total) * 100
        logger.info(f"分类进度: {current}/{total} ({progress:.1f}%) - {entry_type}: {filename}")
    
    def log_classification_success(self, filename: str, entry_type: str, target_path: str):
        """记录分类成功日志"""
        logger.info(f"分类成功: {entry_type} '{filename}' → {target_path}")
    
    def log_classification_error(self, filename: str, entry_type: str, error: str):
        """记录分类错误日志"""
        logger.error(f"分类失败: {entry_type} '{filename}' - {error}")
    
    def log_api_request(self, filename: str, api_type: str, request_content: str):
        """记录API请求日志"""
        logger.debug(f"API请求 - 文件: {filename}, API类型: {api_type}, 请求内容: {request_content[:200]}...")
    
    def log_api_response(self, filename: str, api_type: str, response: str):
        """记录API响应日志"""
        logger.debug(f"API响应 - 文件: {filename}, API类型: {api_type}, 响应: {response[:200]}...")
    
    def log_api_error(self, filename: str, api_type: str, error: str):
        """记录API错误日志"""
        logger.error(f"API错误 - 文件: {filename}, API类型: {api_type}, 错误: {error}")
    
    def log_config_change(self, config_type: str, old_value: str, new_value: str):
        """记录配置变更日志"""
        logger.info(f"配置变更 - {config_type}: {old_value} → {new_value}")
    
    def log_classification_complete(self, success_count: int, total_count: int, duration: float):
        """记录分类完成日志"""
        logger.info(f"分类完成 - 成功: {success_count}/{total_count}, 耗时: {duration:.2f}秒")


# 全局日志管理器实例
log_manager = LogManager() 