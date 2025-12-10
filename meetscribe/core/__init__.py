"""
Core module for MeetScribe.

Contains fundamental models, pipeline orchestration, and configuration management.
"""

from .meeting_id import generate_meeting_id, parse_meeting_id
from .models import AudioInfo, MeetingInfo, Minutes, Segment, Transcript

__all__ = [
    "Transcript",
    "Minutes",
    "AudioInfo",
    "MeetingInfo",
    "Segment",
    "generate_meeting_id",
    "parse_meeting_id",
]
