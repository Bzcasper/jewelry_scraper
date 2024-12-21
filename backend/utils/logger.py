# File: /backend/utils/logger.py

import logging
import logging.handlers
import json
from pathlib import Path
from typing import Any, Dict
from datetime import datetime
import traceback
from functools import wraps
import time

class StructuredLogger:
    """Enhanced logger with structured output and performance tracking"""

    def __init__(self, name: str, log_dir: Path):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_handlers()
        self._setup_formatters()

    def _setup_handlers(self):
        """Configure log handlers with rotation"""
        # Main log file with rotation
        main_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        main_handler.setLevel(logging.INFO)
        
        # Error log file
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "error.log",
            maxBytes=10*1024*1024,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        
        # JSON structured log
        json_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "structured.json",
            maxBytes=10*1024*1024,
            backupCount=5
        )
        
        # Console output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        self.logger.addHandler(main_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(json_handler)
        self.logger.addHandler(console_handler)
        
        self.json_handler = json_handler

    def _setup_formatters(self):
        """Configure log formatters"""
        standard_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                data = {
                    'timestamp': self.formatTime(record),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage()
                }
                
                if hasattr(record, 'extra'):
                    data.update(record.extra)
                
                if record.exc_info:
                    data['exception'] = self.formatException(record.exc_info)
                
                return json.dumps(data)
        
        # Apply formatters
        for handler in self.logger.handlers:
            if handler == self.json_handler:
                handler.setFormatter(JSONFormatter())
            else:
                handler.setFormatter(standard_formatter)

    def _log(self, level: int, message: str, extra: Dict[str, Any] = None):
        """Log message with extra context"""
        extra = extra or {}
        extra['timestamp'] = datetime.utcnow().isoformat()
        
        self.logger.log(level, message, extra={'extra': extra})

    def info(self, message: str, extra: Dict[str, Any] = None):
        self._log(logging.INFO, message, extra)

    def error(self, message: str, extra: Dict[str, Any] = None):
        self._log(logging.ERROR, message, extra)

    def warning(self, message: str, extra: Dict[str, Any] = None):
        self._log(logging.WARNING, message, extra)

    def critical(self, message: str, extra: Dict[str, Any] = None):
        self._log(logging.CRITICAL, message, extra)

    def performance(self, func_name: str, duration: float, extra: Dict[str, Any] = None):
        """Log performance metrics"""
        extra = extra or {}
        extra.update({
            'function': func_name,
            'duration': duration,
            'type': 'performance'
        })
        self._log(logging.INFO, f"Performance: {func_name} took {duration:.2f}s", extra)

def performance_logger(logger: StructuredLogger):
    """Decorator to log function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.performance(func.__name__, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Error in {func.__name__}",
                    extra={
                        'duration': duration,
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    }
                )
                raise
        return wrapper
    return decorator

# Create default logger instance
logger = StructuredLogger('jewelry_scraper', Path('logs'))