"""
File management utilities for MeetScribe.

Provides functions for file operations, cleanup, and organization.
"""

import hashlib
import json
import logging
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


def ensure_directory(path: Path, parents: bool = True) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path
        parents: Create parent directories if needed

    Returns:
        Path to the directory
    """
    path = Path(path)
    path.mkdir(parents=parents, exist_ok=True)
    return path


def get_meeting_directory(base_dir: Path, meeting_id: str, create: bool = True) -> Path:
    """
    Get the directory for a specific meeting.

    Args:
        base_dir: Base meetings directory
        meeting_id: Meeting identifier
        create: Create directory if it doesn't exist

    Returns:
        Path to meeting directory
    """
    meeting_dir = Path(base_dir) / meeting_id
    if create:
        meeting_dir.mkdir(parents=True, exist_ok=True)
    return meeting_dir


def list_meeting_directories(base_dir: Path) -> List[Path]:
    """
    List all meeting directories.

    Args:
        base_dir: Base meetings directory

    Returns:
        List of meeting directory paths
    """
    base_dir = Path(base_dir)
    if not base_dir.exists():
        return []

    return sorted([d for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith(".")])


def find_files_by_extension(
    directory: Path, extensions: List[str], recursive: bool = False
) -> List[Path]:
    """
    Find files with specific extensions in a directory.

    Args:
        directory: Directory to search
        extensions: List of extensions (e.g., ['.mp3', '.wav'])
        recursive: Search subdirectories

    Returns:
        List of matching file paths
    """
    directory = Path(directory)
    if not directory.exists():
        return []

    # Normalize extensions
    extensions = [ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions]

    files = []
    if recursive:
        for ext in extensions:
            files.extend(directory.rglob(f"*{ext}"))
    else:
        for ext in extensions:
            files.extend(directory.glob(f"*{ext}"))

    return sorted(set(files))


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate hash of a file.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256)

    Returns:
        Hex digest string
    """
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """
    Get detailed file information.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file information
    """
    file_path = Path(file_path)
    stat = file_path.stat()

    return {
        "path": str(file_path),
        "name": file_path.name,
        "stem": file_path.stem,
        "suffix": file_path.suffix,
        "size_bytes": stat.st_size,
        "size_human": format_file_size(stat.st_size),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "is_file": file_path.is_file(),
        "is_dir": file_path.is_dir(),
    }


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def safe_copy(src: Path, dst: Path, overwrite: bool = False) -> Path:
    """
    Safely copy a file with optional overwrite protection.

    Args:
        src: Source file path
        dst: Destination file path
        overwrite: Allow overwriting existing files

    Returns:
        Path to copied file
    """
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    if dst.exists() and not overwrite:
        raise FileExistsError(f"Destination already exists: {dst}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    logger.debug(f"Copied {src} -> {dst}")
    return dst


def safe_move(src: Path, dst: Path, overwrite: bool = False) -> Path:
    """
    Safely move a file with optional overwrite protection.

    Args:
        src: Source file path
        dst: Destination file path
        overwrite: Allow overwriting existing files

    Returns:
        Path to moved file
    """
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    if dst.exists() and not overwrite:
        raise FileExistsError(f"Destination already exists: {dst}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    logger.debug(f"Moved {src} -> {dst}")
    return dst


def safe_delete(path: Path, recursive: bool = False) -> bool:
    """
    Safely delete a file or directory.

    Args:
        path: Path to delete
        recursive: Allow recursive deletion for directories

    Returns:
        True if deletion was successful
    """
    path = Path(path)

    if not path.exists():
        return False

    try:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            if recursive:
                shutil.rmtree(path)
            else:
                path.rmdir()
        logger.debug(f"Deleted {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete {path}: {e}")
        return False


def cleanup_old_files(
    directory: Path,
    max_age_days: int,
    extensions: Optional[List[str]] = None,
    dry_run: bool = False,
) -> List[Path]:
    """
    Clean up files older than specified age.

    Args:
        directory: Directory to clean
        max_age_days: Maximum age in days
        extensions: Specific extensions to clean (None = all)
        dry_run: If True, only report what would be deleted

    Returns:
        List of deleted (or would-be-deleted) file paths
    """
    directory = Path(directory)
    if not directory.exists():
        return []

    cutoff = datetime.now() - timedelta(days=max_age_days)
    deleted = []

    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue

        # Check extension filter
        if extensions:
            if file_path.suffix.lower() not in [
                ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions
            ]:
                continue

        # Check age
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        if mtime < cutoff:
            if dry_run:
                logger.info(f"Would delete: {file_path}")
            else:
                safe_delete(file_path)
            deleted.append(file_path)

    if deleted:
        logger.info(f"Cleaned up {len(deleted)} old files from {directory}")

    return deleted


def cleanup_empty_directories(directory: Path, dry_run: bool = False) -> List[Path]:
    """
    Remove empty directories.

    Args:
        directory: Root directory to clean
        dry_run: If True, only report what would be deleted

    Returns:
        List of deleted directories
    """
    directory = Path(directory)
    if not directory.exists():
        return []

    deleted = []

    # Walk bottom-up to handle nested empty directories
    for dir_path in sorted(directory.rglob("*"), reverse=True):
        if dir_path.is_dir() and not any(dir_path.iterdir()):
            if dry_run:
                logger.info(f"Would delete empty directory: {dir_path}")
            else:
                safe_delete(dir_path)
            deleted.append(dir_path)

    return deleted


def create_temp_directory(prefix: str = "meetscribe_") -> Path:
    """
    Create a temporary directory.

    Args:
        prefix: Prefix for directory name

    Returns:
        Path to temporary directory
    """
    return Path(tempfile.mkdtemp(prefix=prefix))


def create_temp_file(
    suffix: str = "", prefix: str = "meetscribe_", directory: Optional[Path] = None
) -> Path:
    """
    Create a temporary file.

    Args:
        suffix: File suffix
        prefix: File prefix
        directory: Directory for temp file

    Returns:
        Path to temporary file
    """
    fd, path = tempfile.mkstemp(
        suffix=suffix, prefix=prefix, dir=str(directory) if directory else None
    )
    os.close(fd)
    return Path(path)


def save_json(
    data: Dict[str, Any], file_path: Path, indent: int = 2, ensure_ascii: bool = False
) -> Path:
    """
    Save data to JSON file.

    Args:
        data: Data to save
        file_path: Output file path
        indent: JSON indentation
        ensure_ascii: Escape non-ASCII characters

    Returns:
        Path to saved file
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii, default=str)

    return file_path


def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Load data from JSON file.

    Args:
        file_path: Input file path

    Returns:
        Loaded data
    """
    file_path = Path(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def atomic_write(file_path: Path, content: str, encoding: str = "utf-8") -> Path:
    """
    Atomically write content to file (write to temp, then rename).

    Args:
        file_path: Target file path
        content: Content to write
        encoding: File encoding

    Returns:
        Path to written file
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file
    temp_path = file_path.parent / f".{file_path.name}.tmp"
    with open(temp_path, "w", encoding=encoding) as f:
        f.write(content)

    # Atomically replace
    temp_path.replace(file_path)
    return file_path


def get_directory_size(directory: Path) -> int:
    """
    Get total size of directory in bytes.

    Args:
        directory: Directory path

    Returns:
        Total size in bytes
    """
    directory = Path(directory)
    if not directory.exists():
        return 0

    total = 0
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            total += file_path.stat().st_size

    return total


def archive_meeting(meeting_dir: Path, archive_dir: Path, compress: bool = True) -> Path:
    """
    Archive a meeting directory.

    Args:
        meeting_dir: Meeting directory to archive
        archive_dir: Directory to store archive
        compress: Use compression

    Returns:
        Path to archive file
    """
    meeting_dir = Path(meeting_dir)
    archive_dir = Path(archive_dir)

    if not meeting_dir.exists():
        raise FileNotFoundError(f"Meeting directory not found: {meeting_dir}")

    archive_dir.mkdir(parents=True, exist_ok=True)

    archive_name = meeting_dir.name
    archive_format = "gztar" if compress else "tar"

    archive_path = shutil.make_archive(
        str(archive_dir / archive_name),
        archive_format,
        root_dir=str(meeting_dir.parent),
        base_dir=meeting_dir.name,
    )

    logger.info(f"Archived {meeting_dir.name} -> {archive_path}")
    return Path(archive_path)
