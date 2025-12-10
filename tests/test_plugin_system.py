"""
Tests for meetscribe plugin system.

Tests plugin discovery, loading, validation, and registry.
"""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from meetscribe.core.models import Minutes, Transcript
from meetscribe.core.providers import (
    ConvertProvider,
    InputProvider,
    LLMProvider,
    OutputRenderer,
)


class TestPluginMetadata:
    """Tests for PluginMetadata dataclass."""

    def test_plugin_metadata_creation(self):
        """Test creating PluginMetadata with required fields."""
        from meetscribe.core.plugin import PluginMetadata

        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            provider_type="input",
            provider_class="TestProvider",
        )

        assert metadata.name == "test-plugin"
        assert metadata.version == "1.0.0"
        assert metadata.provider_type == "input"
        assert metadata.provider_class == "TestProvider"

    def test_plugin_metadata_with_optional_fields(self):
        """Test creating PluginMetadata with all fields."""
        from meetscribe.core.plugin import PluginMetadata

        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            provider_type="input",
            provider_class="TestProvider",
            description="A test plugin",
            author="Test Author",
            homepage="https://example.com",
            dependencies=["pyyaml>=6.0"],
        )

        assert metadata.description == "A test plugin"
        assert metadata.author == "Test Author"
        assert metadata.homepage == "https://example.com"
        assert metadata.dependencies == ["pyyaml>=6.0"]

    def test_plugin_metadata_default_optional_fields(self):
        """Test that optional fields have sensible defaults."""
        from meetscribe.core.plugin import PluginMetadata

        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            provider_type="input",
            provider_class="TestProvider",
        )

        assert metadata.description is None
        assert metadata.author is None
        assert metadata.homepage is None
        assert metadata.dependencies == []


class TestPluginRegistry:
    """Tests for PluginRegistry singleton."""

    def setup_method(self):
        """Reset singleton before each test."""
        from meetscribe.core.plugin import PluginRegistry

        PluginRegistry._instance = None

    def test_plugin_registry_is_singleton(self):
        """Test that PluginRegistry is a singleton."""
        from meetscribe.core.plugin import PluginRegistry

        registry1 = PluginRegistry()
        registry2 = PluginRegistry()

        assert registry1 is registry2

    def test_plugin_registry_starts_empty(self):
        """Test that registry starts with no plugins."""
        from meetscribe.core.plugin import PluginRegistry

        registry = PluginRegistry()

        assert len(registry.get_all_plugins()) == 0

    def test_register_input_plugin(self):
        """Test registering an input provider plugin."""
        from meetscribe.core.plugin import PluginMetadata, PluginRegistry

        registry = PluginRegistry()

        class MockInputProvider(InputProvider):
            def record(self, meeting_id: str) -> Path:
                return Path("mock.mp3")

        metadata = PluginMetadata(
            name="mock-input",
            version="1.0.0",
            provider_type="input",
            provider_class="MockInputProvider",
        )

        registry.register("mock-input", MockInputProvider, metadata)

        assert registry.has_plugin("mock-input")
        assert registry.get_plugin_class("mock-input") == MockInputProvider

    def test_register_converter_plugin(self):
        """Test registering a converter plugin."""
        from meetscribe.core.plugin import PluginMetadata, PluginRegistry

        registry = PluginRegistry()

        class MockConverter(ConvertProvider):
            def transcribe(self, audio_path: Path, meeting_id: str) -> Transcript:
                return Transcript(text="mock")

        metadata = PluginMetadata(
            name="mock-converter",
            version="1.0.0",
            provider_type="converter",
            provider_class="MockConverter",
        )

        registry.register("mock-converter", MockConverter, metadata)

        assert registry.has_plugin("mock-converter")

    def test_register_llm_plugin(self):
        """Test registering an LLM provider plugin."""
        from meetscribe.core.plugin import PluginMetadata, PluginRegistry

        registry = PluginRegistry()

        class MockLLM(LLMProvider):
            def generate_minutes(self, transcript: Transcript) -> Minutes:
                return Minutes(meeting_id="test", summary="mock")

        metadata = PluginMetadata(
            name="mock-llm",
            version="1.0.0",
            provider_type="llm",
            provider_class="MockLLM",
        )

        registry.register("mock-llm", MockLLM, metadata)

        assert registry.has_plugin("mock-llm")

    def test_register_output_plugin(self):
        """Test registering an output renderer plugin."""
        from meetscribe.core.plugin import PluginMetadata, PluginRegistry

        registry = PluginRegistry()

        class MockRenderer(OutputRenderer):
            def render(self, minutes: Minutes, meeting_id: str) -> str:
                return "mock output"

        metadata = PluginMetadata(
            name="mock-output",
            version="1.0.0",
            provider_type="output",
            provider_class="MockRenderer",
        )

        registry.register("mock-output", MockRenderer, metadata)

        assert registry.has_plugin("mock-output")

    def test_get_plugins_by_type(self):
        """Test filtering plugins by type."""
        from meetscribe.core.plugin import PluginMetadata, PluginRegistry

        registry = PluginRegistry()

        class MockInput1(InputProvider):
            def record(self, meeting_id: str) -> Path:
                return Path("mock1.mp3")

        class MockInput2(InputProvider):
            def record(self, meeting_id: str) -> Path:
                return Path("mock2.mp3")

        class MockLLM(LLMProvider):
            def generate_minutes(self, transcript: Transcript) -> Minutes:
                return Minutes(meeting_id="test", summary="mock")

        registry.register(
            "input1",
            MockInput1,
            PluginMetadata(
                name="input1", version="1.0.0", provider_type="input", provider_class="MockInput1"
            ),
        )
        registry.register(
            "input2",
            MockInput2,
            PluginMetadata(
                name="input2", version="1.0.0", provider_type="input", provider_class="MockInput2"
            ),
        )
        registry.register(
            "llm1",
            MockLLM,
            PluginMetadata(
                name="llm1", version="1.0.0", provider_type="llm", provider_class="MockLLM"
            ),
        )

        input_plugins = registry.get_plugins_by_type("input")
        llm_plugins = registry.get_plugins_by_type("llm")

        assert len(input_plugins) == 2
        assert len(llm_plugins) == 1

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        from meetscribe.core.plugin import PluginMetadata, PluginRegistry

        registry = PluginRegistry()

        class MockInput(InputProvider):
            def record(self, meeting_id: str) -> Path:
                return Path("mock.mp3")

        metadata = PluginMetadata(
            name="mock-input",
            version="1.0.0",
            provider_type="input",
            provider_class="MockInput",
        )

        registry.register("mock-input", MockInput, metadata)
        assert registry.has_plugin("mock-input")

        registry.unregister("mock-input")
        assert not registry.has_plugin("mock-input")

    def test_get_nonexistent_plugin(self):
        """Test getting a plugin that doesn't exist."""
        from meetscribe.core.plugin import PluginRegistry

        registry = PluginRegistry()

        assert registry.get_plugin_class("nonexistent") is None

    def test_get_plugin_metadata(self):
        """Test getting plugin metadata."""
        from meetscribe.core.plugin import PluginMetadata, PluginRegistry

        registry = PluginRegistry()

        class MockInput(InputProvider):
            def record(self, meeting_id: str) -> Path:
                return Path("mock.mp3")

        metadata = PluginMetadata(
            name="mock-input",
            version="1.0.0",
            provider_type="input",
            provider_class="MockInput",
            description="Test plugin",
        )

        registry.register("mock-input", MockInput, metadata)

        retrieved_metadata = registry.get_plugin_metadata("mock-input")
        assert retrieved_metadata is not None
        assert retrieved_metadata.name == "mock-input"
        assert retrieved_metadata.description == "Test plugin"


class TestPluginValidator:
    """Tests for plugin validation."""

    def test_validate_valid_input_plugin(self):
        """Test validating a valid input provider plugin."""
        from meetscribe.core.plugin import PluginValidator

        class ValidInput(InputProvider):
            def record(self, meeting_id: str) -> Path:
                return Path("mock.mp3")

        validator = PluginValidator()
        is_valid, errors = validator.validate_provider_class(ValidInput, "input")

        assert is_valid
        assert len(errors) == 0

    def test_validate_valid_converter_plugin(self):
        """Test validating a valid converter plugin."""
        from meetscribe.core.plugin import PluginValidator

        class ValidConverter(ConvertProvider):
            def transcribe(self, audio_path: Path, meeting_id: str) -> Transcript:
                return Transcript(text="test")

        validator = PluginValidator()
        is_valid, errors = validator.validate_provider_class(ValidConverter, "converter")

        assert is_valid
        assert len(errors) == 0

    def test_validate_valid_llm_plugin(self):
        """Test validating a valid LLM provider plugin."""
        from meetscribe.core.plugin import PluginValidator

        class ValidLLM(LLMProvider):
            def generate_minutes(self, transcript: Transcript) -> Minutes:
                return Minutes(meeting_id="test", summary="mock")

        validator = PluginValidator()
        is_valid, errors = validator.validate_provider_class(ValidLLM, "llm")

        assert is_valid
        assert len(errors) == 0

    def test_validate_valid_output_plugin(self):
        """Test validating a valid output renderer plugin."""
        from meetscribe.core.plugin import PluginValidator

        class ValidOutput(OutputRenderer):
            def render(self, minutes: Minutes, meeting_id: str) -> str:
                return "output"

        validator = PluginValidator()
        is_valid, errors = validator.validate_provider_class(ValidOutput, "output")

        assert is_valid
        assert len(errors) == 0

    def test_validate_invalid_base_class(self):
        """Test validating a plugin with wrong base class."""
        from meetscribe.core.plugin import PluginValidator

        class InvalidPlugin:
            pass

        validator = PluginValidator()
        is_valid, errors = validator.validate_provider_class(InvalidPlugin, "input")

        assert not is_valid
        assert len(errors) > 0
        assert "InputProvider" in errors[0]

    def test_validate_missing_abstract_method(self):
        """Test validating a plugin missing abstract method."""
        from meetscribe.core.plugin import PluginValidator

        # This class inherits but doesn't implement the abstract method
        class IncompleteInput(InputProvider):
            pass

        validator = PluginValidator()
        is_valid, errors = validator.validate_provider_class(IncompleteInput, "input")

        assert not is_valid
        assert len(errors) > 0

    def test_validate_unknown_provider_type(self):
        """Test validating with unknown provider type."""
        from meetscribe.core.plugin import PluginValidator

        class SomeClass:
            pass

        validator = PluginValidator()
        is_valid, errors = validator.validate_provider_class(SomeClass, "unknown")

        assert not is_valid
        assert "Unknown provider type" in errors[0]


class TestPluginDiscovery:
    """Tests for plugin discovery via entry points."""

    def setup_method(self):
        """Reset singleton before each test."""
        from meetscribe.core.plugin import PluginRegistry

        PluginRegistry._instance = None

    def test_discover_plugins_from_entry_points(self):
        """Test discovering plugins from entry points."""
        from meetscribe.core.plugin import PluginDiscovery

        discovery = PluginDiscovery()

        # Mock entry points
        mock_entry_point = MagicMock()
        mock_entry_point.name = "mock-plugin"
        mock_entry_point.value = "mock_package:MockProvider"

        class MockProvider(InputProvider):
            def record(self, meeting_id: str) -> Path:
                return Path("mock.mp3")

        mock_entry_point.load.return_value = MockProvider

        with patch(
            "meetscribe.core.plugin.entry_points",
            return_value={"meetscribe.plugins.input": [mock_entry_point]},
        ):
            plugins = discovery.discover_entry_points("input")

        assert len(plugins) == 1
        assert plugins[0][0] == "mock-plugin"

    def test_discover_plugins_handles_load_error(self):
        """Test that discovery handles load errors gracefully."""
        from meetscribe.core.plugin import PluginDiscovery

        discovery = PluginDiscovery()

        mock_entry_point = MagicMock()
        mock_entry_point.name = "broken-plugin"
        mock_entry_point.load.side_effect = ImportError("Module not found")

        with patch(
            "meetscribe.core.plugin.entry_points",
            return_value={"meetscribe.plugins.input": [mock_entry_point]},
        ):
            plugins = discovery.discover_entry_points("input")

        # Should return empty list, not raise
        assert len(plugins) == 0

    def test_discover_all_plugin_types(self):
        """Test discovering all plugin types."""
        from meetscribe.core.plugin import PluginDiscovery

        discovery = PluginDiscovery()

        with patch("meetscribe.core.plugin.entry_points", return_value={}):
            all_plugins = discovery.discover_all()

        assert "input" in all_plugins
        assert "converter" in all_plugins
        assert "llm" in all_plugins
        assert "output" in all_plugins


class TestPluginLoader:
    """Tests for loading and instantiating plugins."""

    def setup_method(self):
        """Reset singleton before each test."""
        from meetscribe.core.plugin import PluginRegistry

        PluginRegistry._instance = None

    def test_load_plugin_from_registry(self):
        """Test loading a registered plugin."""
        from meetscribe.core.plugin import PluginLoader, PluginMetadata, PluginRegistry

        registry = PluginRegistry()

        class MockInput(InputProvider):
            def __init__(self, config: Dict[str, Any]):
                super().__init__(config)
                self.custom_option = config.get("custom_option", False)

            def record(self, meeting_id: str) -> Path:
                return Path("mock.mp3")

        metadata = PluginMetadata(
            name="mock-input",
            version="1.0.0",
            provider_type="input",
            provider_class="MockInput",
        )

        registry.register("mock-input", MockInput, metadata)

        loader = PluginLoader(registry)
        config = {"custom_option": True}
        instance = loader.load("mock-input", config)

        assert instance is not None
        assert isinstance(instance, MockInput)
        assert instance.custom_option is True

    def test_load_nonexistent_plugin(self):
        """Test loading a plugin that doesn't exist."""
        from meetscribe.core.plugin import PluginLoader, PluginRegistry

        registry = PluginRegistry()
        loader = PluginLoader(registry)

        with pytest.raises(ValueError, match="Plugin not found"):
            loader.load("nonexistent", {})

    def test_load_plugin_with_validation(self):
        """Test that loader validates plugins before loading."""
        from meetscribe.core.plugin import PluginLoader, PluginMetadata, PluginRegistry

        registry = PluginRegistry()

        class ValidInput(InputProvider):
            def record(self, meeting_id: str) -> Path:
                return Path("mock.mp3")

        metadata = PluginMetadata(
            name="valid-input",
            version="1.0.0",
            provider_type="input",
            provider_class="ValidInput",
        )

        registry.register("valid-input", ValidInput, metadata)

        loader = PluginLoader(registry, validate=True)
        instance = loader.load("valid-input", {})

        assert instance is not None


class TestFactoryIntegration:
    """Tests for plugin integration with existing factories."""

    def setup_method(self):
        """Reset singleton before each test."""
        from meetscribe.core.plugin import PluginRegistry

        PluginRegistry._instance = None

    def test_get_input_provider_from_plugin(self):
        """Test getting an input provider that was registered as plugin."""
        from meetscribe.core.plugin import PluginMetadata, PluginRegistry
        from meetscribe.inputs.factory import get_input_provider

        registry = PluginRegistry()

        class CustomInput(InputProvider):
            def record(self, meeting_id: str) -> Path:
                return Path("custom.mp3")

        metadata = PluginMetadata(
            name="custom-input",
            version="1.0.0",
            provider_type="input",
            provider_class="CustomInput",
        )

        registry.register("custom-input", CustomInput, metadata)

        # Factory should fall back to plugin registry
        provider = get_input_provider("custom-input", {})

        assert provider is not None
        assert isinstance(provider, CustomInput)

    def test_builtin_provider_takes_precedence(self):
        """Test that built-in providers take precedence over plugins."""
        from meetscribe.core.plugin import PluginMetadata, PluginRegistry
        from meetscribe.inputs.factory import get_input_provider
        from meetscribe.inputs.file_provider import FileProvider

        registry = PluginRegistry()

        class OverrideFileProvider(InputProvider):
            def record(self, meeting_id: str) -> Path:
                return Path("override.mp3")

        metadata = PluginMetadata(
            name="file",
            version="1.0.0",
            provider_type="input",
            provider_class="OverrideFileProvider",
        )

        registry.register("file", OverrideFileProvider, metadata)

        # Built-in "file" provider should still be returned
        provider = get_input_provider("file", {"audio_path": "test.mp3"})

        assert isinstance(provider, FileProvider)
