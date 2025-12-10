"""
Tests for meetscribe.utils.files module.

Tests file management utilities including directory operations,
file hashing, copying, moving, deletion, and JSON operations.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_ensure_directory_creates_new_directory(self, tmp_path):
        """Test that ensure_directory creates a new directory."""
        from meetscribe.utils.files import ensure_directory

        new_dir = tmp_path / "new_directory"
        result = ensure_directory(new_dir)

        assert result == new_dir
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_creates_nested_directories(self, tmp_path):
        """Test that ensure_directory creates nested directories."""
        from meetscribe.utils.files import ensure_directory

        nested_dir = tmp_path / "level1" / "level2" / "level3"
        result = ensure_directory(nested_dir)

        assert result == nested_dir
        assert nested_dir.exists()

    def test_ensure_directory_existing_directory(self, tmp_path):
        """Test that ensure_directory works with existing directory."""
        from meetscribe.utils.files import ensure_directory

        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        result = ensure_directory(existing_dir)
        assert result == existing_dir
        assert existing_dir.exists()


class TestGetMeetingDirectory:
    """Tests for get_meeting_directory function."""

    def test_get_meeting_directory_creates_directory(self, tmp_path):
        """Test that get_meeting_directory creates meeting directory."""
        from meetscribe.utils.files import get_meeting_directory

        meeting_id = "2025-01-01T10-00_discord_test"
        result = get_meeting_directory(tmp_path, meeting_id)

        assert result == tmp_path / meeting_id
        assert result.exists()

    def test_get_meeting_directory_no_create(self, tmp_path):
        """Test get_meeting_directory without creating directory."""
        from meetscribe.utils.files import get_meeting_directory

        meeting_id = "2025-01-01T10-00_discord_test"
        result = get_meeting_directory(tmp_path, meeting_id, create=False)

        assert result == tmp_path / meeting_id
        assert not result.exists()


class TestListMeetingDirectories:
    """Tests for list_meeting_directories function."""

    def test_list_meeting_directories_empty(self, tmp_path):
        """Test listing empty directory."""
        from meetscribe.utils.files import list_meeting_directories

        result = list_meeting_directories(tmp_path)
        assert result == []

    def test_list_meeting_directories_multiple(self, tmp_path):
        """Test listing multiple meeting directories."""
        from meetscribe.utils.files import list_meeting_directories

        # Create some directories
        (tmp_path / "meeting1").mkdir()
        (tmp_path / "meeting2").mkdir()
        (tmp_path / "meeting3").mkdir()
        # Create a file (should be ignored)
        (tmp_path / "file.txt").write_text("test")

        result = list_meeting_directories(tmp_path)
        assert len(result) == 3
        assert all(p.is_dir() for p in result)

    def test_list_meeting_directories_ignores_hidden(self, tmp_path):
        """Test that hidden directories are ignored."""
        from meetscribe.utils.files import list_meeting_directories

        (tmp_path / ".hidden").mkdir()
        (tmp_path / "visible").mkdir()

        result = list_meeting_directories(tmp_path)
        assert len(result) == 1
        assert result[0].name == "visible"

    def test_list_meeting_directories_nonexistent(self, tmp_path):
        """Test listing nonexistent directory."""
        from meetscribe.utils.files import list_meeting_directories

        result = list_meeting_directories(tmp_path / "nonexistent")
        assert result == []


class TestFindFilesByExtension:
    """Tests for find_files_by_extension function."""

    def test_find_files_by_extension_basic(self, tmp_path):
        """Test finding files by extension."""
        from meetscribe.utils.files import find_files_by_extension

        (tmp_path / "audio1.mp3").write_bytes(b"")
        (tmp_path / "audio2.mp3").write_bytes(b"")
        (tmp_path / "video.mp4").write_bytes(b"")

        result = find_files_by_extension(tmp_path, [".mp3"])
        assert len(result) == 2
        assert all(f.suffix == ".mp3" for f in result)

    def test_find_files_by_extension_multiple(self, tmp_path):
        """Test finding files with multiple extensions."""
        from meetscribe.utils.files import find_files_by_extension

        (tmp_path / "audio.mp3").write_bytes(b"")
        (tmp_path / "audio.wav").write_bytes(b"")
        (tmp_path / "video.mp4").write_bytes(b"")

        result = find_files_by_extension(tmp_path, [".mp3", ".wav"])
        assert len(result) == 2

    def test_find_files_by_extension_recursive(self, tmp_path):
        """Test finding files recursively."""
        from meetscribe.utils.files import find_files_by_extension

        (tmp_path / "audio.mp3").write_bytes(b"")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "audio2.mp3").write_bytes(b"")

        result = find_files_by_extension(tmp_path, [".mp3"], recursive=True)
        assert len(result) == 2

    def test_find_files_by_extension_nonexistent(self, tmp_path):
        """Test finding files in nonexistent directory."""
        from meetscribe.utils.files import find_files_by_extension

        result = find_files_by_extension(tmp_path / "nonexistent", [".mp3"])
        assert result == []

    def test_find_files_by_extension_without_dot(self, tmp_path):
        """Test that extensions without dot are normalized."""
        from meetscribe.utils.files import find_files_by_extension

        (tmp_path / "audio.mp3").write_bytes(b"")

        result = find_files_by_extension(tmp_path, ["mp3"])
        assert len(result) == 1


class TestCalculateFileHash:
    """Tests for calculate_file_hash function."""

    def test_calculate_file_hash_sha256(self, tmp_path):
        """Test calculating SHA256 hash."""
        from meetscribe.utils.files import calculate_file_hash

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        result = calculate_file_hash(test_file)
        assert len(result) == 64  # SHA256 hex digest length
        assert result.isalnum()

    def test_calculate_file_hash_md5(self, tmp_path):
        """Test calculating MD5 hash."""
        from meetscribe.utils.files import calculate_file_hash

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        result = calculate_file_hash(test_file, algorithm="md5")
        assert len(result) == 32  # MD5 hex digest length

    def test_calculate_file_hash_sha1(self, tmp_path):
        """Test calculating SHA1 hash."""
        from meetscribe.utils.files import calculate_file_hash

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        result = calculate_file_hash(test_file, algorithm="sha1")
        assert len(result) == 40  # SHA1 hex digest length


class TestGetFileInfo:
    """Tests for get_file_info function."""

    def test_get_file_info_basic(self, tmp_path):
        """Test getting file information."""
        from meetscribe.utils.files import get_file_info

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = get_file_info(test_file)

        assert result["name"] == "test.txt"
        assert result["stem"] == "test"
        assert result["suffix"] == ".txt"
        assert result["size_bytes"] == 12
        assert result["is_file"] is True
        assert result["is_dir"] is False
        assert "created" in result
        assert "modified" in result


class TestFormatFileSize:
    """Tests for format_file_size function."""

    def test_format_file_size_bytes(self):
        """Test formatting bytes."""
        from meetscribe.utils.files import format_file_size

        assert format_file_size(512) == "512.0 B"

    def test_format_file_size_kilobytes(self):
        """Test formatting kilobytes."""
        from meetscribe.utils.files import format_file_size

        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(2048) == "2.0 KB"

    def test_format_file_size_megabytes(self):
        """Test formatting megabytes."""
        from meetscribe.utils.files import format_file_size

        assert format_file_size(1024 * 1024) == "1.0 MB"

    def test_format_file_size_gigabytes(self):
        """Test formatting gigabytes."""
        from meetscribe.utils.files import format_file_size

        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"


class TestSafeCopy:
    """Tests for safe_copy function."""

    def test_safe_copy_success(self, tmp_path):
        """Test successful file copy."""
        from meetscribe.utils.files import safe_copy

        src = tmp_path / "source.txt"
        src.write_text("content")
        dst = tmp_path / "dest.txt"

        result = safe_copy(src, dst)

        assert result == dst
        assert dst.exists()
        assert dst.read_text() == "content"

    def test_safe_copy_creates_parent_dirs(self, tmp_path):
        """Test that safe_copy creates parent directories."""
        from meetscribe.utils.files import safe_copy

        src = tmp_path / "source.txt"
        src.write_text("content")
        dst = tmp_path / "nested" / "dir" / "dest.txt"

        result = safe_copy(src, dst)

        assert result.exists()
        assert dst.parent.exists()

    def test_safe_copy_no_overwrite(self, tmp_path):
        """Test that safe_copy raises error when not overwriting."""
        from meetscribe.utils.files import safe_copy

        src = tmp_path / "source.txt"
        src.write_text("content")
        dst = tmp_path / "dest.txt"
        dst.write_text("existing")

        with pytest.raises(FileExistsError):
            safe_copy(src, dst)

    def test_safe_copy_with_overwrite(self, tmp_path):
        """Test safe_copy with overwrite enabled."""
        from meetscribe.utils.files import safe_copy

        src = tmp_path / "source.txt"
        src.write_text("new content")
        dst = tmp_path / "dest.txt"
        dst.write_text("existing")

        result = safe_copy(src, dst, overwrite=True)

        assert dst.read_text() == "new content"

    def test_safe_copy_source_not_found(self, tmp_path):
        """Test safe_copy with nonexistent source."""
        from meetscribe.utils.files import safe_copy

        with pytest.raises(FileNotFoundError):
            safe_copy(tmp_path / "nonexistent.txt", tmp_path / "dest.txt")


class TestSafeMove:
    """Tests for safe_move function."""

    def test_safe_move_success(self, tmp_path):
        """Test successful file move."""
        from meetscribe.utils.files import safe_move

        src = tmp_path / "source.txt"
        src.write_text("content")
        dst = tmp_path / "dest.txt"

        result = safe_move(src, dst)

        assert result == dst
        assert dst.exists()
        assert not src.exists()

    def test_safe_move_no_overwrite(self, tmp_path):
        """Test that safe_move raises error when not overwriting."""
        from meetscribe.utils.files import safe_move

        src = tmp_path / "source.txt"
        src.write_text("content")
        dst = tmp_path / "dest.txt"
        dst.write_text("existing")

        with pytest.raises(FileExistsError):
            safe_move(src, dst)

    def test_safe_move_source_not_found(self, tmp_path):
        """Test safe_move with nonexistent source."""
        from meetscribe.utils.files import safe_move

        with pytest.raises(FileNotFoundError):
            safe_move(tmp_path / "nonexistent.txt", tmp_path / "dest.txt")


class TestSafeDelete:
    """Tests for safe_delete function."""

    def test_safe_delete_file(self, tmp_path):
        """Test deleting a file."""
        from meetscribe.utils.files import safe_delete

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = safe_delete(test_file)

        assert result is True
        assert not test_file.exists()

    def test_safe_delete_empty_directory(self, tmp_path):
        """Test deleting an empty directory."""
        from meetscribe.utils.files import safe_delete

        test_dir = tmp_path / "empty_dir"
        test_dir.mkdir()

        result = safe_delete(test_dir)

        assert result is True
        assert not test_dir.exists()

    def test_safe_delete_directory_recursive(self, tmp_path):
        """Test deleting directory recursively."""
        from meetscribe.utils.files import safe_delete

        test_dir = tmp_path / "dir_with_files"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        result = safe_delete(test_dir, recursive=True)

        assert result is True
        assert not test_dir.exists()

    def test_safe_delete_nonexistent(self, tmp_path):
        """Test deleting nonexistent file."""
        from meetscribe.utils.files import safe_delete

        result = safe_delete(tmp_path / "nonexistent.txt")
        assert result is False


class TestCleanupOldFiles:
    """Tests for cleanup_old_files function."""

    def test_cleanup_old_files_basic(self, tmp_path):
        """Test cleaning up old files."""
        from meetscribe.utils.files import cleanup_old_files

        # Create a file
        test_file = tmp_path / "old.txt"
        test_file.write_text("content")

        # Modify the file's mtime to be old
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(test_file, (old_time, old_time))

        result = cleanup_old_files(tmp_path, max_age_days=5)

        assert len(result) == 1
        assert not test_file.exists()

    def test_cleanup_old_files_dry_run(self, tmp_path):
        """Test cleanup with dry run."""
        from meetscribe.utils.files import cleanup_old_files

        test_file = tmp_path / "old.txt"
        test_file.write_text("content")

        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(test_file, (old_time, old_time))

        result = cleanup_old_files(tmp_path, max_age_days=5, dry_run=True)

        assert len(result) == 1
        assert test_file.exists()  # File should still exist

    def test_cleanup_old_files_with_extensions(self, tmp_path):
        """Test cleanup filtering by extension."""
        from meetscribe.utils.files import cleanup_old_files

        mp3_file = tmp_path / "old.mp3"
        txt_file = tmp_path / "old.txt"
        mp3_file.write_bytes(b"")
        txt_file.write_text("content")

        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(mp3_file, (old_time, old_time))
        os.utime(txt_file, (old_time, old_time))

        result = cleanup_old_files(tmp_path, max_age_days=5, extensions=[".mp3"])

        assert len(result) == 1
        assert not mp3_file.exists()
        assert txt_file.exists()

    def test_cleanup_old_files_nonexistent_dir(self, tmp_path):
        """Test cleanup on nonexistent directory."""
        from meetscribe.utils.files import cleanup_old_files

        result = cleanup_old_files(tmp_path / "nonexistent", max_age_days=5)
        assert result == []


class TestCleanupEmptyDirectories:
    """Tests for cleanup_empty_directories function."""

    def test_cleanup_empty_directories(self, tmp_path):
        """Test cleaning up empty directories."""
        from meetscribe.utils.files import cleanup_empty_directories

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = cleanup_empty_directories(tmp_path)

        assert len(result) == 1
        assert not empty_dir.exists()

    def test_cleanup_empty_directories_nested(self, tmp_path):
        """Test cleaning up nested empty directories."""
        from meetscribe.utils.files import cleanup_empty_directories

        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)

        result = cleanup_empty_directories(tmp_path)

        assert len(result) >= 1
        assert not nested.exists()

    def test_cleanup_empty_directories_dry_run(self, tmp_path):
        """Test cleanup with dry run."""
        from meetscribe.utils.files import cleanup_empty_directories

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = cleanup_empty_directories(tmp_path, dry_run=True)

        assert len(result) == 1
        assert empty_dir.exists()


class TestTempFileOperations:
    """Tests for temporary file operations."""

    def test_create_temp_directory(self):
        """Test creating temporary directory."""
        from meetscribe.utils.files import create_temp_directory

        result = create_temp_directory()

        try:
            assert result.exists()
            assert result.is_dir()
            assert "meetscribe_" in result.name
        finally:
            result.rmdir()

    def test_create_temp_file(self):
        """Test creating temporary file."""
        from meetscribe.utils.files import create_temp_file

        result = create_temp_file(suffix=".txt")

        try:
            assert result.exists()
            assert result.suffix == ".txt"
            assert "meetscribe_" in result.name
        finally:
            result.unlink()


class TestJsonOperations:
    """Tests for JSON file operations."""

    def test_save_json(self, tmp_path):
        """Test saving JSON file."""
        from meetscribe.utils.files import save_json

        data = {"key": "value", "number": 42}
        file_path = tmp_path / "test.json"

        result = save_json(data, file_path)

        assert result == file_path
        assert file_path.exists()

        with open(file_path) as f:
            loaded = json.load(f)
        assert loaded == data

    def test_save_json_creates_parents(self, tmp_path):
        """Test that save_json creates parent directories."""
        from meetscribe.utils.files import save_json

        file_path = tmp_path / "nested" / "dir" / "test.json"
        save_json({"key": "value"}, file_path)

        assert file_path.exists()

    def test_load_json(self, tmp_path):
        """Test loading JSON file."""
        from meetscribe.utils.files import load_json

        data = {"key": "value", "number": 42}
        file_path = tmp_path / "test.json"

        with open(file_path, "w") as f:
            json.dump(data, f)

        result = load_json(file_path)
        assert result == data


class TestAtomicWrite:
    """Tests for atomic_write function."""

    def test_atomic_write_basic(self, tmp_path):
        """Test basic atomic write."""
        from meetscribe.utils.files import atomic_write

        file_path = tmp_path / "test.txt"
        content = "test content"

        result = atomic_write(file_path, content)

        assert result == file_path
        assert file_path.exists()
        assert file_path.read_text() == content

    def test_atomic_write_creates_parents(self, tmp_path):
        """Test that atomic_write creates parent directories."""
        from meetscribe.utils.files import atomic_write

        file_path = tmp_path / "nested" / "dir" / "test.txt"
        atomic_write(file_path, "content")

        assert file_path.exists()


class TestGetDirectorySize:
    """Tests for get_directory_size function."""

    def test_get_directory_size_basic(self, tmp_path):
        """Test getting directory size."""
        from meetscribe.utils.files import get_directory_size

        (tmp_path / "file1.txt").write_text("hello")  # 5 bytes
        (tmp_path / "file2.txt").write_text("world")  # 5 bytes

        result = get_directory_size(tmp_path)
        assert result == 10

    def test_get_directory_size_nested(self, tmp_path):
        """Test getting size of nested directory."""
        from meetscribe.utils.files import get_directory_size

        (tmp_path / "file1.txt").write_text("hello")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("world")

        result = get_directory_size(tmp_path)
        assert result == 10

    def test_get_directory_size_nonexistent(self, tmp_path):
        """Test getting size of nonexistent directory."""
        from meetscribe.utils.files import get_directory_size

        result = get_directory_size(tmp_path / "nonexistent")
        assert result == 0


class TestArchiveMeeting:
    """Tests for archive_meeting function."""

    def test_archive_meeting_basic(self, tmp_path):
        """Test archiving a meeting directory."""
        from meetscribe.utils.files import archive_meeting

        meeting_dir = tmp_path / "meeting"
        meeting_dir.mkdir()
        (meeting_dir / "audio.mp3").write_bytes(b"audio content")
        (meeting_dir / "transcript.txt").write_text("transcript")

        archive_dir = tmp_path / "archives"

        result = archive_meeting(meeting_dir, archive_dir)

        assert result.exists()
        assert archive_dir.exists()

    def test_archive_meeting_not_found(self, tmp_path):
        """Test archiving nonexistent meeting directory."""
        from meetscribe.utils.files import archive_meeting

        with pytest.raises(FileNotFoundError):
            archive_meeting(tmp_path / "nonexistent", tmp_path / "archives")
