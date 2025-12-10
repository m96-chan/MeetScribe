"""
Utility modules for MeetScribe.

Audio processing, file management, and helper functions.
"""

from .audio import (
    SUPPORTED_FORMATS,
    analyze_audio_quality,
    convert_audio,
    extract_audio_from_video,
    get_audio_duration,
    get_audio_info,
    get_mime_type,
    is_valid_audio_format,
    merge_audio,
    normalize_audio,
    remove_silence,
    split_audio,
)
from .files import (
    archive_meeting,
    atomic_write,
    calculate_file_hash,
    cleanup_empty_directories,
    cleanup_old_files,
    create_temp_directory,
    create_temp_file,
    ensure_directory,
    find_files_by_extension,
    format_file_size,
    get_directory_size,
    get_file_info,
    get_meeting_directory,
    list_meeting_directories,
    load_json,
    safe_copy,
    safe_delete,
    safe_move,
    save_json,
)

__all__ = [
    # Audio utilities
    "get_audio_info",
    "get_audio_duration",
    "convert_audio",
    "normalize_audio",
    "remove_silence",
    "extract_audio_from_video",
    "split_audio",
    "merge_audio",
    "analyze_audio_quality",
    "is_valid_audio_format",
    "get_mime_type",
    "SUPPORTED_FORMATS",
    # File utilities
    "ensure_directory",
    "get_meeting_directory",
    "list_meeting_directories",
    "find_files_by_extension",
    "calculate_file_hash",
    "get_file_info",
    "format_file_size",
    "safe_copy",
    "safe_move",
    "safe_delete",
    "cleanup_old_files",
    "cleanup_empty_directories",
    "create_temp_directory",
    "create_temp_file",
    "save_json",
    "load_json",
    "atomic_write",
    "get_directory_size",
    "archive_meeting",
]
