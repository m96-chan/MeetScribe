"""
Gemini Audio CONVERT provider for MeetScribe.

Uses Google's Gemini API for audio transcription and analysis.
"""

import base64
import logging
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ..core.meeting_id import parse_meeting_id
from ..core.models import AudioInfo, MeetingInfo, Segment, Transcript
from ..core.providers import ConvertProvider

logger = logging.getLogger(__name__)


class GeminiAudioConverter(ConvertProvider):
    """
    Gemini Audio converter using Google's Gemini API.

    Supports direct audio processing with transcription and analysis.
    """

    # Supported audio formats
    SUPPORTED_FORMATS = [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".aac"]
    # Maximum file size (20MB for inline, larger for File API)
    MAX_INLINE_SIZE = 20 * 1024 * 1024
    MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB via File API

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Gemini Audio converter.

        Config params:
            api_key: Gemini API key (or from GEMINI_API_KEY env)
            model: Model name (default: "gemini-2.0-flash-exp")
            language: Target language for transcription
            include_timestamps: Include timestamps in transcription
            include_speaker_labels: Attempt speaker diarization
            use_file_api: Use File API for large files
            generation_config: Custom generation config (dict)
        """
        super().__init__(config)

        # API credentials
        self.api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("No Gemini API key provided - running in mock mode")

        # Model settings
        self.model_name = config.get("model", "gemini-2.0-flash-exp")
        self.language = config.get("language", "auto")
        self.include_timestamps = config.get("include_timestamps", True)
        self.include_speaker_labels = config.get("include_speaker_labels", False)
        self.use_file_api = config.get("use_file_api", False)
        self.generation_config = config.get("generation_config", {})

        # Initialize client
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize Gemini client."""
        if not self.api_key:
            logger.info("Running Gemini converter in mock mode")
            return

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model_name)
            logger.info(f"Gemini client initialized with model: {self.model_name}")
        except ImportError:
            logger.error(
                "google-generativeai package not installed. " "Run: pip install google-generativeai"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    def transcribe(self, audio_path: Path, meeting_id: str) -> Transcript:
        """
        Transcribe audio using Gemini API.

        Args:
            audio_path: Path to audio file
            meeting_id: Meeting identifier

        Returns:
            Transcript object with text and segments
        """
        logger.info(f"Transcribing {audio_path} using Gemini API")

        # Validate file
        self._validate_audio_file(audio_path)

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
        if self.client:
            result = self._transcribe_with_api(audio_path)
        else:
            result = self._mock_transcription(audio_path)

        # Parse segments
        segments = self._parse_segments(result)

        # Get audio info
        audio_info = self._get_audio_info(audio_path, result)

        # Build transcript
        transcript = Transcript(
            meeting_info=meeting_info,
            text=result.get("text", ""),
            audio_path=audio_path,
            segments=segments,
            audio_info=audio_info,
            metadata={
                "converter": "gemini-audio",
                "model": self.model_name,
                "language": result.get("language", self.language),
                "duration": result.get("duration", 0),
            },
        )

        transcript.add_processing_step(
            "gemini_audio_transcribe",
            {
                "model": self.model_name,
                "language": result.get("language"),
                "segments_count": len(segments),
                "include_timestamps": self.include_timestamps,
            },
        )

        logger.info(
            f"Transcription complete: {len(segments)} segments, "
            f"{len(transcript.text)} characters"
        )
        return transcript

    def _validate_audio_file(self, audio_path: Path):
        """Validate audio file for Gemini API."""
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Check file format
        suffix = audio_path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported audio format: {suffix}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # Check file size
        file_size = audio_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"Audio file too large: {file_size / 1024 / 1024:.1f}MB. "
                f"Maximum: {self.MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
            )

    def _transcribe_with_api(self, audio_path: Path) -> Dict[str, Any]:
        """Perform actual API transcription."""
        import google.generativeai as genai

        logger.info(f"Calling Gemini API for {audio_path.name}")

        file_size = audio_path.stat().st_size

        # Use File API for large files
        if file_size > self.MAX_INLINE_SIZE or self.use_file_api:
            audio_content = self._upload_to_file_api(audio_path)
        else:
            audio_content = self._prepare_inline_audio(audio_path)

        # Build transcription prompt
        prompt = self._build_transcription_prompt()

        # Configure generation
        gen_config = genai.GenerationConfig(
            temperature=self.generation_config.get("temperature", 0),
            max_output_tokens=self.generation_config.get("max_output_tokens", 8192),
        )

        # Call API
        response = self.client.generate_content(
            [prompt, audio_content],
            generation_config=gen_config,
        )

        # Parse response
        return self._parse_response(response)

    def _prepare_inline_audio(self, audio_path: Path) -> Dict[str, Any]:
        """Prepare audio for inline upload."""

        mime_type = mimetypes.guess_type(str(audio_path))[0] or "audio/mpeg"

        with open(audio_path, "rb") as f:
            audio_data = f.read()

        return {
            "mime_type": mime_type,
            "data": base64.standard_b64encode(audio_data).decode("utf-8"),
        }

    def _upload_to_file_api(self, audio_path: Path):
        """Upload audio using File API."""
        import google.generativeai as genai

        logger.info(f"Uploading {audio_path.name} via File API")

        mime_type = mimetypes.guess_type(str(audio_path))[0] or "audio/mpeg"

        uploaded_file = genai.upload_file(
            path=str(audio_path),
            mime_type=mime_type,
        )

        logger.info(f"File uploaded: {uploaded_file.name}")
        return uploaded_file

    def _build_transcription_prompt(self) -> str:
        """Build the transcription prompt."""
        prompt_parts = [
            "Please transcribe the following audio accurately.",
        ]

        if self.language != "auto":
            prompt_parts.append(f"The audio is in {self.language}.")

        if self.include_timestamps:
            prompt_parts.append("Include timestamps for each segment in the format [HH:MM:SS].")

        if self.include_speaker_labels:
            prompt_parts.append(
                "If multiple speakers are present, label them as Speaker 1, Speaker 2, etc."
            )

        prompt_parts.append(
            "\nProvide the transcription in a clear, readable format. "
            "At the end, provide a brief summary of the detected language and duration."
        )

        return "\n".join(prompt_parts)

    def _parse_response(self, response) -> Dict[str, Any]:
        """Parse Gemini API response."""
        text = response.text

        # Extract segments from timestamped text
        segments = []
        lines = text.split("\n")
        current_time = 0.0

        for line in lines:
            line = line.strip()
            if not line or line.startswith("Language:") or line.startswith("Duration:"):
                continue

            # Try to parse timestamp
            import re

            timestamp_match = re.match(r"\[(\d{2}):(\d{2}):(\d{2})\](.+)", line)
            if timestamp_match:
                hours, minutes, seconds, content = timestamp_match.groups()
                start_time = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
                segments.append(
                    {
                        "start": float(start_time),
                        "end": float(start_time + 5),  # Estimate
                        "text": content.strip(),
                    }
                )
                current_time = start_time + 5
            elif line:
                segments.append(
                    {
                        "start": current_time,
                        "end": current_time + 5,
                        "text": line,
                    }
                )
                current_time += 5

        return {
            "text": text,
            "segments": segments,
            "language": self._detect_language(text),
            "duration": current_time,
        }

    def _detect_language(self, text: str) -> str:
        """Simple language detection from text."""
        # Look for explicit language declaration
        import re

        lang_match = re.search(r"Language:\s*(\w+)", text)
        if lang_match:
            return lang_match.group(1).lower()
        return self.language if self.language != "auto" else "unknown"

    def _mock_transcription(self, audio_path: Path) -> Dict[str, Any]:
        """Return mock transcription for testing."""
        logger.info(f"[MOCK] Transcribing {audio_path.name}")

        file_size = audio_path.stat().st_size
        estimated_duration = file_size / (1024 * 1024) * 60

        return {
            "text": (
                "[00:00:00] This is a mock transcription from Gemini Audio.\n"
                "[00:00:05] The Gemini model provides excellent audio understanding.\n"
                "[00:00:10] Meeting topics included project updates and planning.\n"
                "[00:00:15] Key decisions were documented for follow-up.\n\n"
                "Language: English\n"
                f"Duration: {estimated_duration:.0f} seconds"
            ),
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "This is a mock transcription from Gemini Audio.",
                },
                {
                    "start": 5.0,
                    "end": 10.0,
                    "text": "The Gemini model provides excellent audio understanding.",
                },
                {
                    "start": 10.0,
                    "end": 15.0,
                    "text": "Meeting topics included project updates and planning.",
                },
                {
                    "start": 15.0,
                    "end": 20.0,
                    "text": "Key decisions were documented for follow-up.",
                },
            ],
            "language": "en",
            "duration": estimated_duration,
        }

    def _parse_segments(self, result: Dict[str, Any]) -> List[Segment]:
        """Parse segments from result."""
        segments = []
        for seg in result.get("segments", []):
            segments.append(
                Segment(
                    start=seg.get("start", 0),
                    end=seg.get("end", 0),
                    text=seg.get("text", "").strip(),
                    speaker=seg.get("speaker"),
                    language=result.get("language"),
                )
            )
        return segments

    def _get_audio_info(self, audio_path: Path, result: Dict[str, Any]) -> AudioInfo:
        """Extract audio information."""
        try:
            return AudioInfo(
                duration=result.get("duration", 0),
                samplerate=44100,
                codec=audio_path.suffix.lower().replace(".", ""),
                channels=2,
            )
        except Exception as e:
            logger.warning(f"Could not extract audio info: {e}")
            return AudioInfo(duration=0, samplerate=0, codec="unknown", channels=0)

    def validate_config(self) -> bool:
        """
        Validate converter configuration.

        Returns:
            True if config is valid

        Raises:
            ValueError: If config is invalid
        """
        if not self.api_key:
            logger.warning("No API key - running in mock mode")

        valid_models = [
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]
        if not any(m in self.model_name for m in ["gemini"]):
            logger.warning(f"Unusual model name: {self.model_name}")

        return True
