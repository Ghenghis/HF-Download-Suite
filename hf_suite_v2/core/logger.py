"""
Logging configuration with file and console handlers.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from .constants import LOGS_DIR, APP_NAME

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log levels
LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


class ColoredFormatter(logging.Formatter):
    """Formatter with ANSI color codes for console output."""
    
    COLORS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    level: str = "info",
    log_file: bool = True,
    console: bool = True,
    colored: bool = True
) -> logging.Logger:
    """
    Set up application-wide logging.
    
    Args:
        level: Log level (debug, info, warning, error, critical)
        log_file: Whether to log to file
        console: Whether to log to console
        colored: Whether to use colored console output
    
    Returns:
        Root logger instance
    """
    log_level = LEVEL_MAP.get(level.lower(), logging.INFO)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        if colored and sys.stdout.isatty():
            formatter = ColoredFormatter(LOG_FORMAT, LOG_DATE_FORMAT)
        else:
            formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = LOGS_DIR / f"hf_suite_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root_logger.addHandler(file_handler)
    
    # Suppress noisy loggers
    for logger_name in ["urllib3", "huggingface_hub", "httpx"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    root_logger.info(f"Logging initialized at {level.upper()} level")
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)


class LogCapture:
    """Context manager to capture log output."""
    
    def __init__(self, logger_name: str = None, level: int = logging.DEBUG):
        self.logger_name = logger_name
        self.level = level
        self.records = []
        self.handler = None
    
    def __enter__(self):
        class CaptureHandler(logging.Handler):
            def __init__(self, records):
                super().__init__()
                self.records = records
            
            def emit(self, record):
                self.records.append(record)
        
        logger = logging.getLogger(self.logger_name)
        self.handler = CaptureHandler(self.records)
        self.handler.setLevel(self.level)
        logger.addHandler(self.handler)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handler:
            logger = logging.getLogger(self.logger_name)
            logger.removeHandler(self.handler)
    
    @property
    def messages(self):
        return [r.getMessage() for r in self.records]
