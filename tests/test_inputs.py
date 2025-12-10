"""
Unit tests for INPUT layer providers.
"""

import pytest
from pathlib import Path
from datetime import datetime
import json
import tempfile

from meetscribe.inputs.factory import get_input_provider
from meetscribe.inputs.file_provider import FileProvider
from meetscribe.inputs.zip_provider import ZipProvider
from meetscribe.inputs.google_meet_provider import GoogleMeetProvider
from meetscribe.inputs.obs_provider import OBSProvider
from meetscribe.inputs.webrtc_provider import WebRTCProvider


class TestInputFactory:
    """Tests for input factory."""

    def test_get_file_provider(self, tmp_path):
        """Test getting file provider."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        provider = get_input_provider("file", {"audio_path": str(audio_file)})
        assert isinstance(provider, FileProvider)

    def test_get_meet_provider(self):
        """Test getting Google Meet provider."""
        provider = get_input_provider("meet", {})
        assert isinstance(provider, GoogleMeetProvider)

    def test_get_google_meet_provider(self):
        """Test getting Google Meet provider alias."""
        provider = get_input_provider("google-meet", {})
        assert isinstance(provider, GoogleMeetProvider)

    def test_get_obs_provider(self):
        """Test getting OBS provider."""
        provider = get_input_provider("obs", {})
        assert isinstance(provider, OBSProvider)

    def test_get_webrtc_provider(self):
        """Test getting WebRTC provider."""
        provider = get_input_provider("webrtc", {})
        assert isinstance(provider, WebRTCProvider)

    def test_unsupported_provider(self):
        """Test error for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported input provider"):
            get_input_provider("invalid", {})


class TestFileProvider:
    """Tests for FileProvider."""

    def test_init_with_file(self, tmp_path):
        """Test initialization with file path."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio data")

        provider = FileProvider({"audio_path": str(audio_file)})
        assert provider.audio_path == audio_file

    def test_record_returns_path(self, tmp_path):
        """Test record returns audio path."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio data")

        provider = FileProvider({"audio_path": str(audio_file)})
        result = provider.record("2024-01-01T10-00_test_channel")

        assert result == audio_file

    def test_record_with_copy(self, tmp_path):
        """Test record with copy to working directory."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio data")
        working_dir = tmp_path / "working"

        provider = FileProvider(
            {
                "audio_path": str(audio_file),
                "copy_to_working_dir": True,
                "working_dir": str(working_dir),
            }
        )
        result = provider.record("2024-01-01T10-00_test_channel")

        assert result != audio_file
        assert result.exists()
        assert working_dir in result.parents

    def test_record_missing_file(self, tmp_path):
        """Test record with missing file."""
        provider = FileProvider({"audio_path": str(tmp_path / "nonexistent.mp3")})

        with pytest.raises(FileNotFoundError):
            provider.record("2024-01-01T10-00_test_channel")

    def test_record_from_directory(self, tmp_path):
        """Test record from directory."""
        # Create multiple audio files
        (tmp_path / "audio1.mp3").write_bytes(b"fake audio 1")
        (tmp_path / "audio2.mp3").write_bytes(b"fake audio 2")

        provider = FileProvider({"audio_path": str(tmp_path), "pattern": "*.mp3"})
        result = provider.record("2024-01-01T10-00_test_channel")

        assert result.exists()
        assert result.suffix == ".mp3"

    def test_validate_unsupported_format(self, tmp_path):
        """Test validation with unsupported format."""
        audio_file = tmp_path / "test.xyz"
        audio_file.write_bytes(b"data")

        provider = FileProvider({"audio_path": str(audio_file), "validate_format": True})

        with pytest.raises(ValueError, match="Unsupported audio format"):
            provider.record("2024-01-01T10-00_test_channel")

    def test_list_available_files(self, tmp_path):
        """Test listing available files."""
        (tmp_path / "audio1.mp3").write_bytes(b"fake audio 1")
        (tmp_path / "audio2.wav").write_bytes(b"fake audio 2")
        (tmp_path / "text.txt").write_bytes(b"not audio")

        provider = FileProvider({"audio_path": str(tmp_path)})
        files = provider.list_available_files()

        assert len(files) == 2
        assert all(f.suffix in [".mp3", ".wav"] for f in files)


class TestZipProvider:
    """Tests for ZipProvider."""

    def test_init_with_zip(self, tmp_path):
        """Test initialization with ZIP path."""
        zip_file = tmp_path / "test.zip"
        zip_file.write_bytes(b"fake zip")

        provider = ZipProvider(
            {"zip_path": str(zip_file), "extract_dir": str(tmp_path / "extract")}
        )
        assert provider.zip_path == zip_file


class TestGoogleMeetProvider:
    """Tests for GoogleMeetProvider."""

    def test_init_default_config(self):
        """Test default initialization."""
        provider = GoogleMeetProvider({})
        assert provider.keep_downloaded is True

    def test_mock_recording(self, tmp_path):
        """Test mock recording creation."""
        provider = GoogleMeetProvider({"download_dir": str(tmp_path)})
        result = provider.record("2024-01-01T10-00_test_channel")

        assert result.exists()

        # Check metadata was saved
        meta_file = result.parent / "drive_metadata.json"
        assert meta_file.exists()


class TestOBSProvider:
    """Tests for OBSProvider."""

    def test_init_default_config(self):
        """Test default initialization."""
        provider = OBSProvider({})
        assert provider.extract_audio is True
        assert provider.audio_format == "mp3"

    def test_find_recordings(self, tmp_path):
        """Test finding recordings."""
        # Create some video files
        (tmp_path / "recording1.mkv").write_bytes(b"video data")
        (tmp_path / "recording2.mp4").write_bytes(b"video data")

        provider = OBSProvider({"recording_dir": str(tmp_path), "pattern": "*.mkv"})
        recordings = provider._find_recordings()

        assert len(recordings) == 1
        assert recordings[0].suffix == ".mkv"

    def test_list_recordings(self, tmp_path):
        """Test listing recordings."""
        (tmp_path / "recording.mkv").write_bytes(b"video data")

        provider = OBSProvider({"recording_dir": str(tmp_path)})
        recordings = provider.list_recordings()

        assert len(recordings) == 1
        assert "path" in recordings[0]
        assert "size" in recordings[0]


class TestWebRTCProvider:
    """Tests for WebRTCProvider."""

    def test_init_default_config(self):
        """Test default initialization."""
        provider = WebRTCProvider({})
        assert provider.recording_format == "wav"
        assert provider.auto_reconnect is True

    def test_mock_recording(self, tmp_path):
        """Test mock recording creation."""
        provider = WebRTCProvider({"output_dir": str(tmp_path)})
        result = provider.record("2024-01-01T10-00_test_channel")

        assert result.exists()

    def test_build_ice_servers(self):
        """Test ICE server configuration."""
        provider = WebRTCProvider(
            {
                "stun_servers": ["stun.example.com:3478"],
                "turn_servers": [
                    {"host": "turn.example.com", "username": "user", "credential": "pass"}
                ],
            }
        )
        servers = provider._build_ice_servers()

        assert len(servers) >= 2
