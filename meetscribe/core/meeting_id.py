"""
Meeting ID generation and parsing utilities.

Format: YYYY-MM-DDTHH-MM_<source>_<channel-or-pid>
Example: 2025-11-21T19-00_discord_channel1234
"""

from datetime import datetime
from typing import Tuple, Optional
import re


def generate_meeting_id(
    source: str,
    channel_or_pid: str,
    start_time: Optional[datetime] = None
) -> str:
    """
    Generate a standardized meeting ID.

    Args:
        source: Source type (discord, zoom, meet, proctap, obs, webrtc)
        channel_or_pid: Channel ID or process ID
        start_time: Meeting start time (defaults to now)

    Returns:
        Meeting ID string

    Example:
        >>> generate_meeting_id("discord", "channel1234")
        '2025-11-21T19-00_discord_channel1234'
    """
    if start_time is None:
        start_time = datetime.now()

    timestamp = start_time.strftime("%Y-%m-%dT%H-%M")
    clean_channel = re.sub(r'[^\w-]', '_', str(channel_or_pid))
    clean_source = re.sub(r'[^\w-]', '_', source.lower())

    return f"{timestamp}_{clean_source}_{clean_channel}"


def parse_meeting_id(meeting_id: str) -> Tuple[datetime, str, str]:
    """
    Parse a meeting ID into its components.

    Args:
        meeting_id: Meeting ID string

    Returns:
        Tuple of (start_time, source, channel_or_pid)

    Raises:
        ValueError: If meeting ID format is invalid

    Example:
        >>> parse_meeting_id("2025-11-21T19-00_discord_channel1234")
        (datetime(2025, 11, 21, 19, 0), 'discord', 'channel1234')
    """
    pattern = r'^(\d{4}-\d{2}-\d{2}T\d{2}-\d{2})_([^_]+)_(.+)$'
    match = re.match(pattern, meeting_id)

    if not match:
        raise ValueError(f"Invalid meeting ID format: {meeting_id}")

    timestamp_str, source, channel = match.groups()
    start_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H-%M")

    return start_time, source, channel


def validate_meeting_id(meeting_id: str) -> bool:
    """
    Check if a meeting ID is valid.

    Args:
        meeting_id: Meeting ID string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        parse_meeting_id(meeting_id)
        return True
    except ValueError:
        return False
