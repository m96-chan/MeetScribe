"""
Tests for meetscribe.core.logging module.

Tests logging configuration, formatters, and decorators.
"""

import asyncio
import json
import logging
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestLogLevels:
    """Tests for LOG_LEVELS constant."""

    def test_log_levels_mapping(self):
        """Test that LOG_LEVELS contains correct mappings."""
        from meetscribe.core.logging import LOG_LEVELS

        assert LOG_LEVELS["debug"] == logging.DEBUG
        assert LOG_LEVELS["info"] == logging.INFO
        assert LOG_LEVELS["warning"] == logging.WARNING
        assert LOG_LEVELS["error"] == logging.ERROR
        assert LOG_LEVELS["critical"] == logging.CRITICAL


class TestJSONFormatter:
    """Tests for JSONFormatter class."""

    def test_json_formatter_basic(self):
        """Test basic JSON formatting."""
        from meetscribe.core.logging import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["message"] == "Test message"
        assert data["line"] == 10
        assert "timestamp" in data

    def test_json_formatter_with_exception(self):
        """Test JSON formatting with exception info."""
        from meetscribe.core.logging import JSONFormatter

        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert "exception" in data
        assert "ValueError" in data["exception"]

    def test_json_formatter_with_extra_fields(self):
        """Test JSON formatting with extra fields."""
        from meetscribe.core.logging import JSONFormatter

        formatter = JSONFormatter(include_extra=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.custom_field = "custom_value"

        result = formatter.format(record)
        data = json.loads(result)

        assert "extra" in data
        assert data["extra"]["custom_field"] == "custom_value"

    def test_json_formatter_non_serializable_extra(self):
        """Test JSON formatting with non-serializable extra field."""
        from meetscribe.core.logging import JSONFormatter

        formatter = JSONFormatter(include_extra=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.custom_object = object()  # Non-serializable

        result = formatter.format(record)
        data = json.loads(result)

        assert "extra" in data
        assert "custom_object" in data["extra"]


class TestMeetScribeLogger:
    """Tests for MeetScribeLogger class."""

    def setup_method(self):
        """Reset singleton before each test."""
        from meetscribe.core.logging import MeetScribeLogger

        MeetScribeLogger._instance = None
        MeetScribeLogger._initialized = False

    def test_singleton_pattern(self):
        """Test that MeetScribeLogger is a singleton."""
        from meetscribe.core.logging import MeetScribeLogger

        logger1 = MeetScribeLogger()
        logger2 = MeetScribeLogger()

        assert logger1 is logger2

    def test_configure_default(self):
        """Test default configuration."""
        from meetscribe.core.logging import MeetScribeLogger

        logger_manager = MeetScribeLogger()
        logger_manager.configure()

        assert logger_manager.root_logger is not None
        assert "console" in logger_manager._handlers

    def test_configure_with_level(self):
        """Test configuration with custom level."""
        from meetscribe.core.logging import MeetScribeLogger

        logger_manager = MeetScribeLogger()
        logger_manager.configure(level="debug")

        assert logger_manager.root_logger.level == logging.DEBUG

    def test_configure_with_int_level(self):
        """Test configuration with integer level."""
        from meetscribe.core.logging import MeetScribeLogger

        logger_manager = MeetScribeLogger()
        logger_manager.configure(level=logging.WARNING)

        assert logger_manager.root_logger.level == logging.WARNING

    def test_configure_json_output(self):
        """Test configuration with JSON output."""
        from meetscribe.core.logging import JSONFormatter, MeetScribeLogger

        logger_manager = MeetScribeLogger()
        logger_manager.configure(json_output=True)

        handler = logger_manager._handlers.get("console")
        assert handler is not None
        assert isinstance(handler.formatter, JSONFormatter)

    def test_configure_detailed_format(self):
        """Test configuration with detailed format."""
        from meetscribe.core.logging import MeetScribeLogger

        logger_manager = MeetScribeLogger()
        logger_manager.configure(log_format="detailed")

        handler = logger_manager._handlers.get("console")
        assert handler is not None

    def test_configure_custom_format(self):
        """Test configuration with custom format string."""
        from meetscribe.core.logging import MeetScribeLogger

        custom_format = "%(levelname)s: %(message)s"
        logger_manager = MeetScribeLogger()
        logger_manager.configure(log_format=custom_format)

        handler = logger_manager._handlers.get("console")
        assert handler is not None

    def test_configure_no_console(self):
        """Test configuration without console output."""
        from meetscribe.core.logging import MeetScribeLogger

        logger_manager = MeetScribeLogger()
        logger_manager.configure(console_output=False)

        assert "console" not in logger_manager._handlers

    def test_configure_with_file(self, tmp_path):
        """Test configuration with log file."""
        from meetscribe.core.logging import MeetScribeLogger

        log_file = tmp_path / "test.log"
        logger_manager = MeetScribeLogger()
        logger_manager.configure(log_file=log_file)

        assert "file" in logger_manager._handlers
        assert log_file.parent.exists()

    def test_configure_with_file_no_rotation(self, tmp_path):
        """Test configuration with log file without rotation."""
        from meetscribe.core.logging import MeetScribeLogger

        log_file = tmp_path / "test.log"
        logger_manager = MeetScribeLogger()
        logger_manager.configure(log_file=log_file, file_rotation=False)

        assert "file" in logger_manager._handlers

    def test_clear_handlers(self):
        """Test clearing handlers."""
        from meetscribe.core.logging import MeetScribeLogger

        logger_manager = MeetScribeLogger()
        logger_manager.configure()

        assert len(logger_manager._handlers) > 0

        logger_manager.clear_handlers()

        assert len(logger_manager._handlers) == 0

    def test_get_logger(self):
        """Test getting a logger for a module."""
        from meetscribe.core.logging import MeetScribeLogger

        logger_manager = MeetScribeLogger()
        logger_manager.configure()

        logger = logger_manager.get_logger("test_module")

        assert logger.name == "meetscribe.test_module"

    def test_get_logger_already_prefixed(self):
        """Test getting a logger with meetscribe prefix."""
        from meetscribe.core.logging import MeetScribeLogger

        logger_manager = MeetScribeLogger()
        logger_manager.configure()

        logger = logger_manager.get_logger("meetscribe.test_module")

        assert logger.name == "meetscribe.test_module"

    def test_add_handler(self):
        """Test adding a custom handler."""
        from meetscribe.core.logging import MeetScribeLogger

        logger_manager = MeetScribeLogger()
        logger_manager.configure()

        custom_handler = logging.StreamHandler()
        logger_manager.add_handler("custom", custom_handler)

        assert "custom" in logger_manager._handlers

    def test_remove_handler(self):
        """Test removing a handler."""
        from meetscribe.core.logging import MeetScribeLogger

        logger_manager = MeetScribeLogger()
        logger_manager.configure()

        assert "console" in logger_manager._handlers

        logger_manager.remove_handler("console")

        assert "console" not in logger_manager._handlers

    def test_remove_nonexistent_handler(self):
        """Test removing a nonexistent handler."""
        from meetscribe.core.logging import MeetScribeLogger

        logger_manager = MeetScribeLogger()
        logger_manager.configure()

        # Should not raise
        logger_manager.remove_handler("nonexistent")


class TestSetupLogging:
    """Tests for setup_logging function."""

    def setup_method(self):
        """Reset singleton before each test."""
        from meetscribe.core.logging import MeetScribeLogger

        MeetScribeLogger._instance = None
        MeetScribeLogger._initialized = False

    def test_setup_logging_returns_logger_manager(self):
        """Test that setup_logging returns MeetScribeLogger instance."""
        from meetscribe.core.logging import MeetScribeLogger, setup_logging

        result = setup_logging()

        assert isinstance(result, MeetScribeLogger)

    def test_setup_logging_with_options(self, tmp_path):
        """Test setup_logging with various options."""
        from meetscribe.core.logging import setup_logging

        log_file = tmp_path / "test.log"
        result = setup_logging(
            level="debug", log_file=log_file, log_format="detailed", json_output=False
        )

        assert result is not None


class TestGetLogger:
    """Tests for get_logger function."""

    def setup_method(self):
        """Reset singleton before each test."""
        from meetscribe.core.logging import MeetScribeLogger

        MeetScribeLogger._instance = None
        MeetScribeLogger._initialized = False

    def test_get_logger_initializes_manager(self):
        """Test that get_logger initializes logger manager if needed."""
        from meetscribe.core.logging import get_logger

        logger = get_logger("test_module")

        assert logger is not None
        assert "meetscribe" in logger.name


class TestLogContext:
    """Tests for LogContext class."""

    def test_log_context_creates_custom_factory(self):
        """Test that LogContext creates a custom log record factory."""
        from meetscribe.core.logging import LogContext

        original_factory = logging.getLogRecordFactory()

        with LogContext(meeting_id="123", user="alice"):
            current_factory = logging.getLogRecordFactory()
            # Factory should be different during context
            assert current_factory != original_factory

        # Factory should be restored after context
        assert logging.getLogRecordFactory() == original_factory

    def test_log_context_restores_factory(self):
        """Test that LogContext restores original factory on exit."""
        from meetscribe.core.logging import LogContext

        original_factory = logging.getLogRecordFactory()

        with LogContext(test="value"):
            pass

        assert logging.getLogRecordFactory() == original_factory


class TestLogExecutionTime:
    """Tests for log_execution_time decorator."""

    def test_log_execution_time_success(self):
        """Test logging execution time for successful function."""
        from meetscribe.core.logging import log_execution_time

        mock_logger = MagicMock()

        @log_execution_time(mock_logger)
        def test_func():
            return "result"

        result = test_func()

        assert result == "result"
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0][0]
        assert "test_func" in call_args
        assert "completed" in call_args

    def test_log_execution_time_exception(self):
        """Test logging execution time for failed function."""
        from meetscribe.core.logging import log_execution_time

        mock_logger = MagicMock()

        @log_execution_time(mock_logger)
        def test_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            test_func()

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "test_func" in call_args
        assert "failed" in call_args


class TestLogAsyncExecutionTime:
    """Tests for log_async_execution_time decorator."""

    def test_log_async_execution_time_decorator_exists(self):
        """Test that log_async_execution_time decorator exists and is callable."""
        from meetscribe.core.logging import log_async_execution_time

        mock_logger = MagicMock()
        decorator = log_async_execution_time(mock_logger)

        assert callable(decorator)

    def test_log_async_execution_time_wraps_function(self):
        """Test that log_async_execution_time wraps async functions."""

        from meetscribe.core.logging import log_async_execution_time

        mock_logger = MagicMock()

        @log_async_execution_time(mock_logger)
        async def test_func():
            return "result"

        # Verify the function is wrapped
        assert asyncio.iscoroutinefunction(test_func)
