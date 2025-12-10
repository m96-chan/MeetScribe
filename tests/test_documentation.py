"""
Tests for documentation files.

This module tests that documentation files exist and contain required sections.
"""

from pathlib import Path

import pytest


class TestUserGuideJapanese:
    """Tests for Japanese user guide."""

    @pytest.fixture
    def user_guide_ja_path(self):
        """Path to Japanese user guide."""
        return Path(__file__).parent.parent / "docs" / "user-guide-ja.md"

    def test_user_guide_ja_exists(self, user_guide_ja_path):
        """Test that Japanese user guide exists."""
        assert user_guide_ja_path.exists(), "docs/user-guide-ja.md should exist"

    def test_user_guide_ja_has_required_sections(self, user_guide_ja_path):
        """Test that Japanese user guide has all required sections."""
        content = user_guide_ja_path.read_text(encoding="utf-8")

        required_sections = [
            "クイックスタート",
            "インストール",
            "設定",
            "ユースケース",
            "トラブルシューティング",
            "FAQ",
        ]

        for section in required_sections:
            assert section in content, f"Section '{section}' should be in user-guide-ja.md"

    def test_user_guide_ja_has_use_cases(self, user_guide_ja_path):
        """Test that Japanese user guide has at least 4 use cases."""
        content = user_guide_ja_path.read_text(encoding="utf-8")

        use_cases = [
            "ローカル音声ファイル",
            "Discord",
            "Google Meet",
            "複数フォーマット",
        ]

        found_count = sum(1 for uc in use_cases if uc in content)
        assert found_count >= 4, f"Should have at least 4 use cases, found {found_count}"

    def test_user_guide_ja_has_troubleshooting_items(self, user_guide_ja_path):
        """Test that Japanese user guide has common troubleshooting items."""
        content = user_guide_ja_path.read_text(encoding="utf-8")

        troubleshooting_items = [
            "ffmpeg",
            "API",
            "エラー",
        ]

        for item in troubleshooting_items:
            assert item in content, f"Troubleshooting should mention '{item}'"

    def test_user_guide_ja_has_os_specific_instructions(self, user_guide_ja_path):
        """Test that Japanese user guide has OS-specific instructions."""
        content = user_guide_ja_path.read_text(encoding="utf-8")

        os_names = ["Windows", "macOS", "Linux"]

        for os_name in os_names:
            assert os_name in content, f"Should have instructions for {os_name}"


class TestUserGuideEnglish:
    """Tests for English user guide."""

    @pytest.fixture
    def user_guide_path(self):
        """Path to English user guide."""
        return Path(__file__).parent.parent / "docs" / "user-guide.md"

    def test_user_guide_exists(self, user_guide_path):
        """Test that English user guide exists."""
        assert user_guide_path.exists(), "docs/user-guide.md should exist"

    def test_user_guide_has_required_sections(self, user_guide_path):
        """Test that English user guide has all required sections."""
        content = user_guide_path.read_text(encoding="utf-8")

        required_sections = [
            "Quick Start",
            "Installation",
            "Configuration",
            "Use Case",
            "Troubleshooting",
            "FAQ",
        ]

        for section in required_sections:
            assert section in content, f"Section '{section}' should be in user-guide.md"

    def test_user_guide_has_use_cases(self, user_guide_path):
        """Test that English user guide has at least 4 use cases."""
        content = user_guide_path.read_text(encoding="utf-8")

        use_cases = [
            "Local Audio",
            "Discord",
            "Google Meet",
            "Multiple",
        ]

        found_count = sum(1 for uc in use_cases if uc in content)
        assert found_count >= 4, f"Should have at least 4 use cases, found {found_count}"

    def test_user_guide_has_glossary(self, user_guide_path):
        """Test that English user guide has a glossary section."""
        content = user_guide_path.read_text(encoding="utf-8")
        assert "Glossary" in content, "Should have a Glossary section"


class TestDocumentationSync:
    """Tests for documentation synchronization between languages."""

    @pytest.fixture
    def docs_path(self):
        """Path to docs directory."""
        return Path(__file__).parent.parent / "docs"

    def test_both_user_guides_exist(self, docs_path):
        """Test that both English and Japanese user guides exist."""
        assert (docs_path / "user-guide.md").exists()
        assert (docs_path / "user-guide-ja.md").exists()

    def test_user_guides_have_similar_structure(self, docs_path):
        """Test that both guides have similar section counts."""
        en_content = (docs_path / "user-guide.md").read_text(encoding="utf-8")
        ja_content = (docs_path / "user-guide-ja.md").read_text(encoding="utf-8")

        # Count H2 headers
        en_h2_count = en_content.count("\n## ")
        ja_h2_count = ja_content.count("\n## ")

        # Should have similar number of main sections (within 6)
        # Note: EN has more detailed subsections split into separate H2 headers
        assert (
            abs(en_h2_count - ja_h2_count) <= 6
        ), f"Section counts should be similar: EN={en_h2_count}, JA={ja_h2_count}"
