"""
Logging system for M70 EZSocket
Converted from m70_log.h and m70_log.c
"""

import logging
import os
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


class M70LogLevel(IntEnum):
    """Log levels"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class M70LogTarget(IntEnum):
    """Log output targets"""
    CONSOLE = 1
    FILE = 2
    BOTH = 3


@dataclass
class M70LogConfig:
    """Log configuration"""
    level: M70LogLevel = M70LogLevel.INFO
    target: M70LogTarget = M70LogTarget.CONSOLE
    log_file_path: str = "./logs/mitsubishi_cnc.log"
    include_timestamp: bool = True
    include_level: bool = True
    include_file_line: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_file_count: int = 5


class M70Logger:
    """Logger for M70 operations"""
    
    _logger: Optional[logging.Logger] = None
    _config: Optional[M70LogConfig] = None
    _initialized: bool = False
    
    @classmethod
    def init(cls, config: M70LogConfig) -> bool:
        """Initialize the logging system"""
        try:
            cls._config = config
            cls._logger = logging.getLogger("M70EZSocket")
            cls._logger.setLevel(config.level)
            
            # Clear existing handlers
            cls._logger.handlers.clear()
            
            # Create formatter
            format_parts = []
            if config.include_timestamp:
                format_parts.append('%(asctime)s')
            if config.include_level:
                format_parts.append('[%(levelname)s]')
            if config.include_file_line:
                format_parts.append('%(filename)s:%(lineno)d')
            format_parts.append('%(message)s')
            
            formatter = logging.Formatter(' '.join(format_parts))
            
            # Add console handler
            if config.target in (M70LogTarget.CONSOLE, M70LogTarget.BOTH):
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                cls._logger.addHandler(console_handler)
            
            # Add file handler
            if config.target in (M70LogTarget.FILE, M70LogTarget.BOTH):
                # Create log directory if it doesn't exist
                log_dir = os.path.dirname(config.log_file_path)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                
                # Use RotatingFileHandler for log rotation
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    config.log_file_path,
                    maxBytes=config.max_file_size,
                    backupCount=config.max_file_count,
                    encoding='utf-8'
                )
                file_handler.setFormatter(formatter)
                cls._logger.addHandler(file_handler)
            
            cls._initialized = True
            cls.info("M70 Log system initialized successfully")
            return True
            
        except Exception as e:
            print(f"Failed to initialize logging system: {e}")
            return False
    
    @classmethod
    def shutdown(cls):
        """Shutdown the logging system"""
        if cls._logger:
            cls.info("M70 Log system shutting down")
            handlers = cls._logger.handlers[:]
            for handler in handlers:
                handler.close()
                cls._logger.removeHandler(handler)
            cls._initialized = False
    
    @classmethod
    def debug(cls, message: str, *args):
        """Log debug message"""
        if cls._logger:
            cls._logger.debug(message, *args)
    
    @classmethod
    def info(cls, message: str, *args):
        """Log info message"""
        if cls._logger:
            cls._logger.info(message, *args)
    
    @classmethod
    def warning(cls, message: str, *args):
        """Log warning message"""
        if cls._logger:
            cls._logger.warning(message, *args)
    
    @classmethod
    def error(cls, message: str, *args):
        """Log error message"""
        if cls._logger:
            cls._logger.error(message, *args)
    
    @classmethod
    def critical(cls, message: str, *args):
        """Log critical message"""
        if cls._logger:
            cls._logger.critical(message, *args)
