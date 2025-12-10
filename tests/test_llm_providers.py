"""
Tests for meetscribe LLM providers.

Tests LLM provider initialization and mock generation.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from meetscribe.core.models import MeetingInfo, Transcript


def create_test_transcript():
    """Helper to create a test Transcript object."""
    return Transcript(
        meeting_info=MeetingInfo(
            meeting_id="test-meeting-id",
            source_type="file",
            start_time=datetime.now(),
        ),
        text="This is a test meeting transcript.",
        segments=[],
    )


class TestChatGPTProvider:
    """Tests for ChatGPTProvider."""

    def test_chatgpt_provider_init(self):
        """Test ChatGPTProvider initialization."""
        from meetscribe.llm.chatgpt_provider import ChatGPTProvider

        config = {
            "api_key": "test_key",
            "model": "gpt-4",
        }

        provider = ChatGPTProvider(config)

        assert provider.model == "gpt-4"

    def test_chatgpt_provider_init_from_env(self, monkeypatch):
        """Test ChatGPTProvider initialization from environment."""
        from meetscribe.llm.chatgpt_provider import ChatGPTProvider

        monkeypatch.setenv("OPENAI_API_KEY", "env_key")

        config = {"model": "gpt-4"}

        provider = ChatGPTProvider(config)

        assert provider.api_key == "env_key"


class TestClaudeProvider:
    """Tests for ClaudeProvider."""

    def test_claude_provider_init(self):
        """Test ClaudeProvider initialization."""
        from meetscribe.llm.claude_provider import ClaudeProvider

        config = {
            "api_key": "test_key",
            "model": "claude-3-sonnet",
        }

        provider = ClaudeProvider(config)

        assert provider.model == "claude-3-sonnet"

    def test_claude_provider_init_from_env(self, monkeypatch):
        """Test ClaudeProvider initialization from environment."""
        from meetscribe.llm.claude_provider import ClaudeProvider

        monkeypatch.setenv("ANTHROPIC_API_KEY", "env_key")

        config = {"model": "claude-3-sonnet"}

        provider = ClaudeProvider(config)

        assert provider.api_key == "env_key"


class TestGeminiProvider:
    """Tests for GeminiProvider."""

    def test_gemini_provider_init(self):
        """Test GeminiProvider initialization."""
        from meetscribe.llm.gemini_provider import GeminiProvider

        config = {
            "api_key": "test_key",
            "model": "gemini-pro",
        }

        provider = GeminiProvider(config)

        assert provider.model == "gemini-pro"

    def test_gemini_provider_init_from_env(self, monkeypatch):
        """Test GeminiProvider initialization from environment."""
        from meetscribe.llm.gemini_provider import GeminiProvider

        monkeypatch.setenv("GEMINI_API_KEY", "env_key")

        config = {"model": "gemini-pro"}

        provider = GeminiProvider(config)

        assert provider.api_key == "env_key"


class TestNotebookLMProvider:
    """Tests for NotebookLMProvider."""

    def test_notebooklm_provider_init(self):
        """Test NotebookLMProvider initialization."""
        from meetscribe.llm.notebooklm_provider import NotebookLMProvider

        config = {
            "api_key": "test_key",
        }

        provider = NotebookLMProvider(config)

        assert provider.api_key == "test_key"

    def test_notebooklm_provider_default_values(self):
        """Test NotebookLMProvider default values."""
        from meetscribe.llm.notebooklm_provider import NotebookLMProvider

        config = {}

        provider = NotebookLMProvider(config)

        # Should have reasonable defaults
        assert hasattr(provider, "api_key")

    def test_notebooklm_provider_generate_minutes_mock(self):
        """Test NotebookLMProvider generate_minutes in mock mode."""
        from meetscribe.llm.notebooklm_provider import NotebookLMProvider

        config = {}

        provider = NotebookLMProvider(config)

        transcript = create_test_transcript()

        result = provider.generate_minutes(transcript)

        assert result is not None
        assert result.summary is not None


class TestLLMFactory:
    """Tests for LLM factory."""

    def test_get_chatgpt_provider(self):
        """Test getting ChatGPT provider from factory."""
        from meetscribe.llm.factory import get_llm_provider

        provider = get_llm_provider("chatgpt", {"api_key": "test"})

        assert provider is not None
        from meetscribe.llm.chatgpt_provider import ChatGPTProvider

        assert isinstance(provider, ChatGPTProvider)

    def test_get_claude_provider(self):
        """Test getting Claude provider from factory."""
        from meetscribe.llm.factory import get_llm_provider

        provider = get_llm_provider("claude", {"api_key": "test"})

        assert provider is not None
        from meetscribe.llm.claude_provider import ClaudeProvider

        assert isinstance(provider, ClaudeProvider)

    def test_get_gemini_provider(self):
        """Test getting Gemini provider from factory."""
        from meetscribe.llm.factory import get_llm_provider

        provider = get_llm_provider("gemini", {"api_key": "test"})

        assert provider is not None
        from meetscribe.llm.gemini_provider import GeminiProvider

        assert isinstance(provider, GeminiProvider)

    def test_get_notebooklm_provider(self):
        """Test getting NotebookLM provider from factory."""
        from meetscribe.llm.factory import get_llm_provider

        provider = get_llm_provider("notebooklm", {"api_key": "test"})

        assert provider is not None
        from meetscribe.llm.notebooklm_provider import NotebookLMProvider

        assert isinstance(provider, NotebookLMProvider)

    def test_get_unsupported_provider(self):
        """Test getting unsupported provider raises error."""
        from meetscribe.llm.factory import get_llm_provider

        with pytest.raises(ValueError):
            get_llm_provider("unsupported", {})
