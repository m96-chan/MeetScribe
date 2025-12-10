"""
Deepgram CONVERT provider for MeetScribe.

Uses Deepgram's API for advanced speech-to-text transcription.
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


class DeepgramConverter(ConvertProvider):
    """
    Deepgram converter for advanced transcription.

    Supports speaker diarization, punctuation, and real-time streaming.
    """

    # Supported audio formats
    SUPPORTED_FORMATS = [
        ".mp3",
        ".mp4",
        ".wav",
        ".flac",
        ".ogg",
        ".webm",
        ".m4a",
        ".aac",
        ".wma",
        ".opus",
    ]

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Deepgram converter.

        Config params:
            api_key: Deepgram API key (or from DEEPGRAM_API_KEY env)
            model: Model to use (nova-2, nova, enhanced, base)
            language: Language code (default: auto-detect)
            punctuate: Add punctuation (default: True)
            diarize: Enable speaker diarization (default: True)
            smart_format: Smart formatting (default: True)
            utterances: Group by utterances (default: False)
            paragraphs: Group by paragraphs (default: False)
            detect_language: Auto-detect language (default: True)
            filler_words: Include filler words (default: False)
            profanity_filter: Filter profanity (default: False)
        """
        super().__init__(config)

        # API credentials
        self.api_key = config.get("api_key") or os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            logger.warning("No Deepgram API key provided - running in mock mode")

        # Model settings
        self.model = config.get("model", "nova-2")
        self.language = config.get("language")
        self.punctuate = config.get("punctuate", True)
        self.diarize = config.get("diarize", True)
        self.smart_format = config.get("smart_format", True)
        self.utterances = config.get("utterances", False)
        self.paragraphs = config.get("paragraphs", False)
        self.detect_language = config.get("detect_language", True)
        self.filler_words = config.get("filler_words", False)
        self.profanity_filter = config.get("profanity_filter", False)

        # Initialize client
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize Deepgram client."""
        if not self.api_key:
            logger.info("Running Deepgram converter in mock mode")
            return

        try:
            from deepgram import DeepgramClient

            self.client = DeepgramClient(self.api_key)
            logger.info("Deepgram client initialized successfully")
        except ImportError:
            logger.warning(
                "deepgram-sdk not installed. Run: pip install deepgram-sdk\n"
                "Running in mock mode."
            )
        except Exception as e:
            logger.error(f"Failed to initialize Deepgram client: {e}")
            logger.warning("Running in mock mode")

    def transcribe(self, audio_path: Path, meeting_id: str) -> Transcript:
        """
        Transcribe audio using Deepgram API.

        Args:
            audio_path: Path to audio file
            meeting_id: Meeting identifier

        Returns:
            Transcript object with text and segments
        """
        logger.info(f"Transcribing {audio_path} using Deepgram")

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
                "converter": "deepgram",
                "model": self.model,
                "language": result.get("language", self.language or "auto"),
                "duration": result.get("duration", 0),
                "channels": result.get("channels", 1),
                "confidence": result.get("confidence", 0),
            },
        )

        transcript.add_processing_step(
            "deepgram_transcribe",
            {
                "model": self.model,
                "language": result.get("language"),
                "duration": result.get("duration"),
                "segments_count": len(segments),
                "diarize": self.diarize,
            },
        )

        logger.info(
            f"Transcription complete: {len(segments)} segments, "
            f"{len(transcript.text)} characters"
        )
        return transcript

    def _validate_audio_file(self, audio_path: Path):
        """Validate audio file."""
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        suffix = audio_path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported audio format: {suffix}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

    def _transcribe_with_api(self, audio_path: Path) -> Dict[str, Any]:
        """Perform actual API transcription."""
        from deepgram import PrerecordedOptions, FileSource

        logger.info(f"Calling Deepgram API for {audio_path.name}")

        # Read audio file
        with open(audio_path, "rb") as f:
            buffer_data = f.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        # Build options
        options = PrerecordedOptions(
            model=self.model,
            punctuate=self.punctuate,
            diarize=self.diarize,
            smart_format=self.smart_format,
            utterances=self.utterances,
            paragraphs=self.paragraphs,
            detect_language=self.detect_language,
            filler_words=self.filler_words,
            profanity_filter=self.profanity_filter,
        )

        if self.language:
            options.language = self.language

        # Call API
        response = self.client.listen.prerecorded.v("1").transcribe_file(payload, options)

        # Parse response
        return self._parse_response(response)

    def _parse_response(self, response) -> Dict[str, Any]:
        """Parse Deepgram API response."""
        result = response.to_dict()

        # Extract results
        channels = result.get("results", {}).get("channels", [])
        if not channels:
            return {"text": "", "segments": []}

        channel = channels[0]
        alternatives = channel.get("alternatives", [])
        if not alternatives:
            return {"text": "", "segments": []}

        alternative = alternatives[0]

        # Build segments from words
        segments = []
        words = alternative.get("words", [])

        if self.diarize:
            # Group words by speaker
            current_speaker = None
            current_segment = None

            for word in words:
                speaker = word.get("speaker", 0)

                if speaker != current_speaker:
                    if current_segment:
                        segments.append(current_segment)

                    current_speaker = speaker
                    current_segment = {
                        "start": word.get("start", 0),
                        "end": word.get("end", 0),
                        "text": word.get("word", ""),
                        "speaker": f"Speaker {speaker}",
                        "confidence": word.get("confidence", 0),
                    }
                else:
                    current_segment["end"] = word.get("end", 0)
                    current_segment["text"] += " " + word.get("word", "")

            if current_segment:
                segments.append(current_segment)
        else:
            # Use paragraphs or utterances if available
            paragraphs_data = alternative.get("paragraphs", {})
            if paragraphs_data:
                for para in paragraphs_data.get("paragraphs", []):
                    for sentence in para.get("sentences", []):
                        segments.append(
                            {
                                "start": sentence.get("start", 0),
                                "end": sentence.get("end", 0),
                                "text": sentence.get("text", ""),
                                "speaker": f"Speaker {para.get('speaker', 0)}",
                            }
                        )
            else:
                # Fall back to creating segments from words
                segment_duration = 30  # seconds
                current_segment = None

                for word in words:
                    if (
                        not current_segment
                        or word.get("start", 0) - current_segment["start"] > segment_duration
                    ):
                        if current_segment:
                            segments.append(current_segment)
                        current_segment = {
                            "start": word.get("start", 0),
                            "end": word.get("end", 0),
                            "text": word.get("word", ""),
                        }
                    else:
                        current_segment["end"] = word.get("end", 0)
                        current_segment["text"] += " " + word.get("word", "")

                if current_segment:
                    segments.append(current_segment)

        # Get metadata
        metadata = result.get("metadata", {})

        return {
            "text": alternative.get("transcript", ""),
            "segments": segments,
            "language": metadata.get("detected_language") or self.language,
            "duration": metadata.get("duration", 0),
            "channels": metadata.get("channels", 1),
            "confidence": alternative.get("confidence", 0),
        }

    def _mock_transcription(self, audio_path: Path) -> Dict[str, Any]:
        """Return mock transcription for testing."""
        logger.info(f"[MOCK] Transcribing {audio_path.name}")

        file_size = audio_path.stat().st_size
        estimated_duration = file_size / (1024 * 1024) * 60

        return {
            "text": (
                "This is a mock transcription from Deepgram. "
                "The meeting covered several important topics. "
                "Speaker 0 discussed the project timeline. "
                "Speaker 1 provided updates on the technical implementation. "
                "Action items were assigned to the team."
            ),
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "This is a mock transcription from Deepgram.",
                    "speaker": "Speaker 0",
                    "confidence": 0.95,
                },
                {
                    "start": 5.0,
                    "end": 10.0,
                    "text": "The meeting covered several important topics.",
                    "speaker": "Speaker 0",
                    "confidence": 0.93,
                },
                {
                    "start": 10.0,
                    "end": 15.0,
                    "text": "Speaker 0 discussed the project timeline.",
                    "speaker": "Speaker 1",
                    "confidence": 0.91,
                },
                {
                    "start": 15.0,
                    "end": 20.0,
                    "text": "Action items were assigned to the team.",
                    "speaker": "Speaker 1",
                    "confidence": 0.94,
                },
            ],
            "language": "en",
            "duration": estimated_duration,
            "channels": 1,
            "confidence": 0.93,
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
                    confidence=seg.get("confidence"),
                    language=result.get("language"),
                )
            )
        return segments

    def _get_audio_info(self, audio_path: Path, result: Dict[str, Any]) -> AudioInfo:
        """Extract audio information."""
        return AudioInfo(
            duration=result.get("duration", 0),
            samplerate=16000,
            codec=audio_path.suffix.lower().replace(".", ""),
            channels=result.get("channels", 1),
        )

    def validate_config(self) -> bool:
        """Validate converter configuration."""
        if not self.api_key:
            logger.warning("No API key - running in mock mode")

        valid_models = [
            "nova-2",
            "nova",
            "enhanced",
            "base",
            "whisper-large",
            "whisper-medium",
            "whisper-small",
        ]
        if self.model not in valid_models:
            logger.warning(f"Unusual model: {self.model}. Valid models: {valid_models}")

        return True
