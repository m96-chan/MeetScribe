"""
Configuration management for MeetScribe.

Supports YAML-based pipeline configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
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
    """Configuration for OUTPUT layer with multiple outputs support."""

    format: str
    params: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    on_error: str = "continue"  # "continue" or "stop"
    execution_group: int = 0  # 0 = parallel, 1+ = serial groups
    depends_on: list = field(default_factory=list)
    wait_for_group: bool = True


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""

    input: InputConfig
    convert: ConvertConfig
    llm: LLMConfig
    output: Optional[OutputConfig] = None
    outputs: Optional[List[OutputConfig]] = None
    working_dir: Path = Path("./meetings")
    cleanup_audio: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    output_execution_mode: str = "auto"  # "auto", "parallel", "serial"

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

        # Handle both single output (legacy) and multiple outputs
        output_cfg = None
        outputs_cfg = None

        if 'output' in data:
            # Legacy single output format
            output_cfg = OutputConfig(
                format=data['output']['format'],
                params=data['output'].get('params', {}),
                enabled=data['output'].get('enabled', True),
                on_error=data['output'].get('on_error', 'continue'),
                execution_group=data['output'].get('execution_group', 0),
                depends_on=data['output'].get('depends_on', []),
                wait_for_group=data['output'].get('wait_for_group', True)
            )

        if 'outputs' in data:
            # Multiple outputs format
            outputs_cfg = [
                OutputConfig(
                    format=output['format'],
                    params=output.get('params', {}),
                    enabled=output.get('enabled', True),
                    on_error=output.get('on_error', 'continue'),
                    execution_group=output.get('execution_group', 0),
                    depends_on=output.get('depends_on', []),
                    wait_for_group=output.get('wait_for_group', True)
                )
                for output in data['outputs']
            ]

        working_dir = Path(data.get('working_dir', './meetings'))
        cleanup_audio = data.get('cleanup_audio', False)
        metadata = data.get('metadata', {})
        output_execution_mode = data.get('output_execution_mode', 'auto')

        return cls(
            input=input_cfg,
            convert=convert_cfg,
            llm=llm_cfg,
            output=output_cfg,
            outputs=outputs_cfg,
            working_dir=working_dir,
            cleanup_audio=cleanup_audio,
            metadata=metadata,
            output_execution_mode=output_execution_mode
        )

    def get_output_configs(self) -> List[OutputConfig]:
        """
        Get list of enabled output configurations.

        Returns:
            List of OutputConfig instances (filters out disabled outputs)
        """
        if self.outputs:
            # Multiple outputs - filter enabled only
            return [cfg for cfg in self.outputs if cfg.enabled]
        elif self.output:
            # Legacy single output
            return [self.output] if self.output.enabled else []
        else:
            return []

    def get_execution_groups(self) -> Dict[int, List[OutputConfig]]:
        """
        Group outputs by execution_group for serial/parallel execution.

        Returns:
            Dictionary mapping execution_group -> list of OutputConfig
        """
        groups: Dict[int, List[OutputConfig]] = {}
        for output_cfg in self.get_output_configs():
            group_id = output_cfg.execution_group
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(output_cfg)
        return groups

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        result = {
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
            'working_dir': str(self.working_dir),
            'cleanup_audio': self.cleanup_audio,
            'metadata': self.metadata,
            'output_execution_mode': self.output_execution_mode
        }

        # Include output or outputs depending on which is set
        if self.outputs:
            result['outputs'] = [
                {
                    'format': cfg.format,
                    'params': cfg.params,
                    'enabled': cfg.enabled,
                    'on_error': cfg.on_error,
                    'execution_group': cfg.execution_group,
                    'depends_on': cfg.depends_on,
                    'wait_for_group': cfg.wait_for_group
                }
                for cfg in self.outputs
            ]
        elif self.output:
            result['output'] = {
                'format': self.output.format,
                'params': self.output.params
            }

        return result

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
