"""
Unit tests for configuration management.
"""


import pytest
import yaml

from meetscribe.core.config import (
    ConfigValidationError,
    OutputConfig,
    PipelineConfig,
    create_default_config,
    validate_config,
)


@pytest.fixture
def valid_config_dict():
    """Create valid configuration dictionary."""
    return {
        "input": {"provider": "file", "params": {"audio_path": "./audio.mp3"}},
        "convert": {"engine": "whisper", "params": {}},
        "llm": {"engine": "chatgpt", "params": {}},
        "output": {"format": "markdown", "params": {}},
        "working_dir": "./meetings",
        "cleanup_audio": False,
    }


@pytest.fixture
def valid_config_file(tmp_path, valid_config_dict):
    """Create valid configuration file."""
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(valid_config_dict, f)
    return config_path


class TestPipelineConfig:
    """Tests for PipelineConfig."""

    def test_from_dict(self, valid_config_dict):
        """Test creating config from dictionary."""
        config = PipelineConfig.from_dict(valid_config_dict)

        assert config.input.provider == "file"
        assert config.convert.engine == "whisper"
        assert config.llm.engine == "chatgpt"
        assert isinstance(config.output, OutputConfig)
        assert config.output.format == "markdown"

    def test_from_yaml(self, valid_config_file):
        """Test loading config from YAML file."""
        config = PipelineConfig.from_yaml(valid_config_file)

        assert config.input.provider == "file"
        assert config.convert.engine == "whisper"

    def test_missing_input_section(self):
        """Test error for missing input section."""
        config_dict = {
            "convert": {"engine": "whisper"},
            "llm": {"engine": "chatgpt"},
            "output": {"format": "markdown"},
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            PipelineConfig.from_dict(config_dict)

        assert "Missing required section: 'input'" in str(exc_info.value)

    def test_missing_provider(self):
        """Test error for missing provider."""
        config_dict = {
            "input": {"params": {}},
            "convert": {"engine": "whisper"},
            "llm": {"engine": "chatgpt"},
            "output": {"format": "markdown"},
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            PipelineConfig.from_dict(config_dict)

        assert "'input.provider' is required" in str(exc_info.value)

    def test_invalid_provider(self, valid_config_dict):
        """Test error for invalid provider."""
        valid_config_dict["input"]["provider"] = "invalid_provider"

        with pytest.raises(ConfigValidationError) as exc_info:
            PipelineConfig.from_dict(valid_config_dict)

        assert "Unknown input provider" in str(exc_info.value)

    def test_invalid_convert_engine(self, valid_config_dict):
        """Test error for invalid convert engine."""
        valid_config_dict["convert"]["engine"] = "invalid_engine"

        with pytest.raises(ConfigValidationError) as exc_info:
            PipelineConfig.from_dict(valid_config_dict)

        assert "Unknown convert engine" in str(exc_info.value)

    def test_invalid_llm_engine(self, valid_config_dict):
        """Test error for invalid LLM engine."""
        valid_config_dict["llm"]["engine"] = "invalid_llm"

        with pytest.raises(ConfigValidationError) as exc_info:
            PipelineConfig.from_dict(valid_config_dict)

        assert "Unknown LLM engine" in str(exc_info.value)

    def test_invalid_output_format(self, valid_config_dict):
        """Test error for invalid output format."""
        valid_config_dict["output"]["format"] = "invalid_format"

        with pytest.raises(ConfigValidationError) as exc_info:
            PipelineConfig.from_dict(valid_config_dict)

        assert "Unknown output format" in str(exc_info.value)

    def test_multiple_outputs(self, valid_config_dict):
        """Test configuration with multiple outputs."""
        valid_config_dict["output"] = [
            {"format": "markdown", "params": {}},
            {"format": "json", "params": {}},
            {"format": "pdf", "params": {}},
        ]

        config = PipelineConfig.from_dict(valid_config_dict)

        assert isinstance(config.output, list)
        assert len(config.output) == 3
        assert config.output[0].format == "markdown"
        assert config.output[1].format == "json"
        assert config.output[2].format == "pdf"

    def test_get_outputs(self, valid_config_dict):
        """Test get_outputs method."""
        # Single output
        config = PipelineConfig.from_dict(valid_config_dict)
        outputs = config.get_outputs()
        assert len(outputs) == 1

        # Multiple outputs
        valid_config_dict["output"] = [{"format": "markdown"}, {"format": "json"}]
        config = PipelineConfig.from_dict(valid_config_dict)
        outputs = config.get_outputs()
        assert len(outputs) == 2

    def test_to_dict(self, valid_config_dict):
        """Test converting config to dictionary."""
        config = PipelineConfig.from_dict(valid_config_dict)
        result = config.to_dict()

        assert result["input"]["provider"] == "file"
        assert result["convert"]["engine"] == "whisper"
        assert result["llm"]["engine"] == "chatgpt"
        assert result["output"]["format"] == "markdown"

    def test_save_and_load(self, tmp_path, valid_config_dict):
        """Test saving and loading config."""
        config = PipelineConfig.from_dict(valid_config_dict)

        save_path = tmp_path / "saved_config.yaml"
        config.save(save_path)

        loaded_config = PipelineConfig.from_yaml(save_path)
        assert loaded_config.input.provider == config.input.provider

    def test_env_var_expansion(self, tmp_path):
        """Test environment variable expansion."""
        import os

        os.environ["TEST_AUDIO_PATH"] = "/path/to/audio.mp3"

        config_dict = {
            "input": {"provider": "file", "params": {"audio_path": "${TEST_AUDIO_PATH}"}},
            "convert": {"engine": "whisper"},
            "llm": {"engine": "chatgpt"},
            "output": {"format": "markdown"},
        }

        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_dict, f)

        config = PipelineConfig.from_yaml(config_path)
        assert config.input.params["audio_path"] == "/path/to/audio.mp3"

        del os.environ["TEST_AUDIO_PATH"]

    def test_daemon_config(self, valid_config_dict):
        """Test daemon configuration."""
        valid_config_dict["daemon"] = {
            "mode": "auto_record",
            "guild_ids": ["123456"],
            "min_users": 2,
        }

        config = PipelineConfig.from_dict(valid_config_dict)
        assert config.daemon is not None
        assert config.daemon["mode"] == "auto_record"


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_validate_valid_config(self, valid_config_file):
        """Test validating valid config."""
        errors = validate_config(valid_config_file)
        assert errors == []

    def test_validate_missing_file(self, tmp_path):
        """Test validating missing file."""
        errors = validate_config(tmp_path / "nonexistent.yaml")
        assert len(errors) > 0
        assert "not found" in errors[0].lower()

    def test_validate_invalid_config(self, tmp_path):
        """Test validating invalid config."""
        config_path = tmp_path / "invalid.yaml"
        with open(config_path, "w") as f:
            yaml.dump({"invalid": "config"}, f)

        errors = validate_config(config_path)
        assert len(errors) > 0


class TestCreateDefaultConfig:
    """Tests for create_default_config function."""

    def test_creates_valid_config(self):
        """Test creating default config."""
        config = create_default_config()

        assert isinstance(config, PipelineConfig)
        assert config.input.provider == "file"
        assert config.convert.engine == "passthrough"
        assert config.llm.engine == "notebooklm"
        assert config.output.format == "url"
