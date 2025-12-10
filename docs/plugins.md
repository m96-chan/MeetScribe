# MeetScribe Plugin Development Guide

This guide explains how to create third-party plugins for MeetScribe.

## Overview

MeetScribe supports plugins for all four pipeline layers:

- **Input**: Recording providers (e.g., custom meeting platforms)
- **Converter**: Transcription engines (e.g., custom STT services)
- **LLM**: Minutes generation providers (e.g., custom AI services)
- **Output**: Rendering formats (e.g., custom document formats)

## Quick Start

### 1. Create a Plugin Package

```python
# my_meetscribe_plugin/provider.py
from pathlib import Path
from meetscribe.core.providers import InputProvider

class MyCustomProvider(InputProvider):
    """Custom input provider for my meeting platform."""

    __version__ = "1.0.0"
    __description__ = "Custom provider for MyPlatform meetings"
    __author__ = "Your Name"

    def record(self, meeting_id: str) -> Path:
        # Implement your recording logic
        output_path = Path(f"recordings/{meeting_id}.mp3")
        # ... record audio ...
        return output_path
```

### 2. Configure Entry Points

In your plugin's `pyproject.toml`:

```toml
[project.entry-points."meetscribe.plugins.input"]
my-custom = "my_meetscribe_plugin.provider:MyCustomProvider"
```

Or in `setup.py`:

```python
setup(
    name="my-meetscribe-plugin",
    entry_points={
        "meetscribe.plugins.input": [
            "my-custom = my_meetscribe_plugin.provider:MyCustomProvider",
        ],
    },
)
```

### 3. Install and Use

```bash
pip install my-meetscribe-plugin
```

Then use in your config:

```yaml
input:
  provider: my-custom
  params:
    custom_option: value
```

## Provider Types

### Input Provider

Handles recording or fetching meeting audio.

```python
from pathlib import Path
from meetscribe.core.providers import InputProvider

class MyInputProvider(InputProvider):
    def record(self, meeting_id: str) -> Path:
        """
        Record or fetch audio for a meeting.

        Args:
            meeting_id: Unique meeting identifier

        Returns:
            Path to the recorded audio file
        """
        # Implementation
        pass

    def validate_config(self) -> bool:
        """Optional: Validate configuration."""
        return True
```

Entry point group: `meetscribe.plugins.input`

### Converter Provider

Transforms audio into transcript format.

```python
from pathlib import Path
from meetscribe.core.providers import ConvertProvider
from meetscribe.core.models import Transcript

class MyConverter(ConvertProvider):
    def transcribe(self, audio_path: Path, meeting_id: str) -> Transcript:
        """
        Convert audio to transcript.

        Args:
            audio_path: Path to audio file
            meeting_id: Meeting identifier

        Returns:
            Transcript object with text and segments
        """
        # Implementation
        pass
```

Entry point group: `meetscribe.plugins.converter`

### LLM Provider

Generates meeting minutes from transcript.

```python
from meetscribe.core.providers import LLMProvider
from meetscribe.core.models import Transcript, Minutes

class MyLLMProvider(LLMProvider):
    def generate_minutes(self, transcript: Transcript) -> Minutes:
        """
        Generate meeting minutes from transcript.

        Args:
            transcript: Transcript object

        Returns:
            Minutes object with summary, decisions, action items
        """
        # Implementation
        pass
```

Entry point group: `meetscribe.plugins.llm`

### Output Renderer

Creates final output artifacts.

```python
from meetscribe.core.providers import OutputRenderer
from meetscribe.core.models import Minutes

class MyRenderer(OutputRenderer):
    def render(self, minutes: Minutes, meeting_id: str) -> str:
        """
        Render minutes to output format.

        Args:
            minutes: Minutes object
            meeting_id: Meeting identifier

        Returns:
            Path to output file or URL
        """
        # Implementation
        pass
```

Entry point group: `meetscribe.plugins.output`

## Plugin Metadata

Add metadata as class attributes:

```python
class MyProvider(InputProvider):
    __version__ = "1.0.0"
    __description__ = "Description of your plugin"
    __author__ = "Author Name"
    __homepage__ = "https://github.com/example/plugin"
    __dependencies__ = ["some-package>=1.0"]
```

## Programmatic Registration

For advanced use cases, register plugins programmatically:

```python
from meetscribe.core.plugin import PluginRegistry, PluginMetadata

registry = PluginRegistry()

metadata = PluginMetadata(
    name="my-plugin",
    version="1.0.0",
    provider_type="input",
    provider_class="MyProvider",
    description="My custom provider",
)

registry.register("my-plugin", MyProvider, metadata)
```

## Validation

MeetScribe validates plugins before loading:

1. **Base class check**: Must inherit from correct provider type
2. **Abstract method check**: Must implement required methods
3. **Instantiation check**: Must be instantiable

Use the validator manually:

```python
from meetscribe.core.plugin import PluginValidator

validator = PluginValidator()
is_valid, errors = validator.validate_provider_class(MyProvider, "input")

if not is_valid:
    print(f"Validation errors: {errors}")
```

## Best Practices

1. **Error handling**: Catch and log errors gracefully
2. **Configuration validation**: Implement `validate_config()` method
3. **Documentation**: Include docstrings and usage examples
4. **Testing**: Test with mock data before real deployments
5. **Dependencies**: Declare all dependencies in your package
6. **Versioning**: Follow semantic versioning

## Example Plugin Structure

```
my-meetscribe-plugin/
├── pyproject.toml
├── README.md
├── my_meetscribe_plugin/
│   ├── __init__.py
│   └── provider.py
└── tests/
    └── test_provider.py
```

## Debugging

Enable debug logging to see plugin discovery:

```python
import logging
logging.getLogger("meetscribe.core.plugin").setLevel(logging.DEBUG)
```

## API Reference

### PluginRegistry

- `register(name, class, metadata)`: Register a plugin
- `unregister(name)`: Remove a plugin
- `has_plugin(name)`: Check if plugin exists
- `get_plugin_class(name)`: Get plugin class
- `get_plugin_metadata(name)`: Get plugin metadata
- `get_all_plugins()`: List all plugins
- `get_plugins_by_type(type)`: Filter by provider type

### PluginDiscovery

- `discover_entry_points(type)`: Find plugins for a type
- `discover_all()`: Find all plugins

### PluginLoader

- `load(name, config)`: Load and instantiate a plugin

### PluginValidator

- `validate_provider_class(class, type)`: Validate a provider class
