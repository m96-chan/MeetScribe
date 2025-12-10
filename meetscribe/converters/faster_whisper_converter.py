"""
faster-whisper CONVERT provider for MeetScribe.

Uses faster-whisper for local GPU-accelerated transcription.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.meeting_id import parse_meeting_id
from ..core.models import AudioInfo, MeetingInfo, Segment, Transcript
from ..core.providers import ConvertProvider

logger = logging.getLogger(__name__)


class FasterWhisperConverter(ConvertProvider):
    """
    faster-whisper converter for local transcription.

    Uses CTranslate2 for efficient inference on GPU or CPU.
    """

    # Available model sizes
    MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize faster-whisper converter.

        Config params:
            model_size: Model size (tiny, base, small, medium, large-v2, large-v3)
            device: Device to use (cuda, cpu, auto)
            compute_type: Computation type (float16, int8, int8_float16, etc.)
            language: Source language code (optional, auto-detect if not set)
            beam_size: Beam size for decoding (default: 5)
            vad_filter: Enable VAD filtering (default: True)
            vad_parameters: VAD filter parameters (dict)
            word_timestamps: Include word-level timestamps (default: False)
            initial_prompt: Optional prompt to guide transcription
            model_path: Custom model path (optional)
        """
        super().__init__(config)

        # Model settings
        self.model_size = config.get("model_size", "base")
        self.device = config.get("device", "auto")
        self.compute_type = config.get("compute_type", "default")
        self.language = config.get("language")
        self.beam_size = config.get("beam_size", 5)
        self.vad_filter = config.get("vad_filter", True)
        self.vad_parameters = config.get("vad_parameters", {})
        self.word_timestamps = config.get("word_timestamps", False)
        self.initial_prompt = config.get("initial_prompt")
        self.model_path = config.get("model_path")

        # Model instance
        self.model = None
        self._init_model()

    def _init_model(self):
        """Initialize faster-whisper model."""
        try:
            from faster_whisper import WhisperModel

            # Determine model path
            model_path = self.model_path or self.model_size

            # Determine compute type
            compute_type = self.compute_type
            if compute_type == "default":
                if self.device == "cuda":
                    compute_type = "float16"
                else:
                    compute_type = "int8"

            logger.info(
                f"Loading faster-whisper model: {model_path} "
                f"(device={self.device}, compute_type={compute_type})"
            )

            self.model = WhisperModel(
                model_path,
                device=self.device,
                compute_type=compute_type,
            )

            logger.info("faster-whisper model loaded successfully")

        except ImportError:
            logger.warning(
                "faster-whisper not installed. Run: pip install faster-whisper\n"
                "Running in mock mode."
            )
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load faster-whisper model: {e}")
            logger.warning("Running in mock mode")
            self.model = None

    def transcribe(self, audio_path: Path, meeting_id: str) -> Transcript:
        """
        Transcribe audio using faster-whisper.

        Args:
            audio_path: Path to audio file
            meeting_id: Meeting identifier

        Returns:
            Transcript object with text and segments
        """
        logger.info(f"Transcribing {audio_path} using faster-whisper")

        # Validate file
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Parse meeting ID
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

        # Perform transcription
        if self.model:
            segments, info = self._transcribe_with_model(audio_path)
        else:
            segments, info = self._mock_transcription(audio_path)

        # Build full text
        full_text = " ".join(seg.text for seg in segments)

        # Get audio info
        audio_info = AudioInfo(
            duration=info.get("duration", 0),
            samplerate=16000,  # Whisper uses 16kHz
            codec=audio_path.suffix.lower().replace(".", ""),
            channels=1,
        )

        # Build transcript
        transcript = Transcript(
            meeting_info=meeting_info,
            text=full_text,
            audio_path=audio_path,
            segments=segments,
            audio_info=audio_info,
            metadata={
                "converter": "faster-whisper",
                "model": self.model_size,
                "language": info.get("language", self.language or "auto"),
                "language_probability": info.get("language_probability", 0),
                "duration": info.get("duration", 0),
            },
        )

        transcript.add_processing_step(
            "faster_whisper_transcribe",
            {
                "model": self.model_size,
                "device": self.device,
                "language": info.get("language"),
                "duration": info.get("duration"),
                "segments_count": len(segments),
                "vad_filter": self.vad_filter,
            },
        )

        logger.info(
            f"Transcription complete: {len(segments)} segments, " f"{len(full_text)} characters"
        )
        return transcript

    def _transcribe_with_model(self, audio_path: Path) -> Tuple[List[Segment], Dict[str, Any]]:
        """Perform actual transcription with model."""
        logger.info(f"Running faster-whisper on {audio_path.name}")

        # Build transcription options
        options = {
            "beam_size": self.beam_size,
            "vad_filter": self.vad_filter,
            "word_timestamps": self.word_timestamps,
        }

        if self.language:
            options["language"] = self.language
        if self.initial_prompt:
            options["initial_prompt"] = self.initial_prompt
        if self.vad_parameters:
            options["vad_parameters"] = self.vad_parameters

        # Run transcription
        raw_segments, info = self.model.transcribe(str(audio_path), **options)

        # Convert segments
        segments = []
        for seg in raw_segments:
            segment = Segment(
                start=seg.start,
                end=seg.end,
                text=seg.text.strip(),
                confidence=seg.avg_logprob if hasattr(seg, "avg_logprob") else None,
                language=info.language,
            )
            segments.append(segment)

        # Build info dict
        result_info = {
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
        }

        return segments, result_info

    def _mock_transcription(self, audio_path: Path) -> Tuple[List[Segment], Dict[str, Any]]:
        """Return mock transcription for testing."""
        logger.info(f"[MOCK] Transcribing {audio_path.name}")

        # Estimate duration from file size
        file_size = audio_path.stat().st_size
        estimated_duration = file_size / (1024 * 1024) * 60  # ~1MB per minute

        segments = [
            Segment(
                start=0.0,
                end=5.0,
                text="This is a mock transcription from faster-whisper.",
                confidence=0.95,
                language="en",
            ),
            Segment(
                start=5.0,
                end=10.0,
                text="Local GPU transcription provides fast results.",
                confidence=0.93,
                language="en",
            ),
            Segment(
                start=10.0,
                end=15.0,
                text="The meeting covered several important topics.",
                confidence=0.91,
                language="en",
            ),
            Segment(
                start=15.0,
                end=20.0,
                text="Action items were assigned to team members.",
                confidence=0.94,
                language="en",
            ),
        ]

        info = {
            "language": "en",
            "language_probability": 0.98,
            "duration": estimated_duration,
        }

        return segments, info

    def validate_config(self) -> bool:
        """
        Validate converter configuration.

        Returns:
            True if config is valid

        Raises:
            ValueError: If config is invalid
        """
        if self.model_size not in self.MODEL_SIZES and not self.model_path:
            raise ValueError(
                f"model_size must be one of: {self.MODEL_SIZES} " f"or provide model_path"
            )

        if self.beam_size < 1 or self.beam_size > 10:
            raise ValueError("beam_size must be between 1 and 10")

        valid_devices = ["cuda", "cpu", "auto"]
        if self.device not in valid_devices:
            raise ValueError(f"device must be one of: {valid_devices}")

        return True
