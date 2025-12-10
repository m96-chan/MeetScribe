"""
Unit tests for CONVERT layer providers.
"""


import pytest

from meetscribe.converters.deepgram_converter import DeepgramConverter
from meetscribe.converters.factory import get_converter
from meetscribe.converters.faster_whisper_converter import FasterWhisperConverter
from meetscribe.converters.gemini_converter import GeminiAudioConverter
from meetscribe.converters.passthrough_converter import PassthroughConverter
from meetscribe.converters.whisper_converter import WhisperAPIConverter
from meetscribe.core.models import Transcript


class TestConverterFactory:
    """Tests for converter factory."""

    def test_get_passthrough_converter(self):
        """Test getting passthrough converter."""
        converter = get_converter("passthrough", {})
        assert isinstance(converter, PassthroughConverter)

    def test_get_whisper_converter(self):
        """Test getting whisper converter."""
        converter = get_converter("whisper", {})
        assert isinstance(converter, WhisperAPIConverter)

    def test_get_whisper_api_converter(self):
        """Test getting whisper-api converter."""
        converter = get_converter("whisper-api", {})
        assert isinstance(converter, WhisperAPIConverter)

    def test_get_faster_whisper_converter(self):
        """Test getting faster-whisper converter."""
        converter = get_converter("faster-whisper", {})
        assert isinstance(converter, FasterWhisperConverter)

    def test_get_gemini_converter(self):
        """Test getting gemini converter."""
        converter = get_converter("gemini", {})
        assert isinstance(converter, GeminiAudioConverter)

    def test_get_deepgram_converter(self):
        """Test getting deepgram converter."""
        converter = get_converter("deepgram", {})
        assert isinstance(converter, DeepgramConverter)

    def test_unsupported_converter(self):
        """Test error for unsupported converter."""
        with pytest.raises(ValueError, match="Unsupported converter"):
            get_converter("invalid", {})


class TestPassthroughConverter:
    """Tests for PassthroughConverter."""

    def test_init_default_config(self):
        """Test default initialization."""
        converter = PassthroughConverter({})
        assert converter.include_audio_info is True

    def test_init_custom_config(self):
        """Test custom initialization."""
        converter = PassthroughConverter({"include_audio_info": False})
        assert converter.include_audio_info is False

    def test_transcribe_creates_transcript(self, tmp_path):
        """Test transcription creates valid transcript."""
        # Create temp audio file
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio data" * 1000)

        converter = PassthroughConverter({})
        transcript = converter.transcribe(audio_file, "2024-01-01T10-00_test_channel")

        assert isinstance(transcript, Transcript)
        assert transcript.audio_path == audio_file
        assert transcript.text is None
        assert transcript.metadata["converter"] == "passthrough"

    def test_transcribe_missing_file(self, tmp_path):
        """Test transcription with missing file."""
        converter = PassthroughConverter({})
        audio_file = tmp_path / "nonexistent.mp3"

        # Should still create transcript (passthrough doesn't require file)
        transcript = converter.transcribe(audio_file, "2024-01-01T10-00_test_channel")
        assert transcript is not None

    def test_validate_config(self):
        """Test config validation."""
        converter = PassthroughConverter({})
        assert converter.validate_config() is True


class TestWhisperAPIConverter:
    """Tests for WhisperAPIConverter."""

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        converter = WhisperAPIConverter({})
        assert converter.client is None
        assert converter.model == "whisper-1"

    def test_init_with_config(self):
        """Test initialization with config."""
        converter = WhisperAPIConverter(
            {"model": "whisper-1", "language": "en", "temperature": 0.5}
        )
        assert converter.model == "whisper-1"
        assert converter.language == "en"
        assert converter.temperature == 0.5

    def test_validate_audio_file_unsupported_format(self, tmp_path):
        """Test validation rejects unsupported formats."""
        converter = WhisperAPIConverter({})
        audio_file = tmp_path / "test.xyz"
        audio_file.write_bytes(b"data")

        with pytest.raises(ValueError, match="Unsupported audio format"):
            converter._validate_audio_file(audio_file)

    def test_validate_audio_file_too_large(self, tmp_path):
        """Test validation rejects large files."""
        converter = WhisperAPIConverter({})
        audio_file = tmp_path / "test.mp3"
        # Create file larger than 25MB
        audio_file.write_bytes(b"x" * (26 * 1024 * 1024))

        with pytest.raises(ValueError, match="too large"):
            converter._validate_audio_file(audio_file)

    def test_mock_transcription(self, tmp_path):
        """Test mock transcription."""
        converter = WhisperAPIConverter({})
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio" * 1000)

        transcript = converter.transcribe(audio_file, "2024-01-01T10-00_test_channel")

        assert isinstance(transcript, Transcript)
        assert transcript.text is not None
        assert len(transcript.segments) > 0


class TestFasterWhisperConverter:
    """Tests for FasterWhisperConverter."""

    def test_init_default_config(self):
        """Test default initialization."""
        converter = FasterWhisperConverter({})
        assert converter.model_size == "base"
        assert converter.device == "auto"

    def test_init_custom_config(self):
        """Test custom initialization."""
        converter = FasterWhisperConverter(
            {"model_size": "large-v3", "device": "cuda", "beam_size": 3}
        )
        assert converter.model_size == "large-v3"
        assert converter.device == "cuda"
        assert converter.beam_size == 3

    def test_validate_config_invalid_model(self):
        """Test validation with invalid model."""
        converter = FasterWhisperConverter({"model_size": "invalid"})
        with pytest.raises(ValueError, match="model_size"):
            converter.validate_config()

    def test_mock_transcription(self, tmp_path):
        """Test mock transcription."""
        # Force mock mode by setting model to None
        converter = FasterWhisperConverter({})
        converter.model = None  # Force mock mode
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio" * 1000)

        transcript = converter.transcribe(audio_file, "2024-01-01T10-00_test_channel")

        assert isinstance(transcript, Transcript)
        assert transcript.text is not None


class TestGeminiAudioConverter:
    """Tests for GeminiAudioConverter."""

    def test_init_default_config(self):
        """Test default initialization."""
        converter = GeminiAudioConverter({})
        assert converter.model_name == "gemini-2.0-flash-exp"
        assert converter.include_timestamps is True

    def test_validate_audio_file_unsupported(self, tmp_path):
        """Test validation rejects unsupported formats."""
        converter = GeminiAudioConverter({})
        audio_file = tmp_path / "test.xyz"
        audio_file.write_bytes(b"data")

        with pytest.raises(ValueError, match="Unsupported audio format"):
            converter._validate_audio_file(audio_file)

    def test_mock_transcription(self, tmp_path):
        """Test mock transcription."""
        converter = GeminiAudioConverter({})
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio" * 1000)

        transcript = converter.transcribe(audio_file, "2024-01-01T10-00_test_channel")

        assert isinstance(transcript, Transcript)
        assert transcript.metadata["converter"] == "gemini-audio"


class TestDeepgramConverter:
    """Tests for DeepgramConverter."""

    def test_init_default_config(self):
        """Test default initialization."""
        converter = DeepgramConverter({})
        assert converter.model == "nova-2"
        assert converter.diarize is True
        assert converter.punctuate is True

    def test_init_custom_config(self):
        """Test custom initialization."""
        converter = DeepgramConverter({"model": "nova", "diarize": False, "language": "ja"})
        assert converter.model == "nova"
        assert converter.diarize is False
        assert converter.language == "ja"

    def test_mock_transcription(self, tmp_path):
        """Test mock transcription."""
        converter = DeepgramConverter({})
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio" * 1000)

        transcript = converter.transcribe(audio_file, "2024-01-01T10-00_test_channel")

        assert isinstance(transcript, Transcript)
        assert transcript.metadata["converter"] == "deepgram"
        # Check diarization produced speaker labels
        assert any(seg.speaker for seg in transcript.segments)
