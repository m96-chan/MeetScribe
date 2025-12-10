"""
File INPUT provider for MeetScribe.

Directly uses an existing audio file as input.
Supports various audio formats and preprocessing.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.providers import InputProvider

logger = logging.getLogger(__name__)


class FileProvider(InputProvider):
    """
    File-based INPUT provider.

    Supports single files, directories, and glob patterns.
    Includes audio validation and optional preprocessing.
    """

    # Supported audio formats
    SUPPORTED_FORMATS = [
        ".mp3",
        ".wav",
        ".m4a",
        ".flac",
        ".ogg",
        ".webm",
        ".aac",
        ".wma",
        ".opus",
        ".mp4",
        ".mkv",
        ".avi",
    ]

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize file provider.

        Config params:
            audio_path: Path to audio file or directory
            pattern: Glob pattern for matching files (e.g., "*.mp3")
            copy_to_working_dir: Whether to copy file (default: False)
            working_dir: Working directory (default: ./meetings)
            validate_format: Validate audio format (default: True)
            convert_to_format: Convert to specific format (e.g., "wav")
            max_file_size: Maximum file size in bytes
            metadata_path: Path to JSON metadata file
        """
        super().__init__(config)
        self.audio_path = Path(config["audio_path"])
        self.pattern = config.get("pattern")
        self.copy_to_working_dir = config.get("copy_to_working_dir", False)
        self.working_dir = Path(config.get("working_dir", "./meetings"))
        self.validate_format = config.get("validate_format", True)
        self.convert_to_format = config.get("convert_to_format")
        self.max_file_size = config.get("max_file_size")
        self.metadata_path = config.get("metadata_path")

        # Loaded metadata
        self._metadata: Optional[Dict[str, Any]] = None

    def record(self, meeting_id: str) -> Path:
        """
        Get audio file path.

        Args:
            meeting_id: Meeting identifier

        Returns:
            Path to audio file

        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If file format is invalid
        """
        # Resolve audio path
        audio_path = self._resolve_audio_path()

        # Validate file
        self._validate_audio_file(audio_path)

        logger.info(f"Using audio file: {audio_path}")

        # Load metadata if available
        self._load_metadata()

        # Process file
        if self.copy_to_working_dir or self.convert_to_format:
            audio_path = self._process_file(audio_path, meeting_id)

        return audio_path

    def _resolve_audio_path(self) -> Path:
        """Resolve audio path from config."""
        if self.audio_path.is_file():
            return self.audio_path

        if self.audio_path.is_dir():
            # Use pattern or find first audio file
            if self.pattern:
                files = list(self.audio_path.glob(self.pattern))
            else:
                files = [
                    f
                    for f in self.audio_path.iterdir()
                    if f.is_file() and f.suffix.lower() in self.SUPPORTED_FORMATS
                ]

            if not files:
                raise FileNotFoundError(f"No audio files found in {self.audio_path}")

            # Sort by modification time, newest first
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            return files[0]

        raise FileNotFoundError(f"Audio path not found: {self.audio_path}")

    def _validate_audio_file(self, audio_path: Path):
        """Validate audio file."""
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Check format
        if self.validate_format:
            suffix = audio_path.suffix.lower()
            if suffix not in self.SUPPORTED_FORMATS:
                raise ValueError(
                    f"Unsupported audio format: {suffix}. "
                    f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
                )

        # Check file size
        if self.max_file_size:
            file_size = audio_path.stat().st_size
            if file_size > self.max_file_size:
                raise ValueError(
                    f"File too large: {file_size} bytes. " f"Maximum: {self.max_file_size} bytes"
                )

    def _load_metadata(self):
        """Load metadata from JSON file if specified."""
        if not self.metadata_path:
            return

        metadata_file = Path(self.metadata_path)
        if metadata_file.exists():
            try:
                with open(metadata_file, encoding="utf-8") as f:
                    self._metadata = json.load(f)
                logger.info(f"Loaded metadata from {metadata_file}")
            except Exception as e:
                logger.warning(f"Could not load metadata: {e}")

    def _process_file(self, audio_path: Path, meeting_id: str) -> Path:
        """Process and optionally convert audio file."""
        # Create meeting directory
        meeting_dir = self.working_dir / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)

        # Determine output format
        if self.convert_to_format:
            output_suffix = f".{self.convert_to_format.lstrip('.')}"
        else:
            output_suffix = audio_path.suffix

        dest_path = meeting_dir / f"audio{output_suffix}"

        # Convert or copy
        if self.convert_to_format and audio_path.suffix.lower() != output_suffix.lower():
            dest_path = self._convert_audio(audio_path, dest_path)
        else:
            logger.info(f"Copying audio to: {dest_path}")
            shutil.copy2(audio_path, dest_path)

        # Save metadata
        if self._metadata:
            meta_path = meeting_dir / "input_metadata.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(self._metadata, f, indent=2)

        return dest_path

    def _convert_audio(self, input_path: Path, output_path: Path) -> Path:
        """Convert audio file to different format."""
        logger.info(f"Converting {input_path} to {output_path}")

        try:
            from pydub import AudioSegment

            # Load audio
            audio = AudioSegment.from_file(str(input_path))

            # Export to new format
            output_format = output_path.suffix.lower().lstrip(".")
            audio.export(str(output_path), format=output_format)

            logger.info(f"Converted audio saved to: {output_path}")
            return output_path

        except ImportError:
            logger.warning("pydub not installed. Run: pip install pydub\n" "Falling back to copy.")
            shutil.copy2(input_path, output_path)
            return output_path

        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            # Fall back to copy
            shutil.copy2(input_path, output_path.with_suffix(input_path.suffix))
            return output_path.with_suffix(input_path.suffix)

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Get loaded metadata."""
        return self._metadata

    def list_available_files(self) -> List[Path]:
        """List all available audio files in directory."""
        if self.audio_path.is_file():
            return [self.audio_path]

        if self.audio_path.is_dir():
            if self.pattern:
                return list(self.audio_path.glob(self.pattern))
            else:
                return [
                    f
                    for f in self.audio_path.iterdir()
                    if f.is_file() and f.suffix.lower() in self.SUPPORTED_FORMATS
                ]

        return []

    def validate_config(self) -> bool:
        """
        Validate provider configuration.

        Returns:
            True if config is valid

        Raises:
            ValueError: If config is invalid
        """
        if "audio_path" not in self.config:
            raise ValueError("'audio_path' is required in config")

        if self.convert_to_format:
            valid_formats = ["wav", "mp3", "flac", "ogg", "m4a"]
            if self.convert_to_format.lower() not in valid_formats:
                raise ValueError(f"convert_to_format must be one of: {valid_formats}")

        return True
