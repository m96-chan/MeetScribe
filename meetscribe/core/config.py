"""
Configuration management for MeetScribe.

Supports YAML-based pipeline configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path
import yaml


@dataclass
class InputConfig:
    """Configuration for INPUT layer."""

    provider: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConvertConfig:
    """Configuration for CONVERT layer."""

    engine: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMConfig:
    """Configuration for LLM layer."""

    engine: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OutputConfig:
    """Configuration for OUTPUT layer."""

    format: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""

    input: InputConfig
    convert: ConvertConfig
    llm: LLMConfig
    output: OutputConfig
    working_dir: Path = Path("./meetings")
    cleanup_audio: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "PipelineConfig":
        """
        Load configuration from YAML file.

        Args:
            path: Path to YAML config file

        Returns:
            PipelineConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        """
        Create config from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            PipelineConfig instance
        """
        input_cfg = InputConfig(
            provider=data['input']['provider'],
            params=data['input'].get('params', {})
        )

        convert_cfg = ConvertConfig(
            engine=data['convert']['engine'],
            params=data['convert'].get('params', {})
        )

        llm_cfg = LLMConfig(
            engine=data['llm']['engine'],
            params=data['llm'].get('params', {})
        )

        output_cfg = OutputConfig(
            format=data['output']['format'],
            params=data['output'].get('params', {})
        )

        working_dir = Path(data.get('working_dir', './meetings'))
        cleanup_audio = data.get('cleanup_audio', False)
        metadata = data.get('metadata', {})

        return cls(
            input=input_cfg,
            convert=convert_cfg,
            llm=llm_cfg,
            output=output_cfg,
            working_dir=working_dir,
            cleanup_audio=cleanup_audio,
            metadata=metadata
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'input': {
                'provider': self.input.provider,
                'params': self.input.params
            },
            'convert': {
                'engine': self.convert.engine,
                'params': self.convert.params
            },
            'llm': {
                'engine': self.llm.engine,
                'params': self.llm.params
            },
            'output': {
                'format': self.output.format,
                'params': self.output.params
            },
            'working_dir': str(self.working_dir),
            'cleanup_audio': self.cleanup_audio,
            'metadata': self.metadata
        }

    def save(self, path: Path):
        """
        Save configuration to YAML file.

        Args:
            path: Output path for config file
        """
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)


def load_config(path: Path) -> PipelineConfig:
    """
    Load pipeline configuration from file.

    Args:
        path: Path to config file

    Returns:
        PipelineConfig instance
    """
    return PipelineConfig.from_yaml(path)
