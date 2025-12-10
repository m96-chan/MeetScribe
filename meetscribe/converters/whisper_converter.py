"""
Whisper API CONVERT provider for MeetScribe.

Uses OpenAI's Whisper API for cloud-based transcription.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os

from ..core.providers import ConvertProvider
from ..core.models import Transcript, AudioInfo, MeetingInfo, Segment
from ..core.meeting_id import parse_meeting_id


logger = logging.getLogger(__name__)


class WhisperAPIConverter(ConvertProvider):
    """
    Whisper API converter using OpenAI's transcription service.

    Supports both transcription and translation modes.
    """

    # Supported audio formats by Whisper API
    SUPPORTED_FORMATS = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
    # Maximum file size (25MB)
    MAX_FILE_SIZE = 25 * 1024 * 1024

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Whisper API converter.

        Config params:
            api_key: OpenAI API key (or from OPENAI_API_KEY env)
            model: Whisper model (default: "whisper-1")
            language: Source language code (optional, auto-detect if not set)
            response_format: Output format (json, text, srt, vtt, verbose_json)
            temperature: Sampling temperature (0-1, default: 0)
            prompt: Optional prompt to guide transcription
            timestamp_granularities: Granularity for timestamps (word, segment)
        """
        super().__init__(config)

        # API credentials
        self.api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("No OpenAI API key provided - running in mock mode")

        # Model settings
        self.model = config.get('model', 'whisper-1')
        self.language = config.get('language')  # None for auto-detect
        self.response_format = config.get('response_format', 'verbose_json')
        self.temperature = config.get('temperature', 0)
        self.prompt = config.get('prompt')
        self.timestamp_granularities = config.get('timestamp_granularities', ['segment'])

        # Initialize client
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize OpenAI client."""
        if not self.api_key:
            logger.info("Running Whisper converter in mock mode")
            return

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized successfully")
        except ImportError:
            logger.error("openai package not installed. Run: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    def transcribe(self, audio_path: Path, meeting_id: str) -> Transcript:
        """
        Transcribe audio using Whisper API.

        Args:
            audio_path: Path to audio file
            meeting_id: Meeting identifier

        Returns:
            Transcript object with text and segments
        """
        logger.info(f"Transcribing {audio_path} using Whisper API")

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
            channel_id=channel
        )

        # Perform transcription
        if self.client:
            result = self._transcribe_with_api(audio_path)
        else:
            result = self._mock_transcription(audio_path)

        # Extract segments
        segments = self._parse_segments(result)

        # Get audio info
        audio_info = self._get_audio_info(audio_path, result)

        # Build transcript
        transcript = Transcript(
            meeting_info=meeting_info,
            text=result.get('text', ''),
            audio_path=audio_path,
            segments=segments,
            audio_info=audio_info,
            metadata={
                'converter': 'whisper-api',
                'model': self.model,
                'language': result.get('language', self.language or 'auto'),
                'duration': result.get('duration', 0),
            }
        )

        transcript.add_processing_step(
            'whisper_api_transcribe',
            {
                'model': self.model,
                'language': result.get('language'),
                'duration': result.get('duration'),
                'segments_count': len(segments),
            }
        )

        logger.info(f"Transcription complete: {len(segments)} segments, "
                    f"{len(transcript.text)} characters")
        return transcript

    def _validate_audio_file(self, audio_path: Path):
        """Validate audio file for Whisper API."""
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
        logger.info(f"Calling Whisper API for {audio_path.name}")

        with open(audio_path, 'rb') as audio_file:
            # Build API parameters
            params = {
                'model': self.model,
                'file': audio_file,
                'response_format': self.response_format,
                'temperature': self.temperature,
            }

            if self.language:
                params['language'] = self.language
            if self.prompt:
                params['prompt'] = self.prompt
            if self.response_format == 'verbose_json':
                params['timestamp_granularities'] = self.timestamp_granularities

            # Call API
            response = self.client.audio.transcriptions.create(**params)

        # Parse response
        if self.response_format == 'verbose_json':
            return {
                'text': response.text,
                'language': response.language,
                'duration': response.duration,
                'segments': [
                    {
                        'start': seg.start,
                        'end': seg.end,
                        'text': seg.text,
                    }
                    for seg in (response.segments or [])
                ],
                'words': [
                    {
                        'start': word.start,
                        'end': word.end,
                        'word': word.word,
                    }
                    for word in (response.words or [])
                ] if hasattr(response, 'words') and response.words else []
            }
        else:
            # Simple text response
            return {
                'text': response if isinstance(response, str) else response.text,
                'segments': []
            }

    def _mock_transcription(self, audio_path: Path) -> Dict[str, Any]:
        """Return mock transcription for testing."""
        logger.info(f"[MOCK] Transcribing {audio_path.name}")

        # Estimate duration from file size
        file_size = audio_path.stat().st_size
        estimated_duration = file_size / (1024 * 1024) * 60  # ~1MB per minute

        return {
            'text': (
                "This is a mock transcription generated by the Whisper API converter "
                "in PoC mode. In production, this would contain the actual transcribed "
                "text from your audio file. The meeting discussed several important "
                "topics including project updates, timeline reviews, and action items. "
                "Key decisions were made regarding the implementation approach."
            ),
            'language': 'en',
            'duration': estimated_duration,
            'segments': [
                {
                    'start': 0.0,
                    'end': 5.0,
                    'text': 'This is a mock transcription generated by the Whisper API converter.',
                },
                {
                    'start': 5.0,
                    'end': 10.0,
                    'text': 'In production, this would contain the actual transcribed text.',
                },
                {
                    'start': 10.0,
                    'end': 15.0,
                    'text': 'The meeting discussed several important topics.',
                },
                {
                    'start': 15.0,
                    'end': 20.0,
                    'text': 'Key decisions were made regarding the implementation approach.',
                },
            ]
        }

    def _parse_segments(self, result: Dict[str, Any]) -> List[Segment]:
        """Parse segments from API response."""
        segments = []
        for seg in result.get('segments', []):
            segments.append(Segment(
                start=seg.get('start', 0),
                end=seg.get('end', 0),
                text=seg.get('text', '').strip(),
                confidence=seg.get('confidence'),
                language=result.get('language'),
            ))
        return segments

    def _get_audio_info(self, audio_path: Path, result: Dict[str, Any]) -> AudioInfo:
        """Extract audio information."""
        try:
            file_size = audio_path.stat().st_size
            duration = result.get('duration', file_size / (1024 * 1024) * 60)

            return AudioInfo(
                duration=duration,
                samplerate=16000,  # Whisper uses 16kHz
                codec=audio_path.suffix.lower().replace('.', ''),
                channels=1,  # Whisper converts to mono
            )
        except Exception as e:
            logger.warning(f"Could not extract audio info: {e}")
            return AudioInfo(
                duration=0,
                samplerate=0,
                codec='unknown',
                channels=0
            )

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

        if self.temperature < 0 or self.temperature > 1:
            raise ValueError("temperature must be between 0 and 1")

        valid_formats = ['json', 'text', 'srt', 'vtt', 'verbose_json']
        if self.response_format not in valid_formats:
            raise ValueError(f"response_format must be one of: {valid_formats}")

        return True
