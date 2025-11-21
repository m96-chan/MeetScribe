"""
File INPUT provider for MeetScribe.

Directly uses an existing audio file as input.
This is useful for PoC and testing purposes.
"""

from pathlib import Path
from typing import Dict, Any
import shutil
import logging

from ..core.providers import InputProvider


logger = logging.getLogger(__name__)


class FileProvider(InputProvider):
    """
    File-based INPUT provider.

    Simply copies or uses an existing audio file.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize file provider.

        Config params:
            audio_path: Path to audio file
            copy_to_working_dir: Whether to copy file (default: False)
        """
        super().__init__(config)
        self.audio_path = Path(config['audio_path'])
        self.copy_to_working_dir = config.get('copy_to_working_dir', False)
        self.working_dir = Path(config.get('working_dir', './meetings'))

    def record(self, meeting_id: str) -> Path:
        """
        Get audio file path.

        Args:
            meeting_id: Meeting identifier

        Returns:
            Path to audio file

        Raises:
            FileNotFoundError: If audio file doesn't exist
        """
        if not self.audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {self.audio_path}")

        logger.info(f"Using audio file: {self.audio_path}")

        if self.copy_to_working_dir:
            # Create meeting directory
            meeting_dir = self.working_dir / meeting_id
            meeting_dir.mkdir(parents=True, exist_ok=True)

            # Copy audio file
            dest_path = meeting_dir / f"audio{self.audio_path.suffix}"
            logger.info(f"Copying audio to: {dest_path}")
            shutil.copy2(self.audio_path, dest_path)

            return dest_path
        else:
            # Use original file directly
            return self.audio_path

    def validate_config(self) -> bool:
        """
        Validate provider configuration.

        Returns:
            True if config is valid

        Raises:
            ValueError: If config is invalid
        """
        if 'audio_path' not in self.config:
            raise ValueError("'audio_path' is required in config")

        return True
