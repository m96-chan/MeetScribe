"""
Tests for ZipProvider.

Following TDD approach - tests written before implementation.
"""

import pytest
import zipfile
import json
from pathlib import Path

from meetscribe.inputs.zip_provider import ZipProvider


@pytest.fixture
def test_working_dir(tmp_path):
    """Create a temporary working directory for tests."""
    working_dir = tmp_path / "test_meetings"
    working_dir.mkdir(parents=True, exist_ok=True)
    return working_dir


@pytest.fixture
def sample_zip_single_audio(tmp_path):
    """Create a ZIP file with a single audio file."""
    zip_path = tmp_path / "single_audio.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        # Create a dummy audio file
        audio_content = b"fake audio content"
        zf.writestr("audio.mp3", audio_content)
    return zip_path


@pytest.fixture
def sample_zip_multiple_audio(tmp_path):
    """Create a ZIP file with multiple audio files."""
    zip_path = tmp_path / "multiple_audio.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        # Create multiple audio files
        zf.writestr("audio_001.mp3", b"audio 1")
        zf.writestr("audio_002.wav", b"audio 2")
        zf.writestr("audio_003.m4a", b"audio 3")
    return zip_path


@pytest.fixture
def sample_zip_with_metadata(tmp_path):
    """Create a ZIP file with audio and metadata."""
    zip_path = tmp_path / "with_metadata.zip"
    metadata = {
        "meeting_title": "Test Meeting",
        "participants": ["Alice", "Bob"],
        "date": "2025-11-22",
    }
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("audio.mp3", b"audio content")
        zf.writestr("metadata.json", json.dumps(metadata))
    return zip_path


@pytest.fixture
def sample_zip_nested_structure(tmp_path):
    """Create a ZIP file with nested directory structure."""
    zip_path = tmp_path / "nested.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("recordings/session1/audio.mp3", b"audio 1")
        zf.writestr("recordings/session2/audio.wav", b"audio 2")
    return zip_path


@pytest.fixture
def sample_zip_empty(tmp_path):
    """Create an empty ZIP file."""
    zip_path = tmp_path / "empty.zip"
    with zipfile.ZipFile(zip_path, "w"):
        pass  # Empty ZIP
    return zip_path


@pytest.fixture
def sample_zip_no_audio(tmp_path):
    """Create a ZIP file with no audio files."""
    zip_path = tmp_path / "no_audio.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("readme.txt", b"No audio here")
        zf.writestr("data.csv", b"col1,col2\n1,2")
    return zip_path


@pytest.fixture
def sample_zip_corrupted(tmp_path):
    """Create a corrupted ZIP file."""
    zip_path = tmp_path / "corrupted.zip"
    # Write invalid data
    with open(zip_path, "wb") as f:
        f.write(b"This is not a valid ZIP file")
    return zip_path


# ===== Phase 1: Single Mode Tests =====


class TestZipProviderSingleMode:
    """Tests for ZipProvider single mode."""

    def test_zip_provider_extracts_and_returns_first_audio(
        self, sample_zip_single_audio, test_working_dir
    ):
        """Test that ZIP is extracted and first audio file is returned."""
        # Given: sample.zip with audio file
        config = {
            "zip_path": str(sample_zip_single_audio),
            "working_dir": str(test_working_dir),
            "mode": "single",
        }
        provider = ZipProvider(config)
        meeting_id = "2025-11-22T10-00_zip_test"

        # When: record() is called
        audio_path = provider.record(meeting_id)

        # Then: first audio file path is returned
        assert audio_path.exists()
        assert audio_path.suffix in [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus"]
        assert "extracted" in str(audio_path)

    def test_zip_provider_returns_first_audio_from_multiple(
        self, sample_zip_multiple_audio, test_working_dir
    ):
        """Test that only first audio file is returned in single mode."""
        # Given: sample.zip with 3 audio files
        config = {
            "zip_path": str(sample_zip_multiple_audio),
            "working_dir": str(test_working_dir),
            "mode": "single",
        }
        provider = ZipProvider(config)
        meeting_id = "2025-11-22T10-00_zip_test"

        # When: record() is called
        audio_path = provider.record(meeting_id)

        # Then: single Path object is returned (not a list)
        assert isinstance(audio_path, Path)
        assert audio_path.exists()
        # First file should be audio_001.mp3 (alphabetically sorted)
        assert audio_path.name == "audio_001.mp3"

    def test_zip_provider_reads_metadata_if_exists(
        self, sample_zip_with_metadata, test_working_dir
    ):
        """Test that metadata is loaded if present in ZIP."""
        # Given: sample.zip with metadata.json
        config = {
            "zip_path": str(sample_zip_with_metadata),
            "working_dir": str(test_working_dir),
            "mode": "single",
        }
        provider = ZipProvider(config)

        # When: record() is called
        provider.record("2025-11-22T10-00_zip_test")

        # Then: metadata is loaded
        assert provider.metadata is not None
        assert "meeting_title" in provider.metadata
        assert provider.metadata["meeting_title"] == "Test Meeting"
        assert "participants" in provider.metadata

    def test_zip_provider_handles_nested_directories(
        self, sample_zip_nested_structure, test_working_dir
    ):
        """Test that nested directory structures are handled correctly."""
        # Given: ZIP with nested directory structure
        config = {
            "zip_path": str(sample_zip_nested_structure),
            "working_dir": str(test_working_dir),
            "mode": "single",
        }
        provider = ZipProvider(config)

        # When: record() is called
        audio_path = provider.record("2025-11-22T10-00_zip_test")

        # Then: audio file from nested directory is found
        assert audio_path.exists()
        assert audio_path.suffix in [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus"]

    def test_zip_provider_creates_extraction_directory(
        self, sample_zip_single_audio, test_working_dir
    ):
        """Test that extraction directory is created properly."""
        # Given: ZIP file and working directory
        config = {
            "zip_path": str(sample_zip_single_audio),
            "working_dir": str(test_working_dir),
            "mode": "single",
        }
        provider = ZipProvider(config)
        meeting_id = "2025-11-22T10-00_zip_test"

        # When: record() is called
        audio_path = provider.record(meeting_id)

        # Then: proper directory structure is created
        expected_extract_dir = test_working_dir / meeting_id / "extracted"
        assert expected_extract_dir.exists()
        assert expected_extract_dir.is_dir()
        assert audio_path.parent.name == "extracted" or "extracted" in str(audio_path.parent)


# ===== Phase 2: Multiple Mode Tests =====


class TestZipProviderMultipleMode:
    """Tests for ZipProvider multiple mode."""

    def test_zip_provider_returns_all_audio_files(
        self, sample_zip_multiple_audio, test_working_dir
    ):
        """Test that all audio files are returned in multiple mode."""
        # Given: sample.zip with 3 audio files
        config = {
            "zip_path": str(sample_zip_multiple_audio),
            "working_dir": str(test_working_dir),
            "mode": "multiple",
        }
        provider = ZipProvider(config)
        meeting_id = "2025-11-22T10-00_zip_test"

        # When: record_multiple() is called
        audio_paths = provider.record_multiple(meeting_id)

        # Then: all audio file paths are returned
        assert len(audio_paths) == 3
        for path in audio_paths:
            assert path.exists()
            assert path.suffix in [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus"]

    def test_zip_provider_sorts_audio_files_by_name(
        self, sample_zip_multiple_audio, test_working_dir
    ):
        """Test that audio files are sorted by name."""
        # Given: sample.zip with audio files
        config = {
            "zip_path": str(sample_zip_multiple_audio),
            "working_dir": str(test_working_dir),
            "mode": "multiple",
        }
        provider = ZipProvider(config)

        # When: record_multiple() is called
        audio_paths = provider.record_multiple("2025-11-22T10-00_zip_test")

        # Then: files are sorted by name
        file_names = [p.name for p in audio_paths]
        assert file_names == sorted(file_names)
        assert file_names == ["audio_001.mp3", "audio_002.wav", "audio_003.m4a"]

    def test_zip_provider_single_audio_returns_list_in_multiple_mode(
        self, sample_zip_single_audio, test_working_dir
    ):
        """Test that single audio file is returned as list in multiple mode."""
        # Given: sample.zip with single audio file
        config = {
            "zip_path": str(sample_zip_single_audio),
            "working_dir": str(test_working_dir),
            "mode": "multiple",
        }
        provider = ZipProvider(config)

        # When: record_multiple() is called
        audio_paths = provider.record_multiple("2025-11-22T10-00_zip_test")

        # Then: list with single audio file is returned
        assert isinstance(audio_paths, list)
        assert len(audio_paths) == 1
        assert audio_paths[0].exists()


# ===== Error Cases =====


class TestZipProviderErrorCases:
    """Tests for ZipProvider error handling."""

    def test_zip_provider_raises_error_for_missing_zip(self, test_working_dir):
        """Test that FileNotFoundError is raised for non-existent ZIP."""
        # Given: non-existent ZIP file path
        config = {
            "zip_path": "sample/nonexistent.zip",
            "working_dir": str(test_working_dir),
            "mode": "single",
        }
        provider = ZipProvider(config)

        # When/Then: FileNotFoundError is raised
        with pytest.raises(FileNotFoundError):
            provider.record("2025-11-22T10-00_zip_test")

    def test_zip_provider_raises_error_for_corrupted_zip(
        self, sample_zip_corrupted, test_working_dir
    ):
        """Test that BadZipFile is raised for corrupted ZIP."""
        # Given: corrupted ZIP file
        config = {
            "zip_path": str(sample_zip_corrupted),
            "working_dir": str(test_working_dir),
            "mode": "single",
        }
        provider = ZipProvider(config)

        # When/Then: BadZipFile error is raised
        with pytest.raises(zipfile.BadZipFile):
            provider.record("2025-11-22T10-00_zip_test")

    def test_zip_provider_raises_error_for_empty_zip(self, sample_zip_empty, test_working_dir):
        """Test that ValueError is raised for empty ZIP."""
        # Given: empty ZIP file
        config = {
            "zip_path": str(sample_zip_empty),
            "working_dir": str(test_working_dir),
            "mode": "single",
        }
        provider = ZipProvider(config)

        # When/Then: ValueError is raised
        with pytest.raises(ValueError, match="No audio files found"):
            provider.record("2025-11-22T10-00_zip_test")

    def test_zip_provider_raises_error_for_no_audio_files(
        self, sample_zip_no_audio, test_working_dir
    ):
        """Test that ValueError is raised when ZIP contains no audio files."""
        # Given: ZIP without audio files
        config = {
            "zip_path": str(sample_zip_no_audio),
            "working_dir": str(test_working_dir),
            "mode": "single",
        }
        provider = ZipProvider(config)

        # When/Then: ValueError is raised
        with pytest.raises(ValueError, match="No audio files found"):
            provider.record("2025-11-22T10-00_zip_test")

    def test_zip_provider_validates_config(self):
        """Test that config validation works correctly."""
        # Given: config without zip_path
        config = {"working_dir": "./test_meetings"}

        # When/Then: ValueError is raised during initialization
        with pytest.raises(ValueError, match="'zip_path' is required"):
            ZipProvider(config)

    def test_zip_provider_validates_mode(self, sample_zip_single_audio, test_working_dir):
        """Test that invalid mode raises ValueError."""
        # Given: config with invalid mode
        config = {
            "zip_path": str(sample_zip_single_audio),
            "working_dir": str(test_working_dir),
            "mode": "invalid_mode",
        }

        # When/Then: ValueError is raised during initialization
        with pytest.raises(ValueError, match="Invalid mode"):
            ZipProvider(config)


# ===== Configuration Tests =====


class TestZipProviderConfiguration:
    """Tests for ZipProvider configuration options."""

    def test_zip_provider_default_mode_is_single(self, sample_zip_single_audio, test_working_dir):
        """Test that default mode is 'single'."""
        # Given: config without mode specified
        config = {"zip_path": str(sample_zip_single_audio), "working_dir": str(test_working_dir)}
        provider = ZipProvider(config)

        # Then: mode defaults to 'single'
        assert provider.mode == "single"

    def test_zip_provider_default_sort_by_is_name(
        self, sample_zip_multiple_audio, test_working_dir
    ):
        """Test that default sort method is 'name'."""
        # Given: config without sort_by specified
        config = {
            "zip_path": str(sample_zip_multiple_audio),
            "working_dir": str(test_working_dir),
            "mode": "multiple",
        }
        provider = ZipProvider(config)

        # Then: sort_by defaults to 'name'
        assert provider.sort_by == "name"

    def test_zip_provider_supported_audio_formats(self, sample_zip_single_audio, test_working_dir):
        """Test that supported audio formats are correctly defined."""
        # Given: ZipProvider
        config = {"zip_path": str(sample_zip_single_audio), "working_dir": str(test_working_dir)}
        provider = ZipProvider(config)

        # Then: supported formats include common audio types
        expected_formats = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus"}
        assert provider.SUPPORTED_AUDIO_FORMATS == expected_formats
