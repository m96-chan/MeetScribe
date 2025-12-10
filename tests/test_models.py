"""
Tests for core data models.
"""

import pytest
from datetime import datetime
from meetscribe.core.models import (
    Transcript,
    Minutes,
    AudioInfo,
    MeetingInfo,
    Segment,
    Decision,
    ActionItem,
)


def test_transcript_creation():
    """Test Transcript model creation."""
    meeting_info = MeetingInfo(
        meeting_id="2025-11-21T19-00_discord_channel1234",
        source_type="discord",
        start_time=datetime.now(),
    )

    transcript = Transcript(meeting_info=meeting_info, text="This is a test transcript.")

    assert transcript.text == "This is a test transcript."
    assert transcript.meeting_info.meeting_id == "2025-11-21T19-00_discord_channel1234"


def test_transcript_processing_history():
    """Test Transcript processing history."""
    meeting_info = MeetingInfo(meeting_id="test", source_type="discord", start_time=datetime.now())

    transcript = Transcript(meeting_info=meeting_info)
    transcript.add_processing_step("transcribe", {"engine": "whisper"})

    assert len(transcript.processing_history) == 1
    assert transcript.processing_history[0]["step"] == "transcribe"


def test_transcript_get_full_text():
    """Test getting full text from segments."""
    meeting_info = MeetingInfo(meeting_id="test", source_type="discord", start_time=datetime.now())

    segments = [
        Segment(start=0.0, end=1.0, text="Hello"),
        Segment(start=1.0, end=2.0, text="World"),
    ]

    transcript = Transcript(meeting_info=meeting_info, segments=segments)

    assert transcript.get_full_text() == "Hello\nWorld"


def test_minutes_to_dict():
    """Test Minutes serialization to dict."""
    decision = Decision(
        description="Use Python for backend", responsible="John Doe", deadline="2025-12-01"
    )

    action_item = ActionItem(
        description="Setup development environment",
        assignee="Jane Doe",
        deadline="2025-11-25",
        priority="high",
    )

    minutes = Minutes(
        meeting_id="test",
        summary="Test meeting summary",
        decisions=[decision],
        action_items=[action_item],
    )

    result = minutes.to_dict()

    assert result["meeting_id"] == "test"
    assert result["summary"] == "Test meeting summary"
    assert len(result["decisions"]) == 1
    assert len(result["action_items"]) == 1
    assert result["decisions"][0]["description"] == "Use Python for backend"
