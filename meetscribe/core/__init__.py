"""
Core module for MeetScribe.

Contains fundamental models, pipeline orchestration, and configuration management.
"""

from .models import Transcript, Minutes, AudioInfo, MeetingInfo, Segment
from .meeting_id import generate_meeting_id, parse_meeting_id

__all__ = [
    "Transcript",
    "Minutes",
    "AudioInfo",
    "MeetingInfo",
    "Segment",
    "generate_meeting_id",
    "parse_meeting_id",
]
