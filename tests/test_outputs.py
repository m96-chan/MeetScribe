"""
Unit tests for OUTPUT layer renderers.
"""

import pytest
from pathlib import Path
from datetime import datetime
import json

from meetscribe.outputs.factory import get_output_renderer, get_multiple_renderers
from meetscribe.outputs.url_renderer import URLRenderer
from meetscribe.outputs.markdown_renderer import MarkdownRenderer
from meetscribe.outputs.json_renderer import JSONRenderer
from meetscribe.outputs.pdf_renderer import PDFRenderer
from meetscribe.outputs.google_docs_renderer import GoogleDocsRenderer
from meetscribe.outputs.google_sheets_renderer import GoogleSheetsRenderer
from meetscribe.outputs.discord_webhook_renderer import DiscordWebhookRenderer
from meetscribe.core.models import Minutes, Decision, ActionItem


@pytest.fixture
def sample_minutes():
    """Create sample minutes for testing."""
    return Minutes(
        meeting_id="2024-01-01T10-00_test_channel",
        summary="This is a test meeting summary with important information.",
        decisions=[
            Decision(
                description="Approved the project plan",
                responsible="Alice",
                deadline="2024-01-15"
            ),
            Decision(
                description="Allocated budget for Q1",
                responsible="Bob",
                deadline=None
            ),
        ],
        action_items=[
            ActionItem(
                description="Complete initial implementation",
                assignee="Charlie",
                deadline="2024-01-10",
                priority="high"
            ),
            ActionItem(
                description="Review documentation",
                assignee="David",
                deadline="2024-01-12",
                priority="medium"
            ),
        ],
        key_points=[
            "Discussed project timeline",
            "Reviewed budget constraints",
            "Assigned responsibilities",
        ],
        participants=["Alice", "Bob", "Charlie", "David"],
        url="https://notebooklm.google.com/notebook/test123",
        metadata={'llm_engine': 'test'}
    )


class TestOutputFactory:
    """Tests for output factory."""

    def test_get_url_renderer(self):
        """Test getting URL renderer."""
        renderer = get_output_renderer('url', {})
        assert isinstance(renderer, URLRenderer)

    def test_get_markdown_renderer(self):
        """Test getting markdown renderer."""
        renderer = get_output_renderer('markdown', {})
        assert isinstance(renderer, MarkdownRenderer)

    def test_get_md_renderer(self):
        """Test getting md renderer alias."""
        renderer = get_output_renderer('md', {})
        assert isinstance(renderer, MarkdownRenderer)

    def test_get_json_renderer(self):
        """Test getting JSON renderer."""
        renderer = get_output_renderer('json', {})
        assert isinstance(renderer, JSONRenderer)

    def test_get_pdf_renderer(self):
        """Test getting PDF renderer."""
        renderer = get_output_renderer('pdf', {})
        assert isinstance(renderer, PDFRenderer)

    def test_get_docs_renderer(self):
        """Test getting Google Docs renderer."""
        renderer = get_output_renderer('docs', {})
        assert isinstance(renderer, GoogleDocsRenderer)

    def test_get_sheets_renderer(self):
        """Test getting Google Sheets renderer."""
        renderer = get_output_renderer('sheets', {})
        assert isinstance(renderer, GoogleSheetsRenderer)

    def test_get_webhook_renderer(self):
        """Test getting webhook renderer."""
        renderer = get_output_renderer('webhook', {})
        assert isinstance(renderer, DiscordWebhookRenderer)

    def test_unsupported_format(self):
        """Test error for unsupported format."""
        with pytest.raises(ValueError, match="Unsupported output format"):
            get_output_renderer('invalid', {})

    def test_get_multiple_renderers(self):
        """Test getting multiple renderers."""
        formats = [
            {'format': 'markdown'},
            {'format': 'json'},
        ]
        renderers = get_multiple_renderers(formats)
        assert len(renderers) == 2
        assert isinstance(renderers[0], MarkdownRenderer)
        assert isinstance(renderers[1], JSONRenderer)


class TestURLRenderer:
    """Tests for URLRenderer."""

    def test_init_default_config(self, tmp_path):
        """Test default initialization."""
        renderer = URLRenderer({'output_dir': str(tmp_path)})
        assert renderer.save_metadata is True

    def test_render_with_url(self, tmp_path, sample_minutes):
        """Test rendering with URL."""
        renderer = URLRenderer({
            'output_dir': str(tmp_path),
            'save_metadata': True
        })
        result = renderer.render(sample_minutes, sample_minutes.meeting_id)

        assert Path(result).exists()
        with open(result) as f:
            data = json.load(f)
        assert data['notebooklm_url'] == sample_minutes.url


class TestMarkdownRenderer:
    """Tests for MarkdownRenderer."""

    def test_render_creates_file(self, tmp_path, sample_minutes):
        """Test rendering creates markdown file."""
        renderer = MarkdownRenderer({'output_dir': str(tmp_path)})
        result = renderer.render(sample_minutes, sample_minutes.meeting_id)

        assert Path(result).exists()
        content = Path(result).read_text()
        assert "# Meeting Minutes" in content
        assert sample_minutes.summary in content

    def test_render_includes_action_items(self, tmp_path, sample_minutes):
        """Test action items are included."""
        renderer = MarkdownRenderer({'output_dir': str(tmp_path)})
        result = renderer.render(sample_minutes, sample_minutes.meeting_id)

        content = Path(result).read_text()
        assert "Action Items" in content
        assert "Complete initial implementation" in content

    def test_render_includes_decisions(self, tmp_path, sample_minutes):
        """Test decisions are included."""
        renderer = MarkdownRenderer({'output_dir': str(tmp_path)})
        result = renderer.render(sample_minutes, sample_minutes.meeting_id)

        content = Path(result).read_text()
        assert "Decisions" in content
        assert "Approved the project plan" in content

    def test_render_with_toc(self, tmp_path, sample_minutes):
        """Test table of contents is generated."""
        renderer = MarkdownRenderer({
            'output_dir': str(tmp_path),
            'include_toc': True
        })
        result = renderer.render(sample_minutes, sample_minutes.meeting_id)

        content = Path(result).read_text()
        assert "Table of Contents" in content


class TestJSONRenderer:
    """Tests for JSONRenderer."""

    def test_render_creates_valid_json(self, tmp_path, sample_minutes):
        """Test rendering creates valid JSON."""
        renderer = JSONRenderer({'output_dir': str(tmp_path)})
        result = renderer.render(sample_minutes, sample_minutes.meeting_id)

        with open(result) as f:
            data = json.load(f)

        assert data['meeting_id'] == sample_minutes.meeting_id
        assert data['summary'] == sample_minutes.summary
        assert len(data['action_items']) == 2
        assert len(data['decisions']) == 2

    def test_render_includes_statistics(self, tmp_path, sample_minutes):
        """Test statistics are included."""
        renderer = JSONRenderer({'output_dir': str(tmp_path)})
        result = renderer.render(sample_minutes, sample_minutes.meeting_id)

        with open(result) as f:
            data = json.load(f)

        assert 'statistics' in data
        assert data['statistics']['total_action_items'] == 2
        assert data['statistics']['total_decisions'] == 2


class TestPDFRenderer:
    """Tests for PDFRenderer."""

    def test_init_default_config(self):
        """Test default initialization."""
        renderer = PDFRenderer({})
        assert renderer.page_size_name == 'A4'
        assert renderer.body_font_size == 11

    def test_render_creates_file(self, tmp_path, sample_minutes):
        """Test rendering creates file."""
        renderer = PDFRenderer({'output_dir': str(tmp_path)})
        result = renderer.render(sample_minutes, sample_minutes.meeting_id)

        assert Path(result).exists()

    def test_validate_invalid_page_size(self):
        """Test validation with invalid page size."""
        renderer = PDFRenderer({'page_size': 'INVALID'})
        with pytest.raises(ValueError, match="page_size"):
            renderer.validate_config()


class TestDiscordWebhookRenderer:
    """Tests for DiscordWebhookRenderer."""

    def test_init_default_config(self):
        """Test default initialization."""
        renderer = DiscordWebhookRenderer({})
        assert renderer.username == 'MeetScribe'
        assert renderer.include_action_items is True

    def test_build_payload(self, sample_minutes):
        """Test payload building."""
        renderer = DiscordWebhookRenderer({})
        payload = renderer._build_payload(sample_minutes, sample_minutes.meeting_id)

        assert 'embeds' in payload
        assert payload['username'] == 'MeetScribe'
        assert len(payload['embeds']) >= 1

    def test_truncate_text(self):
        """Test text truncation."""
        renderer = DiscordWebhookRenderer({})
        long_text = "x" * 5000
        truncated = renderer._truncate(long_text, 100)

        assert len(truncated) == 100
        assert truncated.endswith("...")

    def test_mock_output_saves_payload(self, tmp_path, sample_minutes):
        """Test mock mode saves payload."""
        renderer = DiscordWebhookRenderer({'output_dir': str(tmp_path)})
        result = renderer.render(sample_minutes, sample_minutes.meeting_id)

        assert Path(result).exists()
        with open(result, encoding='utf-8') as f:
            payload = json.load(f)
        assert 'embeds' in payload
