"""
Passthrough CONVERT provider for MeetScribe.

Does not perform transcription - passes audio directly to LLM layer.
Used when LLM can consume audio files directly (e.g., NotebookLM, ChatGPT Audio).
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from ..core.meeting_id import parse_meeting_id
from ..core.models import AudioInfo, MeetingInfo, Transcript
from ..core.providers import ConvertProvider

logger = logging.getLogger(__name__)


class PassthroughConverter(ConvertProvider):
    """
    Passthrough converter that doesn't transcribe.

    Simply wraps the audio file in a Transcript object
    for downstream LLM processing.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize passthrough converter.

        Config params:
            include_audio_info: Whether to analyze audio metadata (default: True)
        """
        super().__init__(config)
        self.include_audio_info = config.get("include_audio_info", True)

    def transcribe(self, audio_path: Path, meeting_id: str) -> Transcript:
        """
        Create Transcript object without transcription.

        Args:
            audio_path: Path to audio file
            meeting_id: Meeting identifier

        Returns:
            Transcript object with audio_path but no text
        """
        logger.info(f"Passthrough mode: skipping transcription for {audio_path}")

        # Parse meeting ID to get metadata
        try:
            start_time, source_type, channel = parse_meeting_id(meeting_id)
        except ValueError:
            logger.warning(f"Could not parse meeting_id: {meeting_id}")
            start_time = datetime.now()
            source_type = "unknown"
            channel = "unknown"

        # Create meeting info
        meeting_info = MeetingInfo(
            meeting_id=meeting_id,
            source_type=source_type,
            start_time=start_time,
            channel_id=channel,
        )

        # Get audio info if requested
        audio_info = None
        if self.include_audio_info:
            audio_info = self._get_audio_info(audio_path)

        # Create transcript with audio path only
        transcript = Transcript(
            meeting_info=meeting_info,
            text=None,  # No transcription
            audio_path=audio_path,
            audio_info=audio_info,
            metadata={
                "converter": "passthrough",
                "mode": "audio_only",
                "note": "Audio will be processed directly by LLM",
            },
        )

        transcript.add_processing_step(
            "passthrough_convert",
            {
                "converter": "passthrough",
                "audio_path": str(audio_path),
                "audio_exists": audio_path.exists(),
            },
        )

        logger.info(f"Passthrough conversion complete for {meeting_id}")
        return transcript

    def _get_audio_info(self, audio_path: Path) -> AudioInfo:
        """
        Get basic audio file information.

        Args:
            audio_path: Path to audio file

        Returns:
            AudioInfo object with basic metadata
        """
        try:
            # For PoC, just use file size and basic info
            file_size = audio_path.stat().st_size
            file_extension = audio_path.suffix.lower()

            # Estimate duration based on file size (rough approximation)
            # Assume ~1MB per minute for MP3/M4A
            estimated_duration = file_size / (1024 * 1024)  # minutes

            return AudioInfo(
                duration=estimated_duration * 60,  # seconds
                samplerate=44100,  # default assumption
                codec=file_extension.replace(".", ""),
                channels=2,  # stereo assumption
            )
        except Exception as e:
            logger.warning(f"Could not get audio info: {e}")
            return AudioInfo(duration=0, samplerate=0, codec="unknown", channels=0)

    def validate_config(self) -> bool:
        """
        Validate converter configuration.

        Returns:
            True if config is valid
        """
        # Passthrough has no required config
        return True
