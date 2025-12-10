"""
Configuration management for MeetScribe.

Supports YAML-based pipeline configuration with validation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import yaml
import os
import logging


logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Configuration validation error."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Configuration validation failed: {', '.join(errors)}")


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
    output: Union[OutputConfig, List[OutputConfig], None] = None
    outputs: Optional[List[OutputConfig]] = None
    working_dir: Path = Path("./meetings")
    cleanup_audio: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    output_execution_mode: str = "auto"  # "auto", "parallel", "serial"
    daemon: Optional[Dict[str, Any]] = None

    # Valid provider/engine/format names
    VALID_INPUT_PROVIDERS = ['file', 'zip', 'discord', 'meet', 'google-meet', 'zoom', 'webrtc', 'obs', 'proctap']
    VALID_CONVERT_ENGINES = ['passthrough', 'whisper', 'whisper-api', 'faster-whisper', 'gemini', 'deepgram']
    VALID_LLM_ENGINES = ['notebooklm', 'chatgpt', 'gpt', 'claude', 'gemini']
    VALID_OUTPUT_FORMATS = ['url', 'markdown', 'md', 'json', 'pdf', 'docs', 'google-docs', 'sheets', 'google-sheets', 'webhook', 'discord']

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
            ConfigValidationError: If config is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Expand environment variables
        data = cls._expand_env_vars(data)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        """
        Create config from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            PipelineConfig instance

        Raises:
            ConfigValidationError: If config is invalid
        """
        # Validate required sections
        errors = cls._validate_structure(data)
        if errors:
            raise ConfigValidationError(errors)

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
            output_data = data['output']
            if isinstance(output_data, list):
                # Multiple outputs as list
                output_cfg = [
                    OutputConfig(
                        format=out['format'],
                        params=out.get('params', {}),
                        enabled=out.get('enabled', True),
                        on_error=out.get('on_error', 'continue'),
                        execution_group=out.get('execution_group', 0),
                        depends_on=out.get('depends_on', []),
                        wait_for_group=out.get('wait_for_group', True)
                    )
                    for out in output_data
                ]
            else:
                # Single output
                output_cfg = OutputConfig(
                    format=output_data['format'],
                    params=output_data.get('params', {}),
                    enabled=output_data.get('enabled', True),
                    on_error=output_data.get('on_error', 'continue'),
                    execution_group=output_data.get('execution_group', 0),
                    depends_on=output_data.get('depends_on', []),
                    wait_for_group=output_data.get('wait_for_group', True)
                )

        if 'outputs' in data:
            # Multiple outputs format (alternative key)
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
        daemon = data.get('daemon')

        config = cls(
            input=input_cfg,
            convert=convert_cfg,
            llm=llm_cfg,
            output=output_cfg,
            outputs=outputs_cfg,
            working_dir=working_dir,
            cleanup_audio=cleanup_audio,
            metadata=metadata,
            output_execution_mode=output_execution_mode,
            daemon=daemon
        )

        # Validate semantic rules
        errors = config.validate()
        if errors:
            raise ConfigValidationError(errors)

        return config

    @classmethod
    def _validate_structure(cls, data: Dict[str, Any]) -> List[str]:
        """Validate config structure."""
        errors = []

        # Required top-level sections
        required_sections = ['input', 'convert', 'llm']
        for section in required_sections:
            if section not in data:
                errors.append(f"Missing required section: '{section}'")

        # output or outputs required
        if 'output' not in data and 'outputs' not in data:
            errors.append("Missing required section: 'output' or 'outputs'")

        # Validate input section
        if 'input' in data:
            if not isinstance(data['input'], dict):
                errors.append("'input' must be a dictionary")
            elif 'provider' not in data['input']:
                errors.append("'input.provider' is required")

        # Validate convert section
        if 'convert' in data:
            if not isinstance(data['convert'], dict):
                errors.append("'convert' must be a dictionary")
            elif 'engine' not in data['convert']:
                errors.append("'convert.engine' is required")

        # Validate llm section
        if 'llm' in data:
            if not isinstance(data['llm'], dict):
                errors.append("'llm' must be a dictionary")
            elif 'engine' not in data['llm']:
                errors.append("'llm.engine' is required")

        # Validate output section
        if 'output' in data:
            output = data['output']
            if isinstance(output, list):
                for i, out in enumerate(output):
                    if not isinstance(out, dict):
                        errors.append(f"'output[{i}]' must be a dictionary")
                    elif 'format' not in out:
                        errors.append(f"'output[{i}].format' is required")
            elif isinstance(output, dict):
                if 'format' not in output:
                    errors.append("'output.format' is required")
            else:
                errors.append("'output' must be a dictionary or list")

        # Validate outputs section
        if 'outputs' in data:
            outputs = data['outputs']
            if not isinstance(outputs, list):
                errors.append("'outputs' must be a list")
            else:
                for i, out in enumerate(outputs):
                    if not isinstance(out, dict):
                        errors.append(f"'outputs[{i}]' must be a dictionary")
                    elif 'format' not in out:
                        errors.append(f"'outputs[{i}].format' is required")

        return errors

    @classmethod
    def _expand_env_vars(cls, data: Any) -> Any:
        """Recursively expand environment variables in config."""
        if isinstance(data, dict):
            return {k: cls._expand_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls._expand_env_vars(item) for item in data]
        elif isinstance(data, str):
            # Expand ${VAR} and $VAR patterns
            return os.path.expandvars(data)
        return data

    def validate(self) -> List[str]:
        """
        Validate configuration semantically.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate input provider
        provider = self.input.provider.lower()
        if provider not in self.VALID_INPUT_PROVIDERS:
            errors.append(
                f"Unknown input provider: '{self.input.provider}'. "
                f"Valid: {', '.join(self.VALID_INPUT_PROVIDERS)}"
            )

        # Validate convert engine
        engine = self.convert.engine.lower().replace('_', '-')
        if engine not in self.VALID_CONVERT_ENGINES:
            errors.append(
                f"Unknown convert engine: '{self.convert.engine}'. "
                f"Valid: {', '.join(self.VALID_CONVERT_ENGINES)}"
            )

        # Validate LLM engine
        llm_engine = self.llm.engine.lower()
        if llm_engine not in self.VALID_LLM_ENGINES:
            errors.append(
                f"Unknown LLM engine: '{self.llm.engine}'. "
                f"Valid: {', '.join(self.VALID_LLM_ENGINES)}"
            )

        # Validate output format(s)
        for out in self.get_outputs():
            fmt = out.format.lower().replace('_', '-')
            if fmt not in self.VALID_OUTPUT_FORMATS:
                errors.append(
                    f"Unknown output format: '{out.format}'. "
                    f"Valid: {', '.join(self.VALID_OUTPUT_FORMATS)}"
                )

        # Provider-specific validation
        errors.extend(self._validate_provider_params())

        return errors

    def _validate_provider_params(self) -> List[str]:
        """Validate provider-specific parameters."""
        errors = []

        # File provider requires audio_path
        if self.input.provider == 'file':
            if 'audio_path' not in self.input.params:
                errors.append("File provider requires 'audio_path' parameter")

        # ZIP provider requires zip_path
        if self.input.provider == 'zip':
            if 'zip_path' not in self.input.params:
                errors.append("ZIP provider requires 'zip_path' parameter")

        # Whisper API requires api_key
        if self.convert.engine in ('whisper', 'whisper-api'):
            api_key = self.convert.params.get('api_key') or os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("Whisper API: No API key found (will run in mock mode)")

        # Discord webhook requires webhook_url
        for out in self.get_outputs():
            if out.format in ('webhook', 'discord'):
                webhook_url = out.params.get('webhook_url') or os.getenv('DISCORD_WEBHOOK_URL')
                if not webhook_url:
                    logger.warning("Discord webhook: No webhook URL found (will run in mock mode)")

        return errors

    def get_outputs(self) -> List[OutputConfig]:
        """Get output configurations as list."""
        if self.outputs:
            return [cfg for cfg in self.outputs if cfg.enabled]
        elif self.output:
            if isinstance(self.output, list):
                return [cfg for cfg in self.output if cfg.enabled]
            return [self.output] if self.output.enabled else []
        return []

    def get_output_configs(self) -> List[OutputConfig]:
        """
        Get list of enabled output configurations.
        Alias for get_outputs() for backwards compatibility.

        Returns:
            List of OutputConfig instances (filters out disabled outputs)
        """
        return self.get_outputs()

    def get_execution_groups(self) -> Dict[int, List[OutputConfig]]:
        """
        Group outputs by execution_group for serial/parallel execution.

        Returns:
            Dictionary mapping execution_group -> list of OutputConfig
        """
        groups: Dict[int, List[OutputConfig]] = {}
        for output_cfg in self.get_outputs():
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
            if isinstance(self.output, list):
                result['output'] = [
                    {'format': out.format, 'params': out.params}
                    for out in self.output
                ]
            else:
                result['output'] = {
                    'format': self.output.format,
                    'params': self.output.params
                }

        if self.daemon:
            result['daemon'] = self.daemon

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

    Raises:
        FileNotFoundError: If config file doesn't exist
        ConfigValidationError: If config is invalid
    """
    return PipelineConfig.from_yaml(path)


def validate_config(path: Path) -> List[str]:
    """
    Validate a configuration file without loading it.

    Args:
        path: Path to config file

    Returns:
        List of validation errors (empty if valid)
    """
    try:
        load_config(path)
        return []
    except FileNotFoundError as e:
        return [str(e)]
    except ConfigValidationError as e:
        return e.errors
    except Exception as e:
        return [f"Configuration error: {e}"]


def create_default_config() -> PipelineConfig:
    """
    Create a default configuration.

    Returns:
        PipelineConfig with sensible defaults
    """
    return PipelineConfig(
        input=InputConfig(provider='file', params={'audio_path': './audio.mp3'}),
        convert=ConvertConfig(engine='passthrough', params={}),
        llm=LLMConfig(engine='notebooklm', params={}),
        output=OutputConfig(format='url', params={})
    )
