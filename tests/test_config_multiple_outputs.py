"""
Tests for multiple outputs configuration support.

This test suite covers Phase 1: Config Layer implementation
for Issue #200 - Multiple Output Formats Support.
"""

import pytest
from pathlib import Path
from meetscribe.core.config import (
    OutputConfig,
    PipelineConfig,
    InputConfig,
    ConvertConfig,
    LLMConfig,
)


class TestOutputConfig:
    """Test OutputConfig with new fields for multiple outputs support."""

    def test_output_config_basic(self):
        """Test basic OutputConfig creation."""
        config = OutputConfig(format="markdown", params={"output_dir": "./meetings"})
        assert config.format == "markdown"
        assert config.params["output_dir"] == "./meetings"

    def test_output_config_with_enabled_flag(self):
        """Test OutputConfig with enabled flag."""
        config = OutputConfig(format="pdf", params={}, enabled=True)
        assert config.enabled is True

    def test_output_config_disabled(self):
        """Test OutputConfig can be disabled."""
        config = OutputConfig(format="json", params={}, enabled=False)
        assert config.enabled is False

    def test_output_config_default_enabled_is_true(self):
        """Test OutputConfig defaults to enabled=True."""
        config = OutputConfig(format="url")
        assert config.enabled is True

    def test_output_config_with_on_error_strategy(self):
        """Test OutputConfig with error handling strategy."""
        config = OutputConfig(format="markdown", on_error="continue")
        assert config.on_error == "continue"

        config2 = OutputConfig(format="pdf", on_error="stop")
        assert config2.on_error == "stop"

    def test_output_config_default_on_error_is_continue(self):
        """Test OutputConfig defaults to on_error='continue'."""
        config = OutputConfig(format="json")
        assert config.on_error == "continue"

    def test_output_config_with_execution_group(self):
        """Test OutputConfig with execution_group for serial execution."""
        config = OutputConfig(format="pdf", execution_group=1)
        assert config.execution_group == 1

    def test_output_config_default_execution_group_is_zero(self):
        """Test OutputConfig defaults to execution_group=0 (parallel)."""
        config = OutputConfig(format="markdown")
        assert config.execution_group == 0

    def test_output_config_with_dependencies(self):
        """Test OutputConfig with depends_on list."""
        config = OutputConfig(format="discord_webhook", depends_on=["pdf", "markdown"])
        assert config.depends_on == ["pdf", "markdown"]

    def test_output_config_default_depends_on_is_empty(self):
        """Test OutputConfig defaults to empty depends_on list."""
        config = OutputConfig(format="json")
        assert config.depends_on == []

    def test_output_config_with_wait_for_group(self):
        """Test OutputConfig with wait_for_group flag."""
        config = OutputConfig(format="pdf", execution_group=1, wait_for_group=True)
        assert config.wait_for_group is True

    def test_output_config_default_wait_for_group_is_true(self):
        """Test OutputConfig defaults to wait_for_group=True."""
        config = OutputConfig(format="markdown")
        assert config.wait_for_group is True


class TestPipelineConfigMultipleOutputs:
    """Test PipelineConfig with multiple outputs support."""

    def test_pipeline_config_with_single_output_legacy(self):
        """Test backward compatibility with single output config."""
        config_dict = {
            "input": {"provider": "file", "params": {"audio_path": "./test.mp3"}},
            "convert": {"engine": "passthrough", "params": {}},
            "llm": {"engine": "notebooklm", "params": {}},
            "output": {"format": "url", "params": {}},
        }
        config = PipelineConfig.from_dict(config_dict)

        assert config.output.format == "url"
        # Should work with legacy single output

    def test_pipeline_config_with_multiple_outputs(self):
        """Test PipelineConfig with outputs list."""
        config_dict = {
            "input": {"provider": "file", "params": {"audio_path": "./test.mp3"}},
            "convert": {"engine": "passthrough", "params": {}},
            "llm": {"engine": "notebooklm", "params": {}},
            "outputs": [
                {"format": "url", "params": {}},
                {"format": "markdown", "params": {"output_dir": "./meetings"}},
                {"format": "json", "params": {}},
            ],
        }
        config = PipelineConfig.from_dict(config_dict)

        # Should have outputs attribute
        assert hasattr(config, "outputs")
        assert len(config.outputs) == 3
        assert config.outputs[0].format == "url"
        assert config.outputs[1].format == "markdown"
        assert config.outputs[2].format == "json"

    def test_pipeline_config_get_output_configs_single(self):
        """Test get_output_configs() returns list for single output."""
        config_dict = {
            "input": {"provider": "file", "params": {"audio_path": "./test.mp3"}},
            "convert": {"engine": "passthrough", "params": {}},
            "llm": {"engine": "notebooklm", "params": {}},
            "output": {"format": "markdown", "params": {}},
        }
        config = PipelineConfig.from_dict(config_dict)

        output_configs = config.get_output_configs()
        assert isinstance(output_configs, list)
        assert len(output_configs) == 1
        assert output_configs[0].format == "markdown"

    def test_pipeline_config_get_output_configs_multiple(self):
        """Test get_output_configs() returns outputs list."""
        config_dict = {
            "input": {"provider": "file", "params": {"audio_path": "./test.mp3"}},
            "convert": {"engine": "passthrough", "params": {}},
            "llm": {"engine": "notebooklm", "params": {}},
            "outputs": [{"format": "url"}, {"format": "markdown"}, {"format": "pdf"}],
        }
        config = PipelineConfig.from_dict(config_dict)

        output_configs = config.get_output_configs()
        assert len(output_configs) == 3
        assert all(isinstance(cfg, OutputConfig) for cfg in output_configs)

    def test_pipeline_config_get_output_configs_filters_disabled(self):
        """Test get_output_configs() filters out disabled outputs."""
        config_dict = {
            "input": {"provider": "file", "params": {"audio_path": "./test.mp3"}},
            "convert": {"engine": "passthrough", "params": {}},
            "llm": {"engine": "notebooklm", "params": {}},
            "outputs": [
                {"format": "url", "enabled": True},
                {"format": "markdown", "enabled": False},
                {"format": "json", "enabled": True},
            ],
        }
        config = PipelineConfig.from_dict(config_dict)

        output_configs = config.get_output_configs()
        assert len(output_configs) == 2
        assert output_configs[0].format == "url"
        assert output_configs[1].format == "json"

    def test_pipeline_config_get_execution_groups(self):
        """Test get_execution_groups() returns grouped outputs."""
        config_dict = {
            "input": {"provider": "file", "params": {"audio_path": "./test.mp3"}},
            "convert": {"engine": "passthrough", "params": {}},
            "llm": {"engine": "notebooklm", "params": {}},
            "outputs": [
                {"format": "url", "execution_group": 0},
                {"format": "markdown", "execution_group": 0},
                {"format": "pdf", "execution_group": 1},
                {"format": "discord", "execution_group": 2},
            ],
        }
        config = PipelineConfig.from_dict(config_dict)

        groups = config.get_execution_groups()
        assert isinstance(groups, dict)
        assert 0 in groups
        assert 1 in groups
        assert 2 in groups
        assert len(groups[0]) == 2  # url, markdown
        assert len(groups[1]) == 1  # pdf
        assert len(groups[2]) == 1  # discord

    def test_pipeline_config_with_output_execution_mode(self):
        """Test PipelineConfig with output_execution_mode."""
        config_dict = {
            "input": {"provider": "file", "params": {"audio_path": "./test.mp3"}},
            "convert": {"engine": "passthrough", "params": {}},
            "llm": {"engine": "notebooklm", "params": {}},
            "outputs": [{"format": "url"}, {"format": "markdown"}],
            "output_execution_mode": "parallel",
        }
        config = PipelineConfig.from_dict(config_dict)

        assert config.output_execution_mode == "parallel"

    def test_pipeline_config_default_execution_mode_is_auto(self):
        """Test PipelineConfig defaults to output_execution_mode='auto'."""
        config_dict = {
            "input": {"provider": "file", "params": {"audio_path": "./test.mp3"}},
            "convert": {"engine": "passthrough", "params": {}},
            "llm": {"engine": "notebooklm", "params": {}},
            "outputs": [{"format": "url"}],
        }
        config = PipelineConfig.from_dict(config_dict)

        assert config.output_execution_mode == "auto"

    def test_pipeline_config_execution_mode_validation(self):
        """Test output_execution_mode only accepts valid values."""
        valid_modes = ["auto", "parallel", "serial"]

        for mode in valid_modes:
            config_dict = {
                "input": {"provider": "file", "params": {"audio_path": "./test.mp3"}},
                "convert": {"engine": "passthrough", "params": {}},
                "llm": {"engine": "notebooklm", "params": {}},
                "outputs": [{"format": "url"}],
                "output_execution_mode": mode,
            }
            config = PipelineConfig.from_dict(config_dict)
            assert config.output_execution_mode == mode


class TestPipelineConfigYAMLParsing:
    """Test YAML parsing for multiple outputs."""

    def test_parse_yaml_with_multiple_outputs(self, tmp_path):
        """Test parsing YAML file with multiple outputs."""
        yaml_content = """
input:
  provider: file
  params:
    audio_path: ./sample.mp3

convert:
  engine: passthrough
  params: {}

llm:
  engine: notebooklm
  params: {}

outputs:
  - format: url
    params:
      save_metadata: true
  - format: markdown
    params:
      output_dir: ./meetings
  - format: json
    params:
      output_dir: ./meetings
"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(yaml_content)

        config = PipelineConfig.from_yaml(config_file)

        assert len(config.get_output_configs()) == 3
        assert config.get_output_configs()[0].format == "url"
        assert config.get_output_configs()[1].format == "markdown"
        assert config.get_output_configs()[2].format == "json"

    def test_parse_yaml_with_execution_groups(self, tmp_path):
        """Test parsing YAML with execution_group and depends_on."""
        yaml_content = """
input:
  provider: file
  params:
    audio_path: ./test.mp3

convert:
  engine: passthrough
  params: {}

llm:
  engine: notebooklm
  params: {}

outputs:
  - format: url
    execution_group: 0
  - format: markdown
    execution_group: 0
  - format: pdf
    execution_group: 1
    params:
      output_dir: ./meetings
  - format: discord
    execution_group: 2
    depends_on: ["pdf"]
    params:
      webhook_url: "https://discord.com/api/webhooks/xxx"
"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(yaml_content)

        config = PipelineConfig.from_yaml(config_file)
        groups = config.get_execution_groups()

        assert len(groups[0]) == 2
        assert len(groups[1]) == 1
        assert len(groups[2]) == 1
        assert config.outputs[3].depends_on == ["pdf"]

    def test_backward_compatibility_single_output(self, tmp_path):
        """Test backward compatibility with old single output format."""
        yaml_content = """
input:
  provider: file
  params:
    audio_path: ./test.mp3

convert:
  engine: passthrough
  params: {}

llm:
  engine: notebooklm
  params: {}

output:
  format: markdown
  params:
    output_dir: ./meetings
"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(yaml_content)

        config = PipelineConfig.from_yaml(config_file)

        # Should still work with get_output_configs()
        output_configs = config.get_output_configs()
        assert len(output_configs) == 1
        assert output_configs[0].format == "markdown"
