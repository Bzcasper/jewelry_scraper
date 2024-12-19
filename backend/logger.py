import logging
import json
import os
import sys
import time
import threading
import queue
from logging.handlers import RotatingFileHandler, SMTPHandler, TimedRotatingFileHandler
from datetime import datetime
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import traceback
from concurrent.futures import ThreadPoolExecutor
import socket
import yaml
from enum import Enum

class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

@dataclass
class LogConfig:
    """Configuration for logging settings"""
    log_dir: str = "logs"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    email_notifications: bool = True
    slack_notifications: bool = False
    log_format: str = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    environment: str = "development"

class AsyncLogHandler(logging.Handler):
    """Asynchronous logging handler with queue"""
    def __init__(self, capacity: int = 1000):
        super().__init__()
        self.queue = queue.Queue(capacity)
        self.worker = threading.Thread(target=self._process_queue, daemon=True)
        self.worker.start()
        self.handlers: List[logging.Handler] = []

    def _process_queue(self):
        while True:
            try:
                record = self.queue.get()
                if record is None:
                    break
                for handler in self.handlers:
                    handler.emit(record)
            except Exception:
                print(f"Error processing log record: {traceback.format_exc()}")

    def emit(self, record: logging.LogRecord):
        try:
            self.queue.put(record)
        except queue.Full:
            print("Warning: Logging queue is full, dropping log record")

    def close(self):
        self.queue.put(None)
        self.worker.join()
        for handler in self.handlers:
            handler.close()
        super().close()

class StructuredLogger:
    """Enhanced logging with structured data and multiple outputs"""
    def __init__(self, name: str, config: Optional[LogConfig] = None):
        self.name = name
        self.config = config or LogConfig()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create async handler
        self.async_handler = AsyncLogHandler()
        
        # Setup handlers
        self._setup_handlers()
        
        # Context information
        self.context = {
            "hostname": socket.gethostname(),
            "environment": self.config.environment,
            "application": name
        }
        
        # Metrics tracking
        self.metrics: Dict[str, int] = {
            "error_count": 0,
            "critical_count": 0,
            "warning_count": 0
        }
        
        # Rate limiting
        self.rate_limits: Dict[str, Dict] = {}

    def _setup_handlers(self):
        """Setup log handlers with rotation and formatting"""
        # Ensure log directory exists
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            filename=log_dir / f"{self.name}.log",
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count
        )
        file_handler.setFormatter(logging.Formatter(
            self.config.log_format,
            self.config.date_format
        ))
        
        # Error file handler
        error_handler = RotatingFileHandler(
            filename=log_dir / f"{self.name}_error.log",
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            self.config.log_format,
            self.config.date_format
        ))
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            self.config.log_format,
            self.config.date_format
        ))
        
        # JSON handler for structured logging
        json_handler = RotatingFileHandler(
            filename=log_dir / f"{self.name}_structured.json",
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count
        )
        json_handler.setFormatter(self.JsonFormatter())
        
        # Add handlers to async handler
        self.async_handler.handlers.extend([
            file_handler,
            error_handler,
            console_handler,
            json_handler
        ])
        
        # Setup email notifications if enabled
        if self.config.email_notifications:
            self._setup_email_handler()
        
        # Add async handler to logger
        self.logger.addHandler(self.async_handler)

    def _setup_email_handler(self):
        """Setup email notifications for critical errors"""
        try:
            # Load email configuration from environment or config file
            email_config = self._load_email_config()
            
            smtp_handler = SMTPHandler(
                mailhost=(email_config['host'], email_config['port']),
                fromaddr=email_config['from'],
                toaddrs=email_config['to'],
                subject=f"{self.name} Critical Error - {self.config.environment}",
                credentials=(email_config['username'], email_config['password']),
                secure=()
            )
            smtp_handler.setLevel(logging.CRITICAL)
            smtp_handler.setFormatter(logging.Formatter(
                self.config.log_format,
                self.config.date_format
            ))
            self.async_handler.handlers.append(smtp_handler)
        except Exception as e:
            self.logger.warning(f"Failed to setup email notifications: {e}")

    def _load_email_config(self) -> Dict:
        """Load email configuration from environment or config file"""
        config_path = Path("config/email_config.yaml")
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {
            'host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            'port': int(os.getenv('SMTP_PORT', '587')),
            'from': os.getenv('SMTP_FROM', ''),
            'to': os.getenv('SMTP_TO', '').split(','),
            'username': os.getenv('SMTP_USERNAME', ''),
            'password': os.getenv('SMTP_PASSWORD', '')
        }

    class JsonFormatter(logging.Formatter):
        """JSON formatter for structured logging"""
        def format(self, record: logging.LogRecord) -> str:
            data = {
                'timestamp': self.formatTime(record),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            if hasattr(record, 'context'):
                data['context'] = record.context
            
            if record.exc_info:
                data['exception'] = self.formatException(record.exc_info)
            
            return json.dumps(data)

    def _rate_limited(self, key: str, period: int = 60) -> bool:
        """Check if logging should be rate limited"""
        now = time.time()
        if key not in self.rate_limits:
            self.rate_limits[key] = {'count': 0, 'start_time': now}
            return False
        
        if now - self.rate_limits[key]['start_time'] > period:
            self.rate_limits[key] = {'count': 0, 'start_time': now}
            return False
        
        self.rate_limits[key]['count'] += 1
        return self.rate_limits[key]['count'] > 100  # Limit to 100 logs per period

    def _log(self, level: LogLevel, message: str, context: Optional[Dict] = None, rate_limit_key: Optional[str] = None):
        """Internal logging method with context and rate limiting"""
        if rate_limit_key and self._rate_limited(rate_limit_key):
            return

        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self.metrics[f"{level.name.lower()}_count"] += 1

        # Combine context
        log_context = {**self.context, **(context or {})}
        
        # Create log record with context
        record = logging.LogRecord(
            name=self.name,
            level=level.value,
            pathname=__file__,
            lineno=0,
            msg=message,
            args=(),
            exc_info=sys.exc_info()
        )
        record.context = log_context
        
        self.async_handler.emit(record)

def create_logger(name: str, config: Optional[LogConfig] = None) -> StructuredLogger:
    """Create a new structured logger instance"""
    return StructuredLogger(name, config)

# Create default logger instance
logger = create_logger("scraper")

def log_error(message: str, context: Optional[Dict] = None):
    """Log an error message with optional context"""
    logger._log(LogLevel.ERROR, message, context)

def log_critical_error(message: str, context: Optional[Dict] = None):
    """Log a critical error message with optional context"""
    logger._log(LogLevel.CRITICAL, message, context)

# Example usage
if __name__ == "__main__":
    # Configuration example
    config = LogConfig(
        log_dir="logs",
        email_notifications=True,
        environment="production"
    )
    
    # Create logger instance
    app_logger = create_logger("scraper", config)
    
    # Log examples
    app_logger._log(
        LogLevel.ERROR,
        "Failed to scrape product",
        context={
            "product_id": "123",
            "url": "https://example.com",
            "attempt": 2
        }
    )