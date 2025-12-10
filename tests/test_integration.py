"""
Integration tests for MeetScribe pipeline.

Tests the full pipeline flow from input to output.
"""

import pytest
from pathlib import Path
from datetime import datetime
import json
import yaml

from meetscribe.core.config import PipelineConfig, load_config
from meetscribe.core.models import Transcript, Minutes, MeetingInfo, AudioInfo
from meetscribe.inputs.factory import get_input_provider
from meetscribe.converters.factory import get_converter
from meetscribe.llm.factory import get_llm_provider
from meetscribe.outputs.factory import get_output_renderer, get_multiple_renderers


@pytest.mark.integration
class TestPipelineIntegration:
    """Integration tests for the full pipeline."""

    def test_file_to_markdown_pipeline(self, tmp_path):
        """Test full pipeline: file input -> passthrough -> mock LLM -> markdown."""
        # Setup
        audio_file = tmp_path / "test_audio.mp3"
        audio_file.write_bytes(b"fake audio data" * 100)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        meeting_id = "2024-01-15T10-00_test_channel"

        # Step 1: Input
        input_provider = get_input_provider("file", {"audio_path": str(audio_file)})
        audio_path = input_provider.record(meeting_id)
        assert audio_path.exists()

        # Step 2: Convert (passthrough)
        converter = get_converter("passthrough", {})
        transcript = converter.transcribe(audio_path, meeting_id)
        assert isinstance(transcript, Transcript)
        assert transcript.meeting_info.meeting_id == meeting_id

        # Step 3: LLM (mock mode)
        llm = get_llm_provider("notebooklm", {})
        minutes = llm.generate_minutes(transcript)
        assert isinstance(minutes, Minutes)
        assert minutes.meeting_id == meeting_id

        # Step 4: Output
        renderer = get_output_renderer("markdown", {"output_dir": str(output_dir)})
        result = renderer.render(minutes, meeting_id)
        assert Path(result).exists()
        assert Path(result).suffix == ".md"

        # Verify content
        content = Path(result).read_text()
        assert "Meeting Minutes" in content

    def test_multiple_outputs_pipeline(self, tmp_path):
        """Test pipeline with multiple output formats."""
        # Setup
        audio_file = tmp_path / "test_audio.mp3"
        audio_file.write_bytes(b"fake audio data" * 100)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        meeting_id = "2024-01-15T10-00_multi_output"

        # Input -> Convert -> LLM
        input_provider = get_input_provider("file", {"audio_path": str(audio_file)})
        audio_path = input_provider.record(meeting_id)

        # Use whisper (mock mode) which produces text, unlike passthrough
        converter = get_converter("whisper", {})
        transcript = converter.transcribe(audio_path, meeting_id)

        llm = get_llm_provider("chatgpt", {})
        minutes = llm.generate_minutes(transcript)

        # Multiple outputs
        formats = [
            {"format": "markdown", "params": {"output_dir": str(output_dir)}},
            {"format": "json", "params": {"output_dir": str(output_dir)}},
        ]
        renderers = get_multiple_renderers(formats)

        results = []
        for renderer in renderers:
            result = renderer.render(minutes, meeting_id)
            results.append(result)
            assert Path(result).exists()

        # Verify both outputs created
        assert len(results) == 2
        assert any(".md" in r for r in results)
        assert any(".json" in r for r in results)

    def test_config_driven_pipeline(self, tmp_path):
        """Test pipeline driven by YAML configuration."""
        # Create test audio
        audio_file = tmp_path / "meeting.mp3"
        audio_file.write_bytes(b"fake audio" * 100)
        output_dir = tmp_path / "meetings"
        output_dir.mkdir()

        # Create config
        config_dict = {
            "input": {"provider": "file", "params": {"audio_path": str(audio_file)}},
            "convert": {"engine": "passthrough", "params": {}},
            "llm": {"engine": "notebooklm", "params": {}},
            "output": {"format": "json", "params": {"output_dir": str(output_dir)}},
            "working_dir": str(output_dir),
            "cleanup_audio": False,
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_dict, f)

        # Load config
        config = PipelineConfig.from_yaml(config_path)
        assert config.input.provider == "file"

        # Execute pipeline using config
        meeting_id = "2024-01-15T10-00_config_test"

        input_provider = get_input_provider(config.input.provider, config.input.params)
        audio_path = input_provider.record(meeting_id)

        converter = get_converter(config.convert.engine, config.convert.params)
        transcript = converter.transcribe(audio_path, meeting_id)

        llm = get_llm_provider(config.llm.engine, config.llm.params)
        minutes = llm.generate_minutes(transcript)

        outputs = config.get_outputs()
        for output_config in outputs:
            renderer = get_output_renderer(output_config.format, output_config.params)
            result = renderer.render(minutes, meeting_id)
            assert Path(result).exists()


@pytest.mark.integration
class TestConverterIntegration:
    """Integration tests for converters."""

    def test_whisper_mock_transcription(self, tmp_path):
        """Test Whisper converter in mock mode."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio" * 1000)

        converter = get_converter("whisper", {})
        transcript = converter.transcribe(audio_file, "2024-01-15T10-00_whisper_test")

        assert isinstance(transcript, Transcript)
        assert transcript.text is not None
        assert len(transcript.segments) > 0
        assert transcript.metadata.get("converter") in ["whisper-api", "whisper"]

    def test_gemini_mock_transcription(self, tmp_path):
        """Test Gemini converter in mock mode."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio" * 1000)

        converter = get_converter("gemini", {})
        transcript = converter.transcribe(audio_file, "2024-01-15T10-00_gemini_test")

        assert isinstance(transcript, Transcript)
        assert transcript.metadata.get("converter") == "gemini-audio"

    def test_deepgram_mock_transcription(self, tmp_path):
        """Test Deepgram converter in mock mode."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio" * 1000)

        converter = get_converter("deepgram", {})
        transcript = converter.transcribe(audio_file, "2024-01-15T10-00_deepgram_test")

        assert isinstance(transcript, Transcript)
        assert transcript.metadata.get("converter") == "deepgram"
        # Check diarization
        assert any(seg.speaker for seg in transcript.segments)


@pytest.mark.integration
class TestLLMIntegration:
    """Integration tests for LLM providers."""

    def test_all_llm_providers_produce_minutes(self, sample_transcript):
        """Test all LLM providers can produce minutes."""
        providers = ["notebooklm", "chatgpt", "claude", "gemini"]

        for provider_name in providers:
            llm = get_llm_provider(provider_name, {})
            minutes = llm.generate_minutes(sample_transcript)

            assert isinstance(minutes, Minutes), f"{provider_name} failed to produce Minutes"
            assert minutes.summary, f"{provider_name} produced empty summary"
            assert minutes.meeting_id == sample_transcript.meeting_info.meeting_id


@pytest.mark.integration
class TestOutputIntegration:
    """Integration tests for output renderers."""

    def test_all_renderers_produce_output(self, tmp_path, sample_minutes):
        """Test all output renderers can produce output."""
        formats = ["url", "markdown", "json", "pdf"]

        for format_name in formats:
            output_dir = tmp_path / format_name
            output_dir.mkdir()

            renderer = get_output_renderer(format_name, {"output_dir": str(output_dir)})
            result = renderer.render(sample_minutes, sample_minutes.meeting_id)

            assert result, f"{format_name} renderer returned empty result"
            assert Path(result).exists(), f"{format_name} output file not created"

    def test_webhook_renderer_mock_mode(self, tmp_path, sample_minutes):
        """Test webhook renderer in mock mode."""
        output_dir = tmp_path / "webhook"
        output_dir.mkdir()

        renderer = get_output_renderer("webhook", {"output_dir": str(output_dir)})
        result = renderer.render(sample_minutes, sample_minutes.meeting_id)

        assert Path(result).exists()
        with open(result, encoding="utf-8") as f:
            payload = json.load(f)
        assert "embeds" in payload


@pytest.mark.integration
class TestInputIntegration:
    """Integration tests for input providers."""

    def test_file_provider_handles_directory(self, tmp_path):
        """Test file provider can handle directory input."""
        # Create directory with multiple audio files
        (tmp_path / "audio1.mp3").write_bytes(b"audio1" * 100)
        (tmp_path / "audio2.mp3").write_bytes(b"audio2" * 100)

        provider = get_input_provider("file", {"audio_path": str(tmp_path), "pattern": "*.mp3"})
        result = provider.record("2024-01-15T10-00_dir_test")

        assert result.exists()
        assert result.suffix == ".mp3"

    def test_obs_provider_finds_recordings(self, tmp_path):
        """Test OBS provider finds recordings in directory."""
        # Create mock recordings
        (tmp_path / "recording1.mkv").write_bytes(b"video" * 100)
        (tmp_path / "recording2.mp4").write_bytes(b"video" * 100)

        provider = get_input_provider("obs", {"recording_dir": str(tmp_path)})
        recordings = provider.list_recordings()

        assert len(recordings) >= 1


@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling."""

    def test_missing_audio_file_raises_error(self, tmp_path):
        """Test that missing audio file raises appropriate error."""
        provider = get_input_provider("file", {"audio_path": str(tmp_path / "nonexistent.mp3")})

        with pytest.raises(FileNotFoundError):
            provider.record("2024-01-15T10-00_missing")

    def test_invalid_config_raises_error(self, tmp_path):
        """Test that invalid config raises validation error."""
        config_dict = {
            "input": {"provider": "invalid_provider"},
            "convert": {"engine": "whisper"},
            "llm": {"engine": "chatgpt"},
            "output": {"format": "markdown"},
        }

        from meetscribe.core.config import ConfigValidationError

        with pytest.raises(ConfigValidationError):
            PipelineConfig.from_dict(config_dict)

    def test_unsupported_audio_format(self, tmp_path):
        """Test that unsupported audio format raises error."""
        audio_file = tmp_path / "test.xyz"
        audio_file.write_bytes(b"data")

        provider = get_input_provider(
            "file", {"audio_path": str(audio_file), "validate_format": True}
        )

        with pytest.raises(ValueError, match="Unsupported audio format"):
            provider.record("2024-01-15T10-00_unsupported")
