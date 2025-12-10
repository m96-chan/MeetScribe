# MeetScribe API Reference

This document provides a comprehensive API reference for MeetScribe components.

## Table of Contents

- [Core Models](#core-models)
- [Input Providers](#input-providers)
- [Converters](#converters)
- [LLM Providers](#llm-providers)
- [Output Renderers](#output-renderers)
- [Utilities](#utilities)
- [Configuration](#configuration)

---

## Core Models

### Transcript

Represents a transcription result from the CONVERT layer.

```python
from meetscribe.core.models import Transcript

transcript = Transcript(
    meeting_info=MeetingInfo(...),
    text="Full transcript text",
    segments=[Segment(...), ...],
    audio_path=Path("audio.mp3"),
    audio_info=AudioInfo(...),
    metadata={"converter": "whisper"}
)
```

**Attributes:**
- `meeting_info` (MeetingInfo): Meeting metadata
- `text` (Optional[str]): Full transcript text
- `segments` (List[Segment]): Time-aligned segments
- `audio_path` (Optional[Path]): Path to source audio
- `audio_info` (Optional[AudioInfo]): Audio metadata
- `metadata` (Dict[str, Any]): Additional metadata
- `processing_history` (List[Dict]): Processing steps log

**Methods:**
- `add_processing_step(step_name, details)`: Add a processing step to history
- `to_dict()`: Convert to dictionary

---

### Minutes

Represents generated meeting minutes from the LLM layer.

```python
from meetscribe.core.models import Minutes

minutes = Minutes(
    meeting_id="2024-01-15T10-00_discord_general",
    summary="Meeting summary...",
    decisions=[Decision(...)],
    action_items=[ActionItem(...)],
    key_points=["Point 1", "Point 2"],
    participants=["Alice", "Bob"],
    url="https://notebooklm.google.com/...",
    metadata={"llm_engine": "chatgpt"}
)
```

**Attributes:**
- `meeting_id` (str): Meeting identifier
- `summary` (str): Meeting summary
- `decisions` (List[Decision]): Decisions made
- `action_items` (List[ActionItem]): Action items
- `key_points` (List[str]): Key discussion points
- `participants` (List[str]): Participant names
- `url` (Optional[str]): External URL (e.g., NotebookLM)
- `generated_at` (datetime): Generation timestamp
- `metadata` (Dict[str, Any]): Additional metadata

---

### MeetingInfo

Meeting metadata container.

```python
from meetscribe.core.models import MeetingInfo

info = MeetingInfo(
    meeting_id="2024-01-15T10-00_discord_general",
    source_type="discord",
    start_time=datetime.now(),
    end_time=None,
    channel_id="general",
    participants=["Alice", "Bob"]
)
```

---

### Segment

Time-aligned transcript segment.

```python
from meetscribe.core.models import Segment

segment = Segment(
    start=0.0,
    end=5.5,
    text="Hello everyone.",
    speaker="Alice",
    confidence=0.95,
    language="en"
)
```

---

### AudioInfo

Audio file metadata.

```python
from meetscribe.core.models import AudioInfo

info = AudioInfo(
    duration=138.0,
    samplerate=48000,
    codec="opus",
    channels=2,
    bitrate=128000
)
```

---

## Input Providers

### Factory Function

```python
from meetscribe.inputs.factory import get_input_provider

provider = get_input_provider("file", {"audio_path": "./audio.mp3"})
audio_path = provider.record("2024-01-15T10-00_meeting")
```

### Available Providers

| Provider | Name | Description |
|----------|------|-------------|
| FileProvider | `file` | Load from local file or directory |
| ZipProvider | `zip` | Extract from ZIP archive |
| GoogleMeetProvider | `meet`, `google-meet` | Download from Google Drive |
| OBSProvider | `obs` | Monitor OBS recording directory |
| WebRTCProvider | `webrtc` | Capture WebRTC stream |
| DiscordBotProvider | `discord` | Record Discord voice channels |

### FileProvider

```python
provider = get_input_provider("file", {
    "audio_path": "./recordings",  # File or directory
    "pattern": "*.mp3",            # Glob pattern for directory
    "copy_to_working_dir": True,
    "working_dir": "./meetings",
    "validate_format": True
})
```

### ZipProvider

```python
provider = get_input_provider("zip", {
    "zip_path": "./recording.zip",
    "extract_dir": "./extracted",
    "mode": "single",  # or "multiple"
    "sort_by": "name"  # or "date"
})
```

---

## Converters

### Factory Function

```python
from meetscribe.converters.factory import get_converter

converter = get_converter("whisper", {"model": "whisper-1"})
transcript = converter.transcribe(audio_path, meeting_id)
```

### Available Converters

| Converter | Name | Description |
|-----------|------|-------------|
| PassthroughConverter | `passthrough` | No transcription (for audio-capable LLMs) |
| WhisperAPIConverter | `whisper`, `whisper-api` | OpenAI Whisper API |
| FasterWhisperConverter | `faster-whisper` | Local GPU transcription |
| GeminiAudioConverter | `gemini` | Google Gemini audio |
| DeepgramConverter | `deepgram` | Deepgram with diarization |

### WhisperAPIConverter

```python
converter = get_converter("whisper", {
    "model": "whisper-1",
    "language": "en",
    "response_format": "verbose_json",
    "temperature": 0.0
})
```

### FasterWhisperConverter

```python
converter = get_converter("faster-whisper", {
    "model_size": "large-v3",  # tiny, base, small, medium, large-v2, large-v3
    "device": "cuda",          # cuda, cpu, auto
    "compute_type": "float16",
    "language": "en",
    "beam_size": 5,
    "vad_filter": True
})
```

### DeepgramConverter

```python
converter = get_converter("deepgram", {
    "model": "nova-2",
    "language": "en",
    "diarize": True,
    "punctuate": True,
    "smart_format": True
})
```

---

## LLM Providers

### Factory Function

```python
from meetscribe.llm.factory import get_llm_provider

llm = get_llm_provider("chatgpt", {"model": "gpt-4-turbo"})
minutes = llm.generate_minutes(transcript)
```

### Available Providers

| Provider | Name | Description |
|----------|------|-------------|
| NotebookLMProvider | `notebooklm` | Google NotebookLM |
| ChatGPTProvider | `chatgpt`, `gpt` | OpenAI GPT models |
| ClaudeProvider | `claude` | Anthropic Claude |
| GeminiProvider | `gemini` | Google Gemini |

### ChatGPTProvider

```python
llm = get_llm_provider("chatgpt", {
    "model": "gpt-4-turbo",
    "temperature": 0.3,
    "max_tokens": 4096,
    "system_prompt": "Custom prompt..."
})
```

### ClaudeProvider

```python
llm = get_llm_provider("claude", {
    "model": "claude-3-opus-20240229",
    "temperature": 0.3,
    "max_tokens": 4096
})
```

---

## Output Renderers

### Factory Function

```python
from meetscribe.outputs.factory import get_output_renderer, get_multiple_renderers

renderer = get_output_renderer("markdown", {"output_dir": "./meetings"})
result = renderer.render(minutes, meeting_id)

# Multiple outputs
renderers = get_multiple_renderers([
    {"format": "markdown", "params": {"output_dir": "./meetings"}},
    {"format": "json", "params": {"output_dir": "./meetings"}},
])
```

### Available Renderers

| Renderer | Name | Description |
|----------|------|-------------|
| URLRenderer | `url` | Save NotebookLM URL |
| MarkdownRenderer | `markdown`, `md` | Markdown document |
| JSONRenderer | `json` | Structured JSON |
| PDFRenderer | `pdf` | PDF document |
| GoogleDocsRenderer | `docs`, `google-docs` | Google Docs |
| GoogleSheetsRenderer | `sheets`, `google-sheets` | Google Sheets |
| DiscordWebhookRenderer | `webhook`, `discord` | Discord webhook |

### MarkdownRenderer

```python
renderer = get_output_renderer("markdown", {
    "output_dir": "./meetings",
    "include_toc": True,
    "include_participants": True,
    "template": "default"
})
```

### PDFRenderer

```python
renderer = get_output_renderer("pdf", {
    "output_dir": "./meetings",
    "page_size": "A4",
    "title_font_size": 16,
    "body_font_size": 11
})
```

---

## Utilities

### Audio Utilities

```python
from meetscribe.utils import (
    get_audio_info,
    get_audio_duration,
    convert_audio,
    normalize_audio,
    remove_silence,
    extract_audio_from_video,
    split_audio,
    merge_audio,
)

# Get audio info
info = get_audio_info(Path("audio.mp3"))

# Convert format
convert_audio(
    Path("input.wav"),
    Path("output.mp3"),
    samplerate=16000,
    channels=1
)

# Normalize loudness
normalize_audio(Path("audio.mp3"), target_lufs=-16.0)

# Split long audio
segments = split_audio(Path("long.mp3"), Path("segments/"), segment_duration=300)
```

### File Utilities

```python
from meetscribe.utils import (
    ensure_directory,
    get_meeting_directory,
    safe_copy,
    safe_move,
    cleanup_old_files,
    save_json,
    load_json,
)

# Ensure directory exists
ensure_directory(Path("./meetings"))

# Get meeting directory
meeting_dir = get_meeting_directory(Path("./meetings"), "2024-01-15T10-00_test")

# Clean up old files
deleted = cleanup_old_files(Path("./meetings"), max_age_days=30)

# JSON operations
save_json({"key": "value"}, Path("data.json"))
data = load_json(Path("data.json"))
```

---

## Configuration

### PipelineConfig

```python
from meetscribe.core.config import PipelineConfig, load_config

# From YAML file
config = PipelineConfig.from_yaml(Path("config.yaml"))

# From dictionary
config = PipelineConfig.from_dict({
    "input": {"provider": "file", "params": {"audio_path": "./audio.mp3"}},
    "convert": {"engine": "whisper", "params": {}},
    "llm": {"engine": "chatgpt", "params": {}},
    "output": {"format": "markdown", "params": {}},
})

# Validate
errors = config.validate()
if errors:
    print("Config errors:", errors)

# Get outputs (handles single or multiple)
outputs = config.get_outputs()
```

### Logging Setup

```python
from meetscribe.core.logging import setup_logging, get_logger, LogContext

# Setup logging
setup_logging(
    level="info",
    log_file=Path("meetscribe.log"),
    log_format="detailed",
    json_output=False
)

# Get module logger
logger = get_logger("my_module")
logger.info("Processing started")

# Context logging
with LogContext(meeting_id="123", user="alice"):
    logger.info("Processing meeting")  # Includes context in JSON output
```

---

## Environment Variables

| Variable | Description | Used By |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | WhisperAPIConverter, ChatGPTProvider |
| `ANTHROPIC_API_KEY` | Anthropic API key | ClaudeProvider |
| `GOOGLE_API_KEY` | Google API key | GeminiProvider, GeminiConverter |
| `DEEPGRAM_API_KEY` | Deepgram API key | DeepgramConverter |
| `DISCORD_BOT_TOKEN` | Discord bot token | DiscordBotProvider |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | DiscordWebhookRenderer |
| `GOOGLE_APPLICATION_CREDENTIALS` | Google service account | GoogleDocsRenderer, GoogleSheetsRenderer |
