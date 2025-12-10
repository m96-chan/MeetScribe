"""
Tests for meetscribe.init_templates module.

Tests configuration template generation for different providers.
"""

import pytest


class TestGetInitTemplate:
    """Tests for get_init_template function."""

    def test_get_discord_template(self):
        """Test getting Discord configuration template."""
        from meetscribe.init_templates import get_init_template

        template = get_init_template("discord")

        assert "discord" in template.lower()
        assert "bot_token" in template
        assert "guild_id" in template
        assert "channel_id" in template
        assert "input:" in template
        assert "convert:" in template
        assert "llm:" in template
        assert "output:" in template

    def test_get_zoom_template(self):
        """Test getting Zoom configuration template."""
        from meetscribe.init_templates import get_init_template

        template = get_init_template("zoom")

        assert "zoom" in template.lower()
        assert "api_key" in template
        assert "api_secret" in template
        assert "meeting_id" in template.lower()

    def test_get_meet_template(self):
        """Test getting Google Meet configuration template."""
        from meetscribe.init_templates import get_init_template

        template = get_init_template("meet")

        assert "meet" in template.lower()
        assert "credentials_path" in template
        assert "drive_folder_id" in template
        assert "gemini" in template.lower()

    def test_get_proctap_template(self):
        """Test getting ProcTap configuration template."""
        from meetscribe.init_templates import get_init_template

        template = get_init_template("proctap")

        assert "proctap" in template.lower()
        assert "process_name" in template
        assert "audio_device" in template
        assert "faster-whisper" in template
        assert "claude" in template.lower()

    def test_get_obs_template(self):
        """Test getting OBS configuration template."""
        from meetscribe.init_templates import get_init_template

        template = get_init_template("obs")

        assert "obs" in template.lower()
        assert "recording_path" in template
        assert "watch_folder" in template

    def test_get_unknown_template(self):
        """Test getting template for unknown provider returns default."""
        from meetscribe.init_templates import get_init_template

        template = get_init_template("unknown")

        # Should return default template
        assert "input:" in template
        assert "convert:" in template
        assert "llm:" in template
        assert "output:" in template


class TestTemplateContent:
    """Tests for template content validation."""

    def test_discord_template_has_required_sections(self):
        """Test Discord template has all required sections."""
        from meetscribe.init_templates import DISCORD_TEMPLATE

        required_sections = [
            "input:",
            "provider: discord",
            "convert:",
            "engine:",
            "llm:",
            "output:",
            "format:",
            "working_dir:",
        ]

        for section in required_sections:
            assert section in DISCORD_TEMPLATE, f"Missing section: {section}"

    def test_zoom_template_has_required_sections(self):
        """Test Zoom template has all required sections."""
        from meetscribe.init_templates import ZOOM_TEMPLATE

        required_sections = ["input:", "provider: zoom", "convert:", "llm:", "output:"]

        for section in required_sections:
            assert section in ZOOM_TEMPLATE, f"Missing section: {section}"

    def test_meet_template_has_required_sections(self):
        """Test Google Meet template has all required sections."""
        from meetscribe.init_templates import MEET_TEMPLATE

        required_sections = ["input:", "provider: meet", "convert:", "llm:", "output:"]

        for section in required_sections:
            assert section in MEET_TEMPLATE, f"Missing section: {section}"

    def test_proctap_template_has_required_sections(self):
        """Test ProcTap template has all required sections."""
        from meetscribe.init_templates import PROCTAP_TEMPLATE

        required_sections = ["input:", "provider: proctap", "convert:", "llm:", "output:"]

        for section in required_sections:
            assert section in PROCTAP_TEMPLATE, f"Missing section: {section}"

    def test_obs_template_has_required_sections(self):
        """Test OBS template has all required sections."""
        from meetscribe.init_templates import OBS_TEMPLATE

        required_sections = ["input:", "provider: obs", "convert:", "llm:", "output:"]

        for section in required_sections:
            assert section in OBS_TEMPLATE, f"Missing section: {section}"

    def test_default_template_has_required_sections(self):
        """Test default template has all required sections."""
        from meetscribe.init_templates import DEFAULT_TEMPLATE

        required_sections = ["input:", "convert:", "llm:", "output:", "working_dir:"]

        for section in required_sections:
            assert section in DEFAULT_TEMPLATE, f"Missing section: {section}"


class TestTemplateValidity:
    """Tests for template YAML validity."""

    def test_discord_template_is_valid_yaml(self):
        """Test Discord template is valid YAML."""
        import yaml

        from meetscribe.init_templates import DISCORD_TEMPLATE

        # Should not raise
        data = yaml.safe_load(DISCORD_TEMPLATE)
        assert isinstance(data, dict)
        assert "input" in data
        assert "convert" in data
        assert "llm" in data
        assert "output" in data

    def test_zoom_template_is_valid_yaml(self):
        """Test Zoom template is valid YAML."""
        import yaml

        from meetscribe.init_templates import ZOOM_TEMPLATE

        data = yaml.safe_load(ZOOM_TEMPLATE)
        assert isinstance(data, dict)

    def test_meet_template_is_valid_yaml(self):
        """Test Google Meet template is valid YAML."""
        import yaml

        from meetscribe.init_templates import MEET_TEMPLATE

        data = yaml.safe_load(MEET_TEMPLATE)
        assert isinstance(data, dict)

    def test_proctap_template_is_valid_yaml(self):
        """Test ProcTap template is valid YAML."""
        import yaml

        from meetscribe.init_templates import PROCTAP_TEMPLATE

        data = yaml.safe_load(PROCTAP_TEMPLATE)
        assert isinstance(data, dict)

    def test_obs_template_is_valid_yaml(self):
        """Test OBS template is valid YAML."""
        import yaml

        from meetscribe.init_templates import OBS_TEMPLATE

        data = yaml.safe_load(OBS_TEMPLATE)
        assert isinstance(data, dict)

    def test_default_template_is_valid_yaml(self):
        """Test default template is valid YAML."""
        import yaml

        from meetscribe.init_templates import DEFAULT_TEMPLATE

        data = yaml.safe_load(DEFAULT_TEMPLATE)
        assert isinstance(data, dict)
