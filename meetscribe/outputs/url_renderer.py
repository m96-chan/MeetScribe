"""
URL OUTPUT renderer for MeetScribe.

Simply displays the NotebookLM URL and optionally saves basic info.
"""

from pathlib import Path
from typing import Dict, Any
import json
import logging

from ..core.providers import OutputRenderer
from ..core.models import Minutes


logger = logging.getLogger(__name__)


class URLRenderer(OutputRenderer):
    """
    URL-based OUTPUT renderer.

    Displays the NotebookLM URL and saves basic meeting info.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize URL renderer.

        Config params:
            output_dir: Directory to save meeting info (optional)
            save_metadata: Whether to save metadata file (default: True)
        """
        super().__init__(config)
        self.output_dir = Path(config.get('output_dir', './meetings'))
        self.save_metadata = config.get('save_metadata', True)

    def render(self, minutes: Minutes, meeting_id: str) -> str:
        """
        Render minutes as URL display.

        Args:
            minutes: Minutes object
            meeting_id: Meeting identifier

        Returns:
            NotebookLM URL or path to saved metadata
        """
        logger.info(f"Rendering URL output for {meeting_id}")

        # Get NotebookLM URL
        url = minutes.url
        if not url:
            logger.warning("No URL found in minutes")
            url = "No URL available"

        # Display URL
        logger.info("=" * 80)
        logger.info(f"NotebookLM URL: {url}")
        logger.info("=" * 80)

        # Optionally save metadata
        if self.save_metadata:
            metadata_path = self._save_metadata(minutes, meeting_id)
            logger.info(f"Metadata saved to: {metadata_path}")
            return str(metadata_path)

        return url

    def _save_metadata(self, minutes: Minutes, meeting_id: str) -> Path:
        """
        Save meeting metadata to JSON file.

        Args:
            minutes: Minutes object
            meeting_id: Meeting identifier

        Returns:
            Path to saved metadata file
        """
        # Create output directory
        meeting_dir = self.output_dir / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)

        # Create metadata file
        metadata_path = meeting_dir / "meeting_info.json"

        metadata = {
            'meeting_id': meeting_id,
            'notebooklm_url': minutes.url,
            'summary': minutes.summary,
            'decisions_count': len(minutes.decisions),
            'action_items_count': len(minutes.action_items),
            'key_points_count': len(minutes.key_points),
            'participants': minutes.participants,
            'generated_at': minutes.generated_at.isoformat(),
            'metadata': minutes.metadata
        }

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Metadata saved: {metadata_path}")
        return metadata_path

    def validate_config(self) -> bool:
        """
        Validate renderer configuration.

        Returns:
            True if config is valid
        """
        # No required config for URL renderer
        return True
