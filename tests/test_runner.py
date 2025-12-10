"""
Tests for meetscribe.core.runner module.

Tests pipeline runner functionality.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from meetscribe.core.models import ActionItem, Decision, MeetingInfo, Minutes, Transcript


def create_test_transcript():
    """Helper to create a test Transcript object."""
    return Transcript(
        meeting_info=MeetingInfo(
            meeting_id="test-meeting-id",
            source_type="file",
            start_time=datetime.now(),
        ),
        text="Test transcript",
        segments=[],
    )


def create_test_minutes(meeting_id="test-meeting-id"):
    """Helper to create test Minutes object."""
    return Minutes(
        meeting_id=meeting_id,
        summary="Test summary",
        decisions=[Decision(description="Decision 1")],
        action_items=[ActionItem(description="Action 1", assignee="User")],
    )


class TestPipelineRunner:
    """Tests for PipelineRunner class."""

    def test_pipeline_runner_init(self, tmp_path):
        """Test PipelineRunner initialization."""
        from meetscribe.core.config import PipelineConfig
        from meetscribe.core.runner import PipelineRunner

        config = PipelineConfig.from_dict(
            {
                "input": {"provider": "file", "params": {"audio_path": str(tmp_path / "test.mp3")}},
                "convert": {"engine": "passthrough"},
                "llm": {"engine": "notebooklm", "params": {"api_key": "test"}},
                "output": {"format": "markdown", "params": {"output_dir": str(tmp_path)}},
                "working_dir": str(tmp_path),
            }
        )

        runner = PipelineRunner(config)

        assert runner.config == config
        assert runner.input_provider is None
        assert runner.converter is None
        assert runner.llm_provider is None

    def test_pipeline_runner_setup(self, tmp_path):
        """Test PipelineRunner setup."""
        from meetscribe.core.config import PipelineConfig
        from meetscribe.core.runner import PipelineRunner

        config = PipelineConfig.from_dict(
            {
                "input": {"provider": "file", "params": {"audio_path": str(tmp_path / "test.mp3")}},
                "convert": {"engine": "passthrough"},
                "llm": {"engine": "notebooklm", "params": {"api_key": "test"}},
                "output": {"format": "markdown", "params": {"output_dir": str(tmp_path)}},
                "working_dir": str(tmp_path),
            }
        )

        runner = PipelineRunner(config)
        runner.setup()

        assert runner.input_provider is not None
        assert runner.converter is not None
        assert runner.llm_provider is not None

    def test_pipeline_runner_validate_success(self, tmp_path):
        """Test PipelineRunner validate success."""
        from meetscribe.core.config import PipelineConfig
        from meetscribe.core.runner import PipelineRunner

        # Create test audio file
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        config = PipelineConfig.from_dict(
            {
                "input": {"provider": "file", "params": {"audio_path": str(audio_file)}},
                "convert": {"engine": "passthrough"},
                "llm": {"engine": "notebooklm", "params": {"api_key": "test"}},
                "output": {"format": "markdown", "params": {"output_dir": str(tmp_path)}},
                "working_dir": str(tmp_path),
            }
        )

        runner = PipelineRunner(config)
        runner.setup()

        # Should not raise
        runner.validate()

    def test_pipeline_runner_run(self, tmp_path):
        """Test PipelineRunner run."""
        from meetscribe.core.config import PipelineConfig
        from meetscribe.core.runner import PipelineRunner

        # Create test audio file
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        config = PipelineConfig.from_dict(
            {
                "input": {"provider": "file", "params": {"audio_path": str(audio_file)}},
                "convert": {"engine": "passthrough"},
                "llm": {"engine": "notebooklm", "params": {"api_key": "test"}},
                "output": {"format": "markdown", "params": {"output_dir": str(tmp_path)}},
                "working_dir": str(tmp_path),
            }
        )

        runner = PipelineRunner(config)
        runner.setup()

        # Mock the providers
        runner.input_provider.record = MagicMock(return_value=audio_file)
        runner.converter.transcribe = MagicMock(return_value=create_test_transcript())
        runner.llm_provider.generate_minutes = MagicMock(
            return_value=create_test_minutes("test-meeting-id")
        )

        result = runner.run("test-meeting-id")

        assert result is not None
        runner.input_provider.record.assert_called_once()
        runner.converter.transcribe.assert_called_once()
        runner.llm_provider.generate_minutes.assert_called_once()
