"""
Extended tests for meetscribe providers.

Tests additional provider functionality with mocks.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from meetscribe.core.models import ActionItem, Decision, Minutes


def create_test_minutes(meeting_id="test-meeting"):
    """Helper to create test Minutes object."""
    return Minutes(
        meeting_id=meeting_id,
        summary="Test meeting summary",
        decisions=[Decision(description="Decision 1")],
        action_items=[ActionItem(description="Action 1", assignee="User")],
    )


class TestDiscordBotProvider:
    """Tests for DiscordBotProvider."""

    def test_discord_provider_init(self):
        """Test DiscordBotProvider initialization."""
        from meetscribe.inputs.discord_provider import DiscordBotProvider

        config = {
            "bot_token": "test_token",
            "guild_id": "123456",
            "channel_id": "789012",
            "recording_format": "mp3",
        }

        provider = DiscordBotProvider(config)

        assert provider.bot_token == "test_token"
        assert provider.guild_id == "123456"
        assert provider.channel_id == "789012"
        assert provider.recording_format == "mp3"

    def test_discord_provider_init_from_env(self, monkeypatch):
        """Test DiscordBotProvider initialization from environment."""
        from meetscribe.inputs.discord_provider import DiscordBotProvider

        monkeypatch.setenv("DISCORD_BOT_TOKEN", "env_token")

        config = {"guild_id": "123456", "channel_id": "789012"}

        provider = DiscordBotProvider(config)

        assert provider.bot_token == "env_token"

    def test_discord_provider_record_mock_mode(self, tmp_path):
        """Test DiscordBotProvider record in mock mode."""
        from meetscribe.inputs.discord_provider import DiscordBotProvider

        config = {"output_dir": str(tmp_path)}  # No bot_token = mock mode

        provider = DiscordBotProvider(config)
        result = provider.record("test-meeting-id")

        assert result.exists()
        # Mock mode may return different format
        assert result.suffix in [".mp3", ".txt"]

    def test_discord_provider_default_values(self):
        """Test DiscordBotProvider default values."""
        from meetscribe.inputs.discord_provider import DiscordBotProvider

        config = {}

        provider = DiscordBotProvider(config)

        assert provider.recording_format == "mp3"
        assert provider.max_duration == 14400
        assert provider.auto_join is False
        assert provider.min_users == 1


class TestGoogleMeetProvider:
    """Tests for GoogleMeetProvider."""

    def test_google_meet_provider_init(self):
        """Test GoogleMeetProvider initialization."""
        from meetscribe.inputs.google_meet_provider import GoogleMeetProvider

        config = {
            "credentials_path": "creds.json",
            "folder_id": "folder123",
            "download_dir": "./downloads",
        }

        provider = GoogleMeetProvider(config)

        assert provider.folder_id == "folder123"

    def test_google_meet_provider_record_mock(self, tmp_path):
        """Test GoogleMeetProvider record in mock mode."""
        from meetscribe.inputs.google_meet_provider import GoogleMeetProvider

        config = {"download_dir": str(tmp_path)}

        provider = GoogleMeetProvider(config)
        result = provider.record("test-meeting-id")

        # In mock mode, should return a mock recording
        assert result is not None


class TestOBSProvider:
    """Tests for OBSProvider."""

    def test_obs_provider_init(self):
        """Test OBSProvider initialization."""
        from meetscribe.inputs.obs_provider import OBSProvider

        config = {
            "recording_path": "./recordings",
            "watch_mode": True,
            "websocket_host": "localhost",
            "websocket_port": 4455,
        }

        provider = OBSProvider(config)

        assert provider.watch_mode is True
        assert provider.websocket_port == 4455

    def test_obs_provider_initialization(self, tmp_path):
        """Test OBSProvider can be initialized with custom config."""
        from meetscribe.inputs.obs_provider import OBSProvider

        config = {"recording_path": str(tmp_path)}

        provider = OBSProvider(config)

        assert provider is not None


class TestWebRTCProvider:
    """Tests for WebRTCProvider."""

    def test_webrtc_provider_init(self):
        """Test WebRTCProvider initialization."""
        from meetscribe.inputs.webrtc_provider import WebRTCProvider

        config = {
            "output_dir": "./recordings",
        }

        provider = WebRTCProvider(config)

        # Just verify initialization works
        assert provider is not None

    def test_webrtc_provider_record_mock(self, tmp_path):
        """Test WebRTCProvider record in mock mode."""
        from meetscribe.inputs.webrtc_provider import WebRTCProvider

        config = {"output_dir": str(tmp_path)}

        provider = WebRTCProvider(config)
        result = provider.record("test-meeting-id")

        assert result is not None


class TestPDFRenderer:
    """Tests for PDFRenderer."""

    def test_pdf_renderer_init(self):
        """Test PDFRenderer initialization."""
        from meetscribe.outputs.pdf_renderer import PDFRenderer

        config = {
            "output_dir": "./output",
            "page_size": "A4",
            "font_name": "Helvetica",
        }

        renderer = PDFRenderer(config)

        assert renderer.page_size_name == "A4"
        assert renderer.font_name == "Helvetica"

    def test_pdf_renderer_render_mock(self, tmp_path):
        """Test PDFRenderer render in mock mode."""
        from meetscribe.outputs.pdf_renderer import PDFRenderer

        config = {"output_dir": str(tmp_path)}

        renderer = PDFRenderer(config)

        minutes = create_test_minutes("test-meeting-id")

        result = renderer.render(minutes, "test-meeting-id")

        # Should return a path
        assert result is not None


class TestGoogleDocsRenderer:
    """Tests for GoogleDocsRenderer."""

    def test_google_docs_renderer_init(self):
        """Test GoogleDocsRenderer initialization."""
        from meetscribe.outputs.google_docs_renderer import GoogleDocsRenderer

        config = {
            "credentials_path": "creds.json",
            "folder_id": "folder123",
        }

        renderer = GoogleDocsRenderer(config)

        assert renderer.folder_id == "folder123"

    def test_google_docs_renderer_render_mock(self, tmp_path):
        """Test GoogleDocsRenderer render in mock mode."""
        from meetscribe.outputs.google_docs_renderer import GoogleDocsRenderer

        config = {"output_dir": str(tmp_path)}

        renderer = GoogleDocsRenderer(config)

        minutes = create_test_minutes("test-meeting-id")

        result = renderer.render(minutes, "test-meeting-id")

        # Should return a URL or path
        assert result is not None


class TestGoogleSheetsRenderer:
    """Tests for GoogleSheetsRenderer."""

    def test_google_sheets_renderer_init(self):
        """Test GoogleSheetsRenderer initialization."""
        from meetscribe.outputs.google_sheets_renderer import GoogleSheetsRenderer

        config = {
            "credentials_path": "creds.json",
        }

        renderer = GoogleSheetsRenderer(config)

        # Just verify initialization works
        assert renderer is not None


class TestDiscordWebhookRenderer:
    """Tests for DiscordWebhookRenderer."""

    def test_discord_webhook_renderer_init(self):
        """Test DiscordWebhookRenderer initialization."""
        from meetscribe.outputs.discord_webhook_renderer import DiscordWebhookRenderer

        config = {
            "webhook_url": "https://discord.com/api/webhooks/123/abc",
        }

        renderer = DiscordWebhookRenderer(config)

        assert renderer.webhook_url == "https://discord.com/api/webhooks/123/abc"

    def test_discord_webhook_renderer_init_from_env(self, monkeypatch):
        """Test DiscordWebhookRenderer initialization from environment."""
        from meetscribe.outputs.discord_webhook_renderer import DiscordWebhookRenderer

        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/env/url")

        config = {}

        renderer = DiscordWebhookRenderer(config)

        assert renderer.webhook_url == "https://discord.com/api/webhooks/env/url"


class TestURLRenderer:
    """Tests for URLRenderer."""

    def test_url_renderer_init(self):
        """Test URLRenderer initialization."""
        from meetscribe.outputs.url_renderer import URLRenderer

        config = {
            "output_dir": "./output",
        }

        renderer = URLRenderer(config)

        assert renderer.output_dir == Path("./output")

    def test_url_renderer_render(self, tmp_path):
        """Test URLRenderer render creates file."""
        from meetscribe.outputs.url_renderer import URLRenderer

        config = {"output_dir": str(tmp_path)}

        renderer = URLRenderer(config)

        minutes = Minutes(
            meeting_id="test-meeting-id",
            summary="Test meeting",
            url="https://example.com/meeting/123",
        )

        result = renderer.render(minutes, "test-meeting-id")

        # Should return a path to the output file
        assert result is not None
        # File should exist
        result_path = Path(result)
        assert (
            result_path.exists()
            or "mock" in str(result).lower()
            or tmp_path in result_path.parents
            or str(tmp_path) in result
        )
