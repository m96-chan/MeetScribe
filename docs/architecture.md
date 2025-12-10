# MeetScribe Architecture

This document describes the architectural design and principles behind MeetScribe.

## Table of Contents

- [Overview](#overview)
- [Pipeline Architecture](#pipeline-architecture)
- [Component Design](#component-design)
- [Data Flow](#data-flow)
- [Extension Points](#extension-points)
- [Security Considerations](#security-considerations)

---

## Overview

MeetScribe is a modular, extensible, multi-source AI meeting pipeline framework. It transforms raw meeting audio into structured meeting minutes through a four-layer pipeline.

### Core Mission

> "Turn every meeting into structured knowledge, automatically."

### Design Principles

1. **Modularity** - Every component is a plugin
2. **Flexibility** - Support multiple audio sources, transcription engines, and LLMs
3. **Extensibility** - Easy to add new providers and renderers
4. **Configuration-first** - YAML defines pipelines; CLI executes them
5. **Developer-friendly** - Clear interfaces and comprehensive documentation

---

## Pipeline Architecture

MeetScribe follows a strict 4-layer pipeline structure:

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  INPUT  │───>│ CONVERT │───>│   LLM   │───>│ OUTPUT  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │
     │              │              │              │
 Audio/Video    Transcript      Minutes       Artifacts
 Acquisition    Generation     Generation     Rendering
```

### Layer Responsibilities

| Layer | Input | Output | Responsibility |
|-------|-------|--------|---------------|
| INPUT | Source config | Audio file | Acquire meeting audio |
| CONVERT | Audio file | Transcript | Convert audio to text |
| LLM | Transcript | Minutes | Generate structured minutes |
| OUTPUT | Minutes | Artifact | Render final output |

---

## Component Design

### Base Interfaces

All providers implement a common interface pattern:

```python
class BaseProvider:
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        self.config = config

    def validate_config(self) -> bool:
        """Validate configuration."""
        raise NotImplementedError
```

### INPUT Layer

```python
class InputProvider(BaseProvider):
    def record(self, meeting_id: str) -> Path:
        """Acquire audio and return path."""
        raise NotImplementedError
```

**Implementations:**
- `FileProvider` - Local file/directory
- `ZipProvider` - ZIP archive extraction
- `GoogleMeetProvider` - Google Drive recordings
- `OBSProvider` - OBS recording directory
- `WebRTCProvider` - WebRTC stream capture
- `DiscordBotProvider` - Discord voice channels

### CONVERT Layer

```python
class ConvertProvider(BaseProvider):
    def transcribe(self, audio_path: Path, meeting_id: str) -> Transcript:
        """Convert audio to transcript."""
        raise NotImplementedError
```

**Implementations:**
- `PassthroughConverter` - No transcription (for audio-capable LLMs)
- `WhisperAPIConverter` - OpenAI Whisper API
- `FasterWhisperConverter` - Local GPU transcription
- `GeminiAudioConverter` - Google Gemini
- `DeepgramConverter` - Deepgram with diarization

### LLM Layer

```python
class LLMProvider(BaseProvider):
    def generate_minutes(self, transcript: Transcript) -> Minutes:
        """Generate meeting minutes from transcript."""
        raise NotImplementedError
```

**Implementations:**
- `NotebookLMProvider` - Google NotebookLM
- `ChatGPTProvider` - OpenAI GPT models
- `ClaudeProvider` - Anthropic Claude
- `GeminiProvider` - Google Gemini

### OUTPUT Layer

```python
class OutputRenderer(BaseProvider):
    def render(self, minutes: Minutes, meeting_id: str) -> str:
        """Render minutes to output format."""
        raise NotImplementedError
```

**Implementations:**
- `URLRenderer` - Save URL reference
- `MarkdownRenderer` - Markdown document
- `JSONRenderer` - Structured JSON
- `PDFRenderer` - PDF document
- `GoogleDocsRenderer` - Google Docs
- `GoogleSheetsRenderer` - Google Sheets
- `DiscordWebhookRenderer` - Discord webhook

---

## Data Flow

### Core Data Models

```
┌─────────────────────────────────────────────────────────┐
│                      Transcript                          │
├─────────────────────────────────────────────────────────┤
│ meeting_info: MeetingInfo                               │
│ text: Optional[str]           # Full transcript text    │
│ segments: List[Segment]       # Time-aligned segments   │
│ audio_path: Optional[Path]    # Source audio path       │
│ audio_info: Optional[AudioInfo]                         │
│ metadata: Dict[str, Any]                                │
│ processing_history: List[Dict]                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                       Minutes                            │
├─────────────────────────────────────────────────────────┤
│ meeting_id: str                                          │
│ summary: str                                             │
│ decisions: List[Decision]                                │
│ action_items: List[ActionItem]                           │
│ key_points: List[str]                                    │
│ participants: List[str]                                  │
│ url: Optional[str]                                       │
│ generated_at: datetime                                   │
│ metadata: Dict[str, Any]                                 │
└─────────────────────────────────────────────────────────┘
```

### MeetingInfo

Contains meeting metadata:

```python
@dataclass
class MeetingInfo:
    meeting_id: str
    source_type: str        # discord, meet, obs, etc.
    start_time: datetime
    end_time: Optional[datetime]
    channel_id: Optional[str]
    participants: List[str]
```

### Segment

Time-aligned transcript segment:

```python
@dataclass
class Segment:
    start: float           # Start time in seconds
    end: float             # End time in seconds
    text: str              # Segment text
    speaker: Optional[str] # Speaker identifier
    confidence: Optional[float]
    language: Optional[str]
```

---

## Extension Points

### Adding a New Provider

1. **Create provider class** implementing the base interface
2. **Register in factory** using the provider name
3. **Add configuration schema** to documentation
4. **Write unit tests** for the provider

### Factory Pattern

Factories use string-based registration:

```python
# converters/factory.py
CONVERTERS = {
    'passthrough': PassthroughConverter,
    'whisper': WhisperAPIConverter,
    'faster-whisper': FasterWhisperConverter,
    # Add new converter here
    'my-converter': MyConverter,
}

def get_converter(engine: str, config: Dict[str, Any]) -> ConvertProvider:
    if engine not in CONVERTERS:
        raise ValueError(f"Unsupported converter: {engine}")
    return CONVERTERS[engine](config)
```

---

## Runtime Architecture

### CLI Execution

```
┌──────────────────────────────────────────────────────────┐
│                        CLI                                │
│  meetscribe run --config config.yaml                      │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                    PipelineRunner                         │
│  - Loads configuration                                    │
│  - Instantiates providers                                 │
│  - Executes pipeline steps                                │
│  - Handles errors and cleanup                             │
└─────────────────────────┬────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   ┌─────────┐      ┌─────────┐      ┌─────────┐
   │ Input   │      │ Convert │      │  LLM    │
   │ Provider│ ───> │ Provider│ ───> │ Provider│
   └─────────┘      └─────────┘      └─────────┘
                                          │
                                          ▼
                                    ┌─────────┐
                                    │ Output  │
                                    │ Renderer│
                                    └─────────┘
```

### Daemon Mode

```
┌──────────────────────────────────────────────────────────┐
│                   DiscordDaemon                           │
│  - Monitors voice channels                                │
│  - Triggers recording on activity                         │
│  - Manages concurrent recordings                          │
└─────────────────────────┬────────────────────────────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
         ┌────────┐  ┌────────┐  ┌────────┐
         │Recording│  │Recording│  │Recording│
         │ Task 1 │  │ Task 2 │  │ Task 3 │
         └────────┘  └────────┘  └────────┘
```

---

## Security Considerations

### API Key Management

- Never commit API keys to version control
- Use environment variables or `.env` files
- Support for `${VAR_NAME}` expansion in configs

### Audio Data

- Raw audio can be deleted after processing (`cleanup_audio: true`)
- Processing happens locally or via encrypted API calls
- No audio is stored on external servers (except by transcription APIs)

---

## Meeting ID Convention

MeetScribe uses a structured meeting ID format:

```
YYYY-MM-DDTHH-MM_<source>_<channel-or-identifier>
```

Examples:
- `2024-01-15T10-00_discord_general`
- `2024-01-15T14-30_meet_project-sync`
- `2024-01-15T09-00_obs_recording`

This enables:
- Deterministic folder structure
- Searchability and filtering
- Safe file naming (no special characters)
- Future RAG-ready metadata

---

## Future Considerations

### Planned Extensions

1. **Plugin System** - Dynamic loading of external providers
2. **Worker Queue** - For parallel processing of multiple meetings
3. **Web Dashboard** - For monitoring and management
4. **RAG Integration** - Searchable meeting history

### Scalability

Current design supports:
- Single meeting processing (synchronous)
- Multiple daemon recordings (async)

Future design could support:
- Worker queue (Celery/Redis)
- Distributed processing
- Cloud-native deployment
