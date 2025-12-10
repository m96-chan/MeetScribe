# Contributing to MeetScribe

Thank you for your interest in contributing to MeetScribe! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Adding New Providers](#adding-new-providers)

---

## Code of Conduct

This project follows a standard Code of Conduct. Please be respectful and inclusive in all interactions.

---

## Getting Started

### Prerequisites

- Python 3.9+
- Git
- ffmpeg (for audio tests)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/MeetScribe.git
   cd MeetScribe
   ```

3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/m96-chan/MeetScribe.git
   ```

---

## Development Setup

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
```

### Install Development Dependencies

```bash
pip install -e ".[dev,all]"
```

### Install Pre-commit Hooks

```bash
pre-commit install
```

### Verify Setup

```bash
pytest tests/ -v
```

---

## Making Changes

### Branch Naming

Create a feature branch from `main`:

```bash
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring
- `test/description` - Test additions/changes

### Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

Examples:
```
feat(converter): add Deepgram converter with diarization
fix(config): handle missing optional fields
docs(api): update converter documentation
```

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Tests

```bash
# Run a specific test file
pytest tests/test_converters.py -v

# Run a specific test class
pytest tests/test_converters.py::TestWhisperAPIConverter -v

# Run a specific test
pytest tests/test_converters.py::TestWhisperAPIConverter::test_mock_transcription -v
```

### Run with Coverage

```bash
pytest tests/ --cov=meetscribe --cov-report=html
```

### Run Integration Tests

```bash
pytest tests/ -m integration -v
```

### Run Linting

```bash
# Ruff
ruff check .

# Black
black --check .

# isort
isort --check-only .

# MyPy
mypy meetscribe
```

### Fix Formatting

```bash
black .
isort .
ruff check . --fix
```

---

## Pull Request Process

### 1. Update Your Branch

```bash
git fetch upstream
git rebase upstream/main
```

### 2. Run All Checks

```bash
# Format code
black .
isort .

# Run linters
ruff check .
mypy meetscribe

# Run tests
pytest tests/ -v
```

### 3. Push Your Branch

```bash
git push origin feature/your-feature-name
```

### 4. Create Pull Request

1. Go to the repository on GitHub
2. Click "Pull requests" → "New pull request"
3. Select your branch
4. Fill in the PR template:
   - Summary of changes
   - Related issues
   - Test plan
   - Screenshots (if applicable)

### 5. Address Review Feedback

- Respond to comments
- Push additional commits if needed
- Request re-review when ready

---

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use docstrings for public functions/classes

### Docstring Format

```python
def function_name(param1: str, param2: int = 10) -> bool:
    """
    Brief description of function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
    """
    pass
```

### Import Order

```python
# Standard library
import os
from pathlib import Path

# Third-party
import yaml
from pydantic import BaseModel

# Local
from meetscribe.core.models import Transcript
```

### Error Handling

```python
# Good
try:
    result = api_call()
except APIError as e:
    logger.error(f"API call failed: {e}")
    raise

# Avoid bare except
try:
    result = api_call()
except:  # Don't do this
    pass
```

---

## Adding New Providers

### Input Provider

1. Create `meetscribe/inputs/your_provider.py`:

```python
"""Your Provider for MeetScribe."""

from pathlib import Path
from typing import Dict, Any
import logging

from ..core.providers import InputProvider

logger = logging.getLogger(__name__)


class YourProvider(InputProvider):
    """Description of your provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Initialize config parameters
        self.param1 = config.get('param1', 'default')

    def record(self, meeting_id: str) -> Path:
        """
        Record or fetch audio.

        Args:
            meeting_id: Meeting identifier

        Returns:
            Path to audio file
        """
        logger.info(f"Recording with YourProvider: {meeting_id}")
        # Implementation here
        return audio_path

    def validate_config(self) -> bool:
        """Validate configuration."""
        if not self.param1:
            raise ValueError("param1 is required")
        return True
```

2. Register in `meetscribe/inputs/factory.py`:

```python
from .your_provider import YourProvider

PROVIDERS = {
    # ... existing providers
    'your-provider': YourProvider,
}
```

3. Add tests in `tests/test_inputs.py`:

```python
class TestYourProvider:
    def test_init_default_config(self):
        provider = YourProvider({})
        assert provider.param1 == 'default'

    def test_record(self, tmp_path):
        provider = YourProvider({'output_dir': str(tmp_path)})
        result = provider.record("2024-01-15T10-00_test")
        assert result.exists()
```

### Converter

1. Create `meetscribe/converters/your_converter.py`
2. Register in `meetscribe/converters/factory.py`
3. Add tests in `tests/test_converters.py`

### LLM Provider

1. Create `meetscribe/llm/your_provider.py`
2. Register in `meetscribe/llm/factory.py`
3. Add tests in `tests/test_llm.py`

### Output Renderer

1. Create `meetscribe/outputs/your_renderer.py`
2. Register in `meetscribe/outputs/factory.py`
3. Add tests in `tests/test_outputs.py`

---

## Documentation

### Updating Documentation

- API changes → Update `docs/api-reference.md`
- New features → Update `docs/user-guide.md`
- Architecture changes → Update `docs/architecture.md`

### Building Documentation

```bash
# Preview with mkdocs (if configured)
mkdocs serve
```

---

## Release Process

Releases are managed by maintainers:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag
4. GitHub Actions handles PyPI publishing

---

## Getting Help

- Open an issue for bugs or feature requests
- Use discussions for questions
- Join our Discord (if available)

Thank you for contributing to MeetScribe!
