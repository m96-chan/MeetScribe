"""
Unit tests for LLM layer providers.
"""

import pytest
from pathlib import Path
from datetime import datetime

from meetscribe.llm.factory import get_llm_provider
from meetscribe.llm.notebooklm_provider import NotebookLMProvider
from meetscribe.llm.chatgpt_provider import ChatGPTProvider
from meetscribe.llm.claude_provider import ClaudeProvider
from meetscribe.llm.gemini_provider import GeminiProvider
from meetscribe.core.models import Transcript, MeetingInfo, Minutes


@pytest.fixture
def sample_transcript():
    """Create sample transcript for testing."""
    return Transcript(
        meeting_info=MeetingInfo(
            meeting_id="2024-01-01T10-00_test_channel",
            source_type="test",
            start_time=datetime.now(),
            participants=["Alice", "Bob"]
        ),
        text=(
            "Alice: Let's discuss the project timeline. "
            "Bob: I think we should extend it by two weeks. "
            "Alice: Agreed. Let's also assign the documentation task. "
            "Bob: I can handle that by Friday. "
            "Alice: Great, that's decided then."
        ),
        segments=[],
        metadata={'test': True}
    )


class TestLLMFactory:
    """Tests for LLM factory."""

    def test_get_notebooklm_provider(self):
        """Test getting NotebookLM provider."""
        provider = get_llm_provider('notebooklm', {})
        assert isinstance(provider, NotebookLMProvider)

    def test_get_chatgpt_provider(self):
        """Test getting ChatGPT provider."""
        provider = get_llm_provider('chatgpt', {})
        assert isinstance(provider, ChatGPTProvider)

    def test_get_gpt_provider_alias(self):
        """Test getting GPT provider alias."""
        provider = get_llm_provider('gpt', {})
        assert isinstance(provider, ChatGPTProvider)

    def test_get_claude_provider(self):
        """Test getting Claude provider."""
        provider = get_llm_provider('claude', {})
        assert isinstance(provider, ClaudeProvider)

    def test_get_gemini_provider(self):
        """Test getting Gemini provider."""
        provider = get_llm_provider('gemini', {})
        assert isinstance(provider, GeminiProvider)

    def test_unsupported_provider(self):
        """Test error for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported LLM engine"):
            get_llm_provider('invalid', {})


class TestNotebookLMProvider:
    """Tests for NotebookLMProvider."""

    def test_init_default_config(self):
        """Test default initialization."""
        provider = NotebookLMProvider({})
        assert provider.notebook_title_prefix == 'Meeting'

    def test_init_mock_mode(self):
        """Test initialization in mock mode."""
        provider = NotebookLMProvider({})
        assert provider.client is not None  # Mock client

    def test_generate_minutes(self, sample_transcript):
        """Test minutes generation."""
        provider = NotebookLMProvider({})
        minutes = provider.generate_minutes(sample_transcript)

        assert isinstance(minutes, Minutes)
        assert minutes.meeting_id == sample_transcript.meeting_info.meeting_id
        assert minutes.url is not None
        assert minutes.summary is not None


class TestChatGPTProvider:
    """Tests for ChatGPTProvider."""

    def test_init_default_config(self):
        """Test default initialization."""
        provider = ChatGPTProvider({})
        assert provider.model == 'gpt-4-turbo'
        assert provider.temperature == 0.3

    def test_init_custom_config(self):
        """Test custom initialization."""
        provider = ChatGPTProvider({
            'model': 'gpt-4',
            'temperature': 0.5,
            'max_tokens': 2048
        })
        assert provider.model == 'gpt-4'
        assert provider.temperature == 0.5
        assert provider.max_tokens == 2048

    def test_mock_generation(self, sample_transcript):
        """Test mock minutes generation."""
        provider = ChatGPTProvider({})
        minutes = provider.generate_minutes(sample_transcript)

        assert isinstance(minutes, Minutes)
        assert minutes.summary is not None
        assert len(minutes.action_items) > 0
        assert minutes.metadata['llm_engine'] == 'chatgpt'

    def test_validate_config_invalid_temperature(self):
        """Test validation with invalid temperature."""
        provider = ChatGPTProvider({'temperature': 3.0})
        with pytest.raises(ValueError, match="temperature"):
            provider.validate_config()

    def test_extract_json_from_text(self):
        """Test JSON extraction from text."""
        provider = ChatGPTProvider({})
        text = 'Here is the result: {"summary": "test", "decisions": []}'
        result = provider._extract_json_from_text(text)

        assert 'summary' in result
        assert result['summary'] == 'test'


class TestClaudeProvider:
    """Tests for ClaudeProvider."""

    def test_init_default_config(self):
        """Test default initialization."""
        provider = ClaudeProvider({})
        assert 'claude' in provider.model
        assert provider.temperature == 0.3

    def test_mock_generation(self, sample_transcript):
        """Test mock minutes generation."""
        provider = ClaudeProvider({})
        minutes = provider.generate_minutes(sample_transcript)

        assert isinstance(minutes, Minutes)
        assert minutes.summary is not None
        assert minutes.metadata['llm_engine'] == 'claude'

    def test_validate_config_invalid_temperature(self):
        """Test validation with invalid temperature."""
        provider = ClaudeProvider({'temperature': 1.5})
        with pytest.raises(ValueError, match="temperature"):
            provider.validate_config()


class TestGeminiProvider:
    """Tests for GeminiProvider."""

    def test_init_default_config(self):
        """Test default initialization."""
        provider = GeminiProvider({})
        assert 'gemini' in provider.model
        assert provider.process_audio_directly is False

    def test_init_audio_processing(self):
        """Test initialization with audio processing."""
        provider = GeminiProvider({'process_audio_directly': True})
        assert provider.process_audio_directly is True

    def test_mock_generation(self, sample_transcript):
        """Test mock minutes generation."""
        provider = GeminiProvider({})
        minutes = provider.generate_minutes(sample_transcript)

        assert isinstance(minutes, Minutes)
        assert minutes.summary is not None
        assert minutes.metadata['llm_engine'] == 'gemini'

    def test_get_mime_type(self):
        """Test MIME type detection."""
        provider = GeminiProvider({})

        assert provider._get_mime_type(Path("test.mp3")) == "audio/mpeg"
        assert provider._get_mime_type(Path("test.wav")) == "audio/wav"
        assert provider._get_mime_type(Path("test.flac")) == "audio/flac"
