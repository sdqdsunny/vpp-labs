"""
Logger Configuration Service.

Implements:
- Logging configuration
- Log level management
- Log rotation
- Critical operation logging
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional


class LoggerConfig:
    """Logger configuration service."""

    def __init__(self, 
                 log_dir: str = "logs",
                 log_level: str = "INFO",
                 max_bytes: int = 10485760,  # 10MB
                 backup_count: int = 5):
        """
        Initialize logger configuration.
        
        Args:
            log_dir: Directory for log files
            log_level: Default log level
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup log files to keep
        """
        self.log_dir = log_dir
        self.log_level = log_level
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.loggers = {}
        
        # Create log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def configure_logger(self,
                        name: str,
                        log_file: Optional[str] = None,
                        level: Optional[str] = None) -> logging.Logger:
        """
        Configure a logger with file and console handlers.
        
        Args:
            name: Logger name
            log_file: Log file name (optional)
            level: Log level (optional, uses default if not specified)
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        
        # Set log level
        log_level = level or self.log_level
        logger.setLevel(getattr(logging, log_level))
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Add file handler if log file specified
        if log_file:
            log_path = os.path.join(self.log_dir, log_file)
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count
            )
            file_handler.setLevel(getattr(logging, log_level))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        self.loggers[name] = logger
        return logger

    def set_log_level(self, name: str, level: str):
        """
        Set log level for a logger.
        
        Args:
            name: Logger name
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if name in self.loggers:
            logger = self.loggers[name]
            logger.setLevel(getattr(logging, level))
            for handler in logger.handlers:
                handler.setLevel(getattr(logging, level))

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a configured logger.
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        if name not in self.loggers:
            return self.configure_logger(name)
        return self.loggers[name]

    def log_critical_operation(self,
                              logger: logging.Logger,
                              operation: str,
                              details: Optional[dict] = None):
        """
        Log a critical operation.
        
        Args:
            logger: Logger instance
            operation: Operation name
            details: Operation details
        """
        timestamp = datetime.now().isoformat()
        message = f"CRITICAL OPERATION: {operation} at {timestamp}"
        if details:
            message += f" - Details: {details}"
        logger.critical(message)

    def log_data_operation(self,
                          logger: logging.Logger,
                          operation: str,
                          data_type: str,
                          count: int,
                          details: Optional[dict] = None):
        """
        Log a data operation.
        
        Args:
            logger: Logger instance
            operation: Operation name (e.g., 'save', 'delete', 'query')
            data_type: Type of data (e.g., 'power_data', 'storage_data')
            count: Number of records affected
            details: Additional details
        """
        message = f"DATA OPERATION: {operation} {data_type} (count: {count})"
        if details:
            message += f" - {details}"
        logger.info(message)

    def log_api_call(self,
                    logger: logging.Logger,
                    method: str,
                    endpoint: str,
                    status_code: int,
                    response_time_ms: float,
                    request_id: Optional[str] = None):
        """
        Log an API call.
        
        Args:
            logger: Logger instance
            method: HTTP method
            endpoint: API endpoint
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            request_id: Request ID for tracking
        """
        message = f"API CALL: {method} {endpoint} - Status: {status_code} - Time: {response_time_ms:.2f}ms"
        if request_id:
            message += f" - Request ID: {request_id}"
        
        if status_code >= 500:
            logger.error(message)
        elif status_code >= 400:
            logger.warning(message)
        else:
            logger.info(message)

    def log_coordination_event(self,
                              logger: logging.Logger,
                              event: str,
                              score: float,
                              details: Optional[dict] = None):
        """
        Log a coordination event.
        
        Args:
            logger: Logger instance
            event: Event name
            score: Optimization score
            details: Additional details
        """
        message = f"COORDINATION: {event} - Score: {score:.1f}"
        if details:
            message += f" - {details}"
        logger.info(message)

    def get_stats(self) -> dict:
        """
        Get logger statistics.
        
        Returns:
            dict: Logger statistics
        """
        return {
            "log_dir": self.log_dir,
            "log_level": self.log_level,
            "max_bytes": self.max_bytes,
            "backup_count": self.backup_count,
            "configured_loggers": list(self.loggers.keys()),
            "log_files": self._get_log_files(),
        }

    def _get_log_files(self) -> list:
        """Get list of log files."""
        log_files = []
        if os.path.exists(self.log_dir):
            for file in os.listdir(self.log_dir):
                if file.endswith('.log'):
                    file_path = os.path.join(self.log_dir, file)
                    file_size = os.path.getsize(file_path)
                    log_files.append({
                        "name": file,
                        "size": file_size,
                        "size_mb": file_size / (1024 * 1024),
                    })
        return log_files

    def cleanup_old_logs(self, max_age_days: int = 30):
        """
        Clean up old log files.
        
        Args:
            max_age_days: Maximum age of log files to keep
        """
        import time
        
        if not os.path.exists(self.log_dir):
            return
        
        now = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        for file in os.listdir(self.log_dir):
            if file.endswith('.log'):
                file_path = os.path.join(self.log_dir, file)
                file_age = now - os.path.getmtime(file_path)
                
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                        logging.info(f"Removed old log file: {file}")
                    except Exception as e:
                        logging.error(f"Error removing log file {file}: {str(e)}")


# Global logger config instance
_logger_config = None


def get_logger_config() -> LoggerConfig:
    """Get global logger config instance."""
    global _logger_config
    if _logger_config is None:
        _logger_config = LoggerConfig()
    return _logger_config


def init_logger_config(log_dir: str = "logs",
                      log_level: str = "INFO") -> LoggerConfig:
    """Initialize global logger config."""
    global _logger_config
    _logger_config = LoggerConfig(log_dir=log_dir, log_level=log_level)
    return _logger_config
