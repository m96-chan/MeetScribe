"""
Logging system for MeetScribe.

Provides structured logging with multiple output targets and formatting options.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime
import json


# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
JSON_FORMAT = "json"

# Log levels mapping
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra fields
        if self.include_extra:
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in (
                    "name",
                    "msg",
                    "args",
                    "created",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "stack_info",
                    "exc_info",
                    "exc_text",
                    "thread",
                    "threadName",
                    "message",
                    "asctime",
                ):
                    try:
                        json.dumps(value)  # Check if serializable
                        extra_fields[key] = value
                    except (TypeError, ValueError):
                        extra_fields[key] = str(value)

            if extra_fields:
                log_data["extra"] = extra_fields

        return json.dumps(log_data, ensure_ascii=False)


class MeetScribeLogger:
    """
    Central logging configuration for MeetScribe.

    Provides methods to configure logging for the entire application
    with support for multiple handlers and formats.
    """

    _instance: Optional["MeetScribeLogger"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if MeetScribeLogger._initialized:
            return

        self.root_logger = logging.getLogger("meetscribe")
        self.root_logger.setLevel(logging.DEBUG)
        self._handlers: Dict[str, logging.Handler] = {}
        MeetScribeLogger._initialized = True

    def configure(
        self,
        level: Union[str, int] = "info",
        log_file: Optional[Path] = None,
        log_format: str = "default",
        json_output: bool = False,
        console_output: bool = True,
        file_rotation: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
    ) -> None:
        """
        Configure logging for MeetScribe.

        Args:
            level: Log level (debug, info, warning, error, critical)
            log_file: Optional path to log file
            log_format: Format string or 'default', 'detailed', 'json'
            json_output: Output logs in JSON format
            console_output: Enable console output
            file_rotation: Enable log file rotation
            max_file_size: Max file size before rotation (bytes)
            backup_count: Number of backup files to keep
        """
        # Clear existing handlers
        self.clear_handlers()

        # Set log level
        if isinstance(level, str):
            level = LOG_LEVELS.get(level.lower(), logging.INFO)
        self.root_logger.setLevel(level)

        # Determine formatter
        if json_output or log_format == JSON_FORMAT:
            formatter = JSONFormatter()
        elif log_format == "detailed":
            formatter = logging.Formatter(DETAILED_FORMAT)
        elif log_format == "default":
            formatter = logging.Formatter(DEFAULT_FORMAT)
        else:
            formatter = logging.Formatter(log_format)

        # Add console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            self.root_logger.addHandler(console_handler)
            self._handlers["console"] = console_handler

        # Add file handler
        if log_file:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)

            if file_rotation:
                from logging.handlers import RotatingFileHandler

                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=max_file_size,
                    backupCount=backup_count,
                    encoding="utf-8",
                )
            else:
                file_handler = logging.FileHandler(log_file, encoding="utf-8")

            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.root_logger.addHandler(file_handler)
            self._handlers["file"] = file_handler

    def clear_handlers(self) -> None:
        """Remove all handlers from the root logger."""
        for handler in self.root_logger.handlers[:]:
            self.root_logger.removeHandler(handler)
        self._handlers.clear()

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger for a specific module.

        Args:
            name: Module name (will be prefixed with 'meetscribe.')

        Returns:
            Logger instance
        """
        if not name.startswith("meetscribe."):
            name = f"meetscribe.{name}"
        return logging.getLogger(name)

    def add_handler(self, name: str, handler: logging.Handler) -> None:
        """
        Add a custom handler to the root logger.

        Args:
            name: Handler name for reference
            handler: Handler instance
        """
        self.root_logger.addHandler(handler)
        self._handlers[name] = handler

    def remove_handler(self, name: str) -> None:
        """
        Remove a handler by name.

        Args:
            name: Handler name
        """
        if name in self._handlers:
            self.root_logger.removeHandler(self._handlers[name])
            del self._handlers[name]


# Global logger instance
_logger_manager: Optional[MeetScribeLogger] = None


def setup_logging(
    level: Union[str, int] = "info",
    log_file: Optional[Path] = None,
    log_format: str = "default",
    json_output: bool = False,
    console_output: bool = True,
    **kwargs,
) -> MeetScribeLogger:
    """
    Set up logging for MeetScribe.

    This is the main entry point for configuring logging.

    Args:
        level: Log level (debug, info, warning, error, critical)
        log_file: Optional path to log file
        log_format: Format string or 'default', 'detailed', 'json'
        json_output: Output logs in JSON format
        console_output: Enable console output
        **kwargs: Additional arguments passed to configure()

    Returns:
        MeetScribeLogger instance
    """
    global _logger_manager
    _logger_manager = MeetScribeLogger()
    _logger_manager.configure(
        level=level,
        log_file=log_file,
        log_format=log_format,
        json_output=json_output,
        console_output=console_output,
        **kwargs,
    )
    return _logger_manager


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Module name

    Returns:
        Logger instance
    """
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = MeetScribeLogger()
        _logger_manager.configure()
    return _logger_manager.get_logger(name)


class LogContext:
    """
    Context manager for adding extra context to log messages.

    Usage:
        with LogContext(meeting_id="123", user="alice"):
            logger.info("Processing meeting")
            # Log will include meeting_id and user in extra fields
    """

    def __init__(self, **context):
        self.context = context
        self._old_factory = None

    def __enter__(self):
        self._old_factory = logging.getLogRecordFactory()
        context = self.context

        def record_factory(*args, **kwargs):
            record = self._old_factory(*args, **kwargs)
            for key, value in context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self._old_factory)
        return False


def log_execution_time(logger: logging.Logger):
    """
    Decorator to log function execution time.

    Args:
        logger: Logger instance to use

    Usage:
        @log_execution_time(logger)
        def my_function():
            ...
    """
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.debug(f"{func.__name__} completed in {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
                raise

        return wrapper

    return decorator


def log_async_execution_time(logger: logging.Logger):
    """
    Decorator to log async function execution time.

    Args:
        logger: Logger instance to use
    """
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.debug(f"{func.__name__} completed in {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
                raise

        return wrapper

    return decorator
