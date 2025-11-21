"""
Tests for meeting ID generation and parsing.
"""

import pytest
from datetime import datetime
from meetscribe.core.meeting_id import (
    generate_meeting_id,
    parse_meeting_id,
    validate_meeting_id
)


def test_generate_meeting_id():
    """Test meeting ID generation."""
    meeting_id = generate_meeting_id(
        source="discord",
        channel_or_pid="channel1234",
        start_time=datetime(2025, 11, 21, 19, 0)
    )

    assert meeting_id == "2025-11-21T19-00_discord_channel1234"


def test_parse_meeting_id():
    """Test meeting ID parsing."""
    meeting_id = "2025-11-21T19-00_discord_channel1234"
    start_time, source, channel = parse_meeting_id(meeting_id)

    assert start_time == datetime(2025, 11, 21, 19, 0)
    assert source == "discord"
    assert channel == "channel1234"


def test_validate_meeting_id():
    """Test meeting ID validation."""
    assert validate_meeting_id("2025-11-21T19-00_discord_channel1234") is True
    assert validate_meeting_id("invalid-meeting-id") is False
    assert validate_meeting_id("") is False


def test_meeting_id_special_characters():
    """Test meeting ID with special characters."""
    meeting_id = generate_meeting_id(
        source="discord bot",
        channel_or_pid="channel@#$1234",
        start_time=datetime(2025, 11, 21, 19, 0)
    )

    # Special characters should be sanitized
    assert "_" in meeting_id
    assert "@" not in meeting_id
    assert "#" not in meeting_id
    assert "$" not in meeting_id
