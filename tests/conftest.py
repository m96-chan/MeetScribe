"""
Pytest configuration and shared fixtures for MeetScribe tests.
"""

import pytest
from pathlib import Path
from datetime import datetime
import json
import tempfile
import shutil

from meetscribe.core.models import (
    Transcript,
    Minutes,
    MeetingInfo,
    AudioInfo,
    Segment,
    Decision,
    ActionItem,
)


# ============================================================================
# Path Fixtures
# ============================================================================


@pytest.fixture
def fixtures_dir():
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_transcript_path(fixtures_dir):
    """Return path to sample transcript JSON."""
    return fixtures_dir / "sample_transcript.json"


@pytest.fixture
def sample_minutes_path(fixtures_dir):
    """Return path to sample minutes JSON."""
    return fixtures_dir / "sample_minutes.json"


@pytest.fixture
def sample_config_path(fixtures_dir):
    """Return path to sample config YAML."""
    return fixtures_dir / "sample_config.yaml"


# ============================================================================
# Data Fixtures
# ============================================================================


@pytest.fixture
def sample_meeting_info():
    """Create a sample MeetingInfo object."""
    return MeetingInfo(
        meeting_id="2024-01-15T10-00_discord_general",
        source_type="discord",
        start_time=datetime(2024, 1, 15, 10, 0, 0),
        end_time=datetime(2024, 1, 15, 11, 30, 0),
        channel_id="general",
        participants=["Alice", "Bob", "Charlie", "David"],
    )


@pytest.fixture
def sample_audio_info():
    """Create a sample AudioInfo object."""
    return AudioInfo(duration=138.0, samplerate=48000, codec="opus", channels=2, bitrate=128000)


@pytest.fixture
def sample_segments():
    """Create sample transcript segments."""
    return [
        Segment(
            start=0.0,
            end=5.5,
            text="Good morning everyone. Let's start with the project status update.",
            speaker="Alice",
            confidence=0.95,
        ),
        Segment(
            start=5.5,
            end=15.0,
            text="Sure. We've completed the API integration last week.",
            speaker="Bob",
            confidence=0.93,
        ),
        Segment(
            start=15.0,
            end=25.0,
            text="That's great news. I've been working on the frontend components.",
            speaker="Charlie",
            confidence=0.91,
        ),
        Segment(
            start=25.0,
            end=35.0,
            text="I have a question about the database schema.",
            speaker="David",
            confidence=0.94,
        ),
    ]


@pytest.fixture
def sample_transcript(sample_meeting_info, sample_audio_info, sample_segments):
    """Create a sample Transcript object."""
    return Transcript(
        meeting_info=sample_meeting_info,
        text=" ".join(seg.text for seg in sample_segments),
        segments=sample_segments,
        audio_info=sample_audio_info,
        metadata={"converter": "whisper-api", "model": "whisper-1", "language": "en"},
    )


@pytest.fixture
def sample_decisions():
    """Create sample decisions."""
    return [
        Decision(
            description="Prioritize authentication module implementation",
            responsible="Bob",
            deadline="2024-01-22",
        ),
        Decision(
            description="Set auth module completion deadline for next Wednesday",
            responsible="Team",
            deadline="2024-01-22",
        ),
    ]


@pytest.fixture
def sample_action_items():
    """Create sample action items."""
    return [
        ActionItem(
            description="Create initial authentication module PR",
            assignee="Bob",
            deadline="2024-01-20",
            priority="high",
        ),
        ActionItem(
            description="Complete frontend components for testing",
            assignee="Charlie",
            deadline="2024-01-19",
            priority="high",
        ),
        ActionItem(
            description="Prepare database migration scripts",
            assignee="David",
            deadline="2024-01-22",
            priority="medium",
        ),
    ]


@pytest.fixture
def sample_minutes(sample_decisions, sample_action_items):
    """Create a sample Minutes object."""
    return Minutes(
        meeting_id="2024-01-15T10-00_discord_general",
        summary="Weekly team sync meeting covering project status updates.",
        decisions=sample_decisions,
        action_items=sample_action_items,
        key_points=[
            "API integration completed",
            "Frontend components will be ready by Friday",
            "Authentication module is the current priority",
        ],
        participants=["Alice", "Bob", "Charlie", "David"],
        url="https://notebooklm.google.com/notebook/sample123",
        metadata={"llm_engine": "chatgpt", "model": "gpt-4-turbo"},
    )


# ============================================================================
# File Fixtures
# ============================================================================


@pytest.fixture
def temp_audio_file(tmp_path):
    """Create a temporary fake audio file."""
    audio_file = tmp_path / "test_audio.mp3"
    # Create a fake MP3-like file (valid MP3 header bytes)
    # ID3 tag header + minimal frame data
    audio_file.write_bytes(
        b"ID3\x04\x00\x00\x00\x00\x00\x00"  # ID3 header
        + b"\xff\xfb\x90\x00"  # MP3 frame header
        + b"\x00" * 1000  # Padding
    )
    return audio_file


@pytest.fixture
def temp_wav_file(tmp_path):
    """Create a temporary fake WAV file."""
    wav_file = tmp_path / "test_audio.wav"
    # RIFF/WAV header
    wav_file.write_bytes(
        b"RIFF"
        + b"\x00\x00\x00\x00"  # File size (placeholder)
        + b"WAVE"
        + b"fmt "
        + b"\x10\x00\x00\x00"  # Chunk size
        + b"\x01\x00"  # Audio format (PCM)
        + b"\x01\x00"  # Num channels
        + b"\x44\xac\x00\x00"  # Sample rate (44100)
        + b"\x88\x58\x01\x00"  # Byte rate
        + b"\x02\x00"  # Block align
        + b"\x10\x00"  # Bits per sample
        + b"data"
        + b"\x00\x00\x00\x00"  # Data chunk size
        + b"\x00" * 1000  # Audio data
    )
    return wav_file


@pytest.fixture
def temp_working_dir(tmp_path):
    """Create a temporary working directory structure."""
    working_dir = tmp_path / "meetings"
    working_dir.mkdir(parents=True)
    return working_dir


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file."""
    import yaml

    config = {
        "input": {"provider": "file", "params": {"audio_path": str(tmp_path / "audio.mp3")}},
        "convert": {"engine": "passthrough", "params": {}},
        "llm": {"engine": "notebooklm", "params": {}},
        "output": {"format": "url", "params": {}},
        "working_dir": str(tmp_path / "meetings"),
        "cleanup_audio": False,
    }
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path


# ============================================================================
# Environment Fixtures
# ============================================================================


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-deepgram-key")
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-discord-token")
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")


@pytest.fixture
def clean_env(monkeypatch):
    """Remove API keys from environment for mock testing."""
    for key in [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "DEEPGRAM_API_KEY",
        "DISCORD_BOT_TOKEN",
        "DISCORD_WEBHOOK_URL",
    ]:
        monkeypatch.delenv(key, raising=False)


# ============================================================================
# Cleanup Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_test_files(tmp_path):
    """Automatically clean up test files after each test."""
    yield
    # Cleanup is handled automatically by tmp_path


# ============================================================================
# Integration Test Markers
# ============================================================================


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "requires_api: mark test as requiring real API access")
