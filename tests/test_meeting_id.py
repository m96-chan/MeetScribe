"""
Tests for meeting ID generation and parsing.
"""

from datetime import datetime

import pytest

from meetscribe.core.meeting_id import (
    MeetingIDComponents,
    _extract_date_from_filename,
    _generate_unique_part,
    _sanitize_component,
    generate_meeting_id,
    generate_meeting_id_from_file,
    generate_meeting_id_from_url,
    get_meeting_folder_path,
    normalize_meeting_id,
    parse_meeting_id,
    parse_meeting_id_extended,
    validate_meeting_id,
)


class TestMeetingIDComponents:
    """Tests for MeetingIDComponents dataclass."""

    def test_meeting_id_components_to_dict(self):
        """Test converting MeetingIDComponents to dictionary."""
        components = MeetingIDComponents(
            start_time=datetime(2025, 1, 1, 10, 0),
            source="discord",
            channel="test-channel",
            suffix="part1",
            raw_id="2025-01-01T10-00_discord_test-channel_part1",
        )

        result = components.to_dict()

        assert result["source"] == "discord"
        assert result["channel"] == "test-channel"
        assert result["suffix"] == "part1"
        assert "start_time" in result
        assert result["raw_id"] == "2025-01-01T10-00_discord_test-channel_part1"


class TestGenerateMeetingId:
    """Tests for generate_meeting_id function."""

    def test_generate_meeting_id(self):
        """Test meeting ID generation."""
        meeting_id = generate_meeting_id(
            source="discord",
            channel_or_pid="channel1234",
            start_time=datetime(2025, 11, 21, 19, 0),
        )

        assert meeting_id == "2025-11-21T19-00_discord_channel1234"

    def test_generate_meeting_id_without_start_time(self):
        """Test generating meeting ID without start time uses current time."""
        result = generate_meeting_id("discord", "channel123")

        assert "discord" in result
        assert "channel123" in result
        # Should have date format
        assert "-" in result
        assert "T" in result

    def test_generate_meeting_id_with_seconds(self):
        """Test generating meeting ID with seconds."""
        start_time = datetime(2025, 6, 15, 14, 30, 45)
        result = generate_meeting_id(
            "discord", "channel123", start_time=start_time, include_seconds=True
        )

        assert "2025-06-15T14-30-45" in result

    def test_generate_meeting_id_with_suffix(self):
        """Test generating meeting ID with suffix."""
        result = generate_meeting_id(
            "discord", "channel123", start_time=datetime(2025, 1, 1, 10, 0), suffix="part1"
        )

        assert "part1" in result
        assert result.count("_") >= 3

    def test_generate_meeting_id_with_unique(self):
        """Test generating unique meeting IDs."""
        start_time = datetime(2025, 6, 15, 14, 30)
        result1 = generate_meeting_id("discord", "channel123", start_time=start_time, unique=True)
        result2 = generate_meeting_id("discord", "channel123", start_time=start_time, unique=True)

        # Should be different due to unique suffix
        assert result1 != result2

    def test_meeting_id_special_characters(self):
        """Test meeting ID with special characters."""
        meeting_id = generate_meeting_id(
            source="discord bot",
            channel_or_pid="channel@#$1234",
            start_time=datetime(2025, 11, 21, 19, 0),
        )

        # Special characters should be sanitized
        assert "_" in meeting_id
        assert "@" not in meeting_id
        assert "#" not in meeting_id
        assert "$" not in meeting_id


class TestGenerateMeetingIdFromFile:
    """Tests for generate_meeting_id_from_file function."""

    def test_generate_from_file_basic(self):
        """Test generating meeting ID from file path."""
        result = generate_meeting_id_from_file("/path/to/meeting_audio.mp3")

        assert "file" in result
        assert "meeting_audio" in result

    def test_generate_from_file_with_date_in_name(self):
        """Test generating meeting ID from file with date in name."""
        result = generate_meeting_id_from_file("/path/to/2025-01-15_meeting.mp3")

        assert "2025-01-15" in result

    def test_generate_from_file_custom_source(self):
        """Test generating meeting ID with custom source."""
        result = generate_meeting_id_from_file("/path/to/meeting.mp3", source="obs")

        assert "obs" in result

    def test_generate_from_file_with_start_time(self):
        """Test generating meeting ID with explicit start time."""
        start_time = datetime(2025, 3, 20, 15, 45)
        result = generate_meeting_id_from_file("/path/to/meeting.mp3", start_time=start_time)

        assert "2025-03-20T15-45" in result


class TestGenerateMeetingIdFromUrl:
    """Tests for generate_meeting_id_from_url function."""

    def test_generate_from_google_meet_url(self):
        """Test generating meeting ID from Google Meet URL."""
        result = generate_meeting_id_from_url("https://meet.google.com/abc-defg-hij")

        assert "meet" in result
        assert "abc-defg-hij" in result

    def test_generate_from_zoom_url(self):
        """Test generating meeting ID from Zoom URL."""
        result = generate_meeting_id_from_url("https://zoom.us/j/123456789")

        assert "zoom" in result
        assert "123456789" in result

    def test_generate_from_discord_url(self):
        """Test generating meeting ID from Discord URL."""
        result = generate_meeting_id_from_url("https://discord.com/channels/123/456")

        assert "discord" in result

    def test_generate_from_unknown_url(self):
        """Test generating meeting ID from unknown URL."""
        result = generate_meeting_id_from_url("https://example.com/meeting/xyz")

        assert "webrtc" in result

    def test_generate_from_url_with_explicit_source(self):
        """Test generating meeting ID with explicit source."""
        result = generate_meeting_id_from_url("https://example.com/meeting/xyz", source="custom")

        assert "custom" in result

    def test_generate_from_url_with_empty_path(self):
        """Test generating meeting ID from URL with empty path."""
        result = generate_meeting_id_from_url("https://meet.google.com/")

        assert "meet" in result


class TestParseMeetingId:
    """Tests for parse_meeting_id function."""

    def test_parse_meeting_id(self):
        """Test meeting ID parsing."""
        meeting_id = "2025-11-21T19-00_discord_channel1234"
        start_time, source, channel = parse_meeting_id(meeting_id)

        assert start_time == datetime(2025, 11, 21, 19, 0)
        assert source == "discord"
        assert channel == "channel1234"

    def test_parse_meeting_id_with_seconds(self):
        """Test parsing meeting ID with seconds."""
        start_time, source, channel = parse_meeting_id("2025-01-15T10-30-45_discord_channel123")

        assert start_time == datetime(2025, 1, 15, 10, 30, 45)

    def test_parse_invalid_meeting_id(self):
        """Test parsing invalid meeting ID raises error."""
        with pytest.raises(ValueError):
            parse_meeting_id("invalid-meeting-id")


class TestParseMeetingIdExtended:
    """Tests for parse_meeting_id_extended function."""

    def test_parse_extended_basic(self):
        """Test parsing basic meeting ID."""
        result = parse_meeting_id_extended("2025-01-15T10-30_discord_channel123")

        assert result.start_time == datetime(2025, 1, 15, 10, 30)
        assert result.source == "discord"
        assert result.channel == "channel123"
        assert result.suffix is None
        assert result.raw_id == "2025-01-15T10-30_discord_channel123"

    def test_parse_extended_with_suffix(self):
        """Test parsing meeting ID with suffix."""
        result = parse_meeting_id_extended("2025-01-15T10-30_discord_channel123_part1")

        assert result.source == "discord"
        assert result.channel == "channel123"
        assert result.suffix == "part1"

    def test_parse_extended_with_seconds(self):
        """Test parsing meeting ID with seconds."""
        result = parse_meeting_id_extended("2025-01-15T10-30-45_discord_channel123")

        assert result.start_time == datetime(2025, 1, 15, 10, 30, 45)

    def test_parse_extended_invalid(self):
        """Test parsing invalid meeting ID."""
        with pytest.raises(ValueError, match="Invalid meeting ID format"):
            parse_meeting_id_extended("invalid")


class TestValidateMeetingId:
    """Tests for validate_meeting_id function."""

    def test_validate_meeting_id(self):
        """Test meeting ID validation."""
        assert validate_meeting_id("2025-11-21T19-00_discord_channel1234") is True
        assert validate_meeting_id("invalid-meeting-id") is False
        assert validate_meeting_id("") is False

    def test_validate_meeting_id_with_seconds(self):
        """Test validating meeting ID with seconds."""
        assert validate_meeting_id("2025-01-15T10-30-45_discord_channel123") is True

    def test_validate_meeting_id_with_suffix(self):
        """Test validating meeting ID with suffix."""
        assert validate_meeting_id("2025-01-15T10-30_discord_channel123_part1") is True


class TestNormalizeMeetingId:
    """Tests for normalize_meeting_id function."""

    def test_normalize_valid_meeting_id(self):
        """Test normalizing a valid meeting ID returns unchanged."""
        meeting_id = "2025-01-15T10-30_discord_channel123"
        result = normalize_meeting_id(meeting_id)

        assert result == meeting_id

    def test_normalize_meeting_id_with_special_chars(self):
        """Test normalizing meeting ID with special characters."""
        result = normalize_meeting_id("meeting@test#123")

        # Should not contain special characters
        assert "@" not in result
        assert "#" not in result

    def test_normalize_meeting_id_removes_duplicate_underscores(self):
        """Test normalizing removes duplicate underscores."""
        result = normalize_meeting_id("meeting__test")

        assert "__" not in result


class TestGetMeetingFolderPath:
    """Tests for get_meeting_folder_path function."""

    def test_get_meeting_folder_path_basic(self):
        """Test getting meeting folder path."""
        result = get_meeting_folder_path("2025-01-15T10-30_discord_channel123")

        assert "2025-01-15" in result
        assert "2025-01-15T10-30_discord_channel123" in result

    def test_get_meeting_folder_path_custom_base(self):
        """Test getting meeting folder path with custom base directory."""
        result = get_meeting_folder_path(
            "2025-01-15T10-30_discord_channel123", base_dir="/custom/path"
        )

        assert "custom" in result or result.startswith("/custom/path")


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_sanitize_component(self):
        """Test component sanitization."""
        assert _sanitize_component("hello world") == "hello_world"
        assert _sanitize_component("test@#$%") == "test"
        assert _sanitize_component("_test_") == "test"
        assert _sanitize_component("a__b") == "a_b"
        assert _sanitize_component("normal") == "normal"

    def test_generate_unique_part(self):
        """Test unique part generation."""
        result = _generate_unique_part()

        assert len(result) == 6
        assert result.isalnum()

        # Should generate different values
        result2 = _generate_unique_part()
        assert result != result2

    def test_extract_date_from_filename_with_datetime(self):
        """Test extracting date and time from filename."""
        result = _extract_date_from_filename("2025-01-15T10-30_meeting.mp3")
        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_extract_date_from_filename_date_only(self):
        """Test extracting date only from filename."""
        result = _extract_date_from_filename("meeting_2025-01-15.mp3")
        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15

    def test_extract_date_from_filename_compact_format(self):
        """Test extracting date from compact format."""
        result = _extract_date_from_filename("meeting_20250115_1030.mp3")
        assert result is not None
        assert result.year == 2025

    def test_extract_date_from_filename_no_date(self):
        """Test extracting date from filename without date."""
        result = _extract_date_from_filename("meeting.mp3")
        assert result is None

    def test_extract_date_from_filename_invalid_date(self):
        """Test extracting invalid date from filename."""
        result = _extract_date_from_filename("meeting_9999-99-99.mp3")
        assert result is None
