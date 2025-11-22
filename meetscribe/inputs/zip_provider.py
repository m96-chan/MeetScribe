"""
ZIP INPUT provider for MeetScribe.

Extracts audio files and metadata from ZIP archives.
Supports both single mode (first file only) and multiple mode (all files).
"""

import zipfile
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..core.providers import InputProvider


logger = logging.getLogger(__name__)


class ZipProvider(InputProvider):
    """
    ZIP-based INPUT provider.

    Extracts audio files and metadata from ZIP archives.
    """

    SUPPORTED_AUDIO_FORMATS = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus'}
    METADATA_FILES = {'metadata.json', 'metadata.yaml', 'info.json', 'info.yaml'}

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ZIP provider.

        Config params:
            zip_path: Path to ZIP file
            working_dir: Directory to extract files (default: './meetings')
            mode: 'single' or 'multiple' (default: 'single')
            cleanup_after_extraction: Delete ZIP after extraction (default: False)
            sort_by: Sort method for multiple mode ('name', 'modified', 'size') (default: 'name')
        """
        super().__init__(config)

        # Set attributes before validation (so validate_config can check them)
        self.mode = config.get('mode', 'single')

        # Validate configuration
        self.validate_config()

        # Set remaining attributes after validation
        self.zip_path = Path(config['zip_path'])
        self.working_dir = Path(config.get('working_dir', './meetings'))
        self.cleanup_after = config.get('cleanup_after_extraction', False)
        self.sort_by = config.get('sort_by', 'name')
        self.metadata: Optional[Dict] = None

    def record(self, meeting_id: str) -> Path:
        """
        Extract ZIP and return first audio file path.

        Args:
            meeting_id: Meeting identifier

        Returns:
            Path to first audio file

        Raises:
            FileNotFoundError: If ZIP file doesn't exist
            ValueError: If no audio files found
            zipfile.BadZipFile: If ZIP is corrupted
        """
        # 1. Validate ZIP exists
        if not self.zip_path.exists():
            raise FileNotFoundError(f"ZIP file not found: {self.zip_path}")

        # 2. Create extraction directory
        extract_dir = self.working_dir / meeting_id / 'extracted'
        extract_dir.mkdir(parents=True, exist_ok=True)

        # 3. Extract ZIP
        logger.info(f"Extracting ZIP: {self.zip_path} -> {extract_dir}")
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # 4. Find audio files
        audio_files = self._find_audio_files(extract_dir)
        if not audio_files:
            raise ValueError(f"No audio files found in ZIP: {self.zip_path}")

        # 5. Load metadata (if exists)
        self.metadata = self._load_metadata(extract_dir)

        # 6. Return first audio file
        logger.info(f"Returning first audio file: {audio_files[0]}")
        return audio_files[0]

    def record_multiple(self, meeting_id: str) -> List[Path]:
        """
        Extract ZIP and return all audio file paths.

        Args:
            meeting_id: Meeting identifier

        Returns:
            List of paths to all audio files

        Raises:
            FileNotFoundError: If ZIP file doesn't exist
            ValueError: If no audio files found
            zipfile.BadZipFile: If ZIP is corrupted
        """
        # 1. Validate ZIP exists
        if not self.zip_path.exists():
            raise FileNotFoundError(f"ZIP file not found: {self.zip_path}")

        # 2. Create extraction directory
        extract_dir = self.working_dir / meeting_id / 'extracted'
        extract_dir.mkdir(parents=True, exist_ok=True)

        # 3. Extract ZIP
        logger.info(f"Extracting ZIP: {self.zip_path} -> {extract_dir}")
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # 4. Find audio files
        audio_files = self._find_audio_files(extract_dir)
        if not audio_files:
            raise ValueError(f"No audio files found in ZIP: {self.zip_path}")

        # 5. Load metadata (if exists)
        self.metadata = self._load_metadata(extract_dir)

        # 6. Return all audio files
        logger.info(f"Returning {len(audio_files)} audio files")
        return audio_files

    def _find_audio_files(self, directory: Path) -> List[Path]:
        """
        Find all audio files in directory recursively.

        Args:
            directory: Directory to search

        Returns:
            List of audio file paths, sorted according to sort_by setting
        """
        audio_files = []
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_AUDIO_FORMATS:
                audio_files.append(file_path)

        # Sort files based on configuration
        if self.sort_by == 'name':
            audio_files.sort(key=lambda p: p.name)
        elif self.sort_by == 'modified':
            audio_files.sort(key=lambda p: p.stat().st_mtime)
        elif self.sort_by == 'size':
            audio_files.sort(key=lambda p: p.stat().st_size)

        logger.info(f"Found {len(audio_files)} audio files (sorted by {self.sort_by})")
        return audio_files

    def _load_metadata(self, directory: Path) -> Optional[Dict]:
        """
        Load metadata file if exists.

        Args:
            directory: Directory to search for metadata

        Returns:
            Dictionary with metadata if found, None otherwise
        """
        for metadata_file in self.METADATA_FILES:
            metadata_path = directory / metadata_file
            if metadata_path.exists():
                logger.info(f"Loading metadata: {metadata_path}")
                if metadata_path.suffix == '.json':
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                # TODO: Add YAML support if needed
                # elif metadata_path.suffix in ['.yaml', '.yml']:
                #     import yaml
                #     with open(metadata_path, 'r', encoding='utf-8') as f:
                #         return yaml.safe_load(f)

        # Also check recursively in subdirectories
        for metadata_file in self.METADATA_FILES:
            for metadata_path in directory.rglob(metadata_file):
                if metadata_path.is_file():
                    logger.info(f"Loading metadata from subdirectory: {metadata_path}")
                    if metadata_path.suffix == '.json':
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            return json.load(f)

        logger.info("No metadata file found")
        return None

    def validate_config(self) -> bool:
        """
        Validate provider configuration.

        Returns:
            True if config is valid

        Raises:
            ValueError: If config is invalid
        """
        if 'zip_path' not in self.config:
            raise ValueError("'zip_path' is required in config")

        if self.mode not in ['single', 'multiple']:
            raise ValueError(f"Invalid mode: {self.mode}. Must be 'single' or 'multiple'")

        return True
