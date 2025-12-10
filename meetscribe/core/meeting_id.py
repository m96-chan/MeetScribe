"""
Meeting ID generation and parsing utilities.

Format: YYYY-MM-DDTHH-MM_<source>_<channel-or-pid>
Extended: YYYY-MM-DDTHH-MM-SS_<source>_<channel>_<suffix>
Example: 2025-11-21T19-00_discord_channel1234
"""

import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


@dataclass
class MeetingIDComponents:
    """Parsed components of a meeting ID."""

    start_time: datetime
    source: str
    channel: str
    suffix: Optional[str] = None
    raw_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time.isoformat(),
            "source": self.source,
            "channel": self.channel,
            "suffix": self.suffix,
            "raw_id": self.raw_id,
        }


def generate_meeting_id(
    source: str,
    channel_or_pid: str,
    start_time: Optional[datetime] = None,
    include_seconds: bool = False,
    suffix: Optional[str] = None,
    unique: bool = False,
) -> str:
    """
    Generate a standardized meeting ID.

    Args:
        source: Source type (discord, zoom, meet, proctap, obs, webrtc, file)
        channel_or_pid: Channel ID, process ID, or identifier
        start_time: Meeting start time (defaults to now)
        include_seconds: Include seconds in timestamp
        suffix: Optional suffix to append (e.g., "part1", "audio")
        unique: Add unique identifier to ensure uniqueness

    Returns:
        Meeting ID string

    Example:
        >>> generate_meeting_id("discord", "channel1234")
        '2025-11-21T19-00_discord_channel1234'
        >>> generate_meeting_id("zoom", "meeting123", unique=True)
        '2025-11-21T19-00-30_zoom_meeting123_a1b2c3'
    """
    if start_time is None:
        start_time = datetime.now()

    # Format timestamp
    if include_seconds:
        timestamp = start_time.strftime("%Y-%m-%dT%H-%M-%S")
    else:
        timestamp = start_time.strftime("%Y-%m-%dT%H-%M")

    # Clean inputs
    clean_channel = _sanitize_component(str(channel_or_pid))
    clean_source = _sanitize_component(source.lower())

    # Build ID
    meeting_id = f"{timestamp}_{clean_source}_{clean_channel}"

    # Add suffix if provided
    if suffix:
        clean_suffix = _sanitize_component(suffix)
        meeting_id = f"{meeting_id}_{clean_suffix}"

    # Add unique component if requested
    if unique:
        unique_part = _generate_unique_part()
        meeting_id = f"{meeting_id}_{unique_part}"

    return meeting_id


def generate_meeting_id_from_file(
    file_path: str, source: str = "file", start_time: Optional[datetime] = None
) -> str:
    """
    Generate meeting ID from file path.

    Args:
        file_path: Path to audio/video file
        source: Source type (default: "file")
        start_time: Meeting start time

    Returns:
        Meeting ID string
    """
    from pathlib import Path

    path = Path(file_path)

    # Use filename (without extension) as channel
    channel = path.stem

    # Try to extract date from filename if no start_time provided
    if start_time is None:
        start_time = _extract_date_from_filename(path.name) or datetime.now()

    return generate_meeting_id(source, channel, start_time)


def generate_meeting_id_from_url(
    url: str, source: Optional[str] = None, start_time: Optional[datetime] = None
) -> str:
    """
    Generate meeting ID from URL.

    Args:
        url: Meeting URL
        source: Source type (auto-detected if not provided)
        start_time: Meeting start time

    Returns:
        Meeting ID string
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)

    # Auto-detect source from URL
    if source is None:
        if "meet.google.com" in parsed.netloc:
            source = "meet"
        elif "zoom.us" in parsed.netloc:
            source = "zoom"
        elif "discord" in parsed.netloc:
            source = "discord"
        else:
            source = "webrtc"

    # Extract meeting code from path
    path_parts = parsed.path.strip("/").split("/")
    channel = path_parts[-1] if path_parts else _generate_unique_part()

    return generate_meeting_id(source, channel, start_time)


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
    components = parse_meeting_id_extended(meeting_id)
    return components.start_time, components.source, components.channel


def parse_meeting_id_extended(meeting_id: str) -> MeetingIDComponents:
    """
    Parse a meeting ID into detailed components.

    Supports both basic and extended formats.

    Args:
        meeting_id: Meeting ID string

    Returns:
        MeetingIDComponents object

    Raises:
        ValueError: If meeting ID format is invalid
    """
    # Pattern for extended format with optional seconds and suffix
    pattern = r"^(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}(?:-\d{2})?)_([^_]+)_([^_]+)(?:_(.+))?$"
    match = re.match(pattern, meeting_id)

    if not match:
        raise ValueError(f"Invalid meeting ID format: {meeting_id}")

    timestamp_str, source, channel, suffix = match.groups()

    # Parse timestamp (with or without seconds)
    if len(timestamp_str) == 19:  # YYYY-MM-DDTHH-MM-SS
        start_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H-%M-%S")
    else:  # YYYY-MM-DDTHH-MM
        start_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H-%M")

    return MeetingIDComponents(
        start_time=start_time, source=source, channel=channel, suffix=suffix, raw_id=meeting_id
    )


def validate_meeting_id(meeting_id: str) -> bool:
    """
    Check if a meeting ID is valid.

    Args:
        meeting_id: Meeting ID string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        parse_meeting_id_extended(meeting_id)
        return True
    except ValueError:
        return False


def normalize_meeting_id(meeting_id: str) -> str:
    """
    Normalize a meeting ID to standard format.

    Removes invalid characters and ensures proper formatting.

    Args:
        meeting_id: Meeting ID string to normalize

    Returns:
        Normalized meeting ID
    """
    # If already valid, return as-is
    if validate_meeting_id(meeting_id):
        return meeting_id

    # Try to extract components and regenerate
    # This handles cases where the ID might have extra characters
    cleaned = re.sub(r"[^\w\-T]", "_", meeting_id)
    cleaned = re.sub(r"_+", "_", cleaned)  # Remove duplicate underscores
    cleaned = cleaned.strip("_")

    return cleaned


def get_meeting_folder_path(meeting_id: str, base_dir: str = "./meetings") -> str:
    """
    Get folder path for meeting data.

    Args:
        meeting_id: Meeting ID
        base_dir: Base directory for meetings

    Returns:
        Path string for meeting folder
    """
    from pathlib import Path

    # Parse to validate and get components
    components = parse_meeting_id_extended(meeting_id)

    # Organize by date
    date_str = components.start_time.strftime("%Y-%m-%d")

    return str(Path(base_dir) / date_str / meeting_id)


def _sanitize_component(component: str) -> str:
    """Sanitize a component for use in meeting ID."""
    # Replace invalid characters with underscore
    sanitized = re.sub(r"[^\w-]", "_", component)
    # Remove consecutive underscores
    sanitized = re.sub(r"_+", "_", sanitized)
    # Remove leading/trailing underscores
    return sanitized.strip("_")


def _generate_unique_part() -> str:
    """Generate a short unique identifier."""
    # Use first 6 characters of UUID
    return uuid.uuid4().hex[:6]


def _extract_date_from_filename(filename: str) -> Optional[datetime]:
    """Try to extract date from filename."""
    # Common date patterns in filenames
    patterns = [
        (r"(\d{4})[-_]?(\d{2})[-_]?(\d{2})[-_T]?(\d{2})[-_:]?(\d{2})", "%Y-%m-%dT%H-%M"),
        (r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})", "%Y%m%d_%H%M"),
        (r"(\d{4})[-_](\d{2})[-_](\d{2})", "%Y-%m-%d"),
    ]

    for pattern, date_format in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                groups = match.groups()
                if len(groups) >= 5:
                    date_str = f"{groups[0]}-{groups[1]}-{groups[2]}T{groups[3]}-{groups[4]}"
                    return datetime.strptime(date_str, "%Y-%m-%dT%H-%M")
                elif len(groups) >= 3:
                    date_str = f"{groups[0]}-{groups[1]}-{groups[2]}"
                    return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue

    return None
