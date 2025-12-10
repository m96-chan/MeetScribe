# MeetScribe User Guide

This guide covers everything you need to know to use MeetScribe effectively.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Running Pipelines](#running-pipelines)
- [Discord Daemon](#discord-daemon)
- [Output Formats](#output-formats)
- [Input Sources](#input-sources)
- [Transcription Engines](#transcription-engines)
- [LLM Engines](#llm-engines)
- [Use Case Guides](#use-case-guides)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Glossary](#glossary)

---

## Installation

### Prerequisites

- Python 3.9 or higher
- ffmpeg (for audio processing)
- API keys for transcription/LLM services

### Install from PyPI

```bash
pip install meetscribe
```

### Install from Source

```bash
git clone https://github.com/m96-chan/MeetScribe.git
cd MeetScribe
pip install -e ".[all]"
```

### Install Optional Dependencies

```bash
# Audio processing
pip install meetscribe[audio]

# Whisper API
pip install meetscribe[whisper]

# Local faster-whisper
pip install meetscribe[faster-whisper]

# All features
pip install meetscribe[all]
```

### Install ffmpeg

**Windows:**
```bash
winget install ffmpeg
# or download from https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

---

## Quick Start

### 1. Create a Configuration File

```bash
meetscribe init
```

This creates a `config.yaml` file with default settings.

### 2. Set Environment Variables

Create a `.env` file:

```bash
OPENAI_API_KEY=sk-your-key-here
# Or for other services:
# ANTHROPIC_API_KEY=your-key
# GOOGLE_API_KEY=your-key
# DEEPGRAM_API_KEY=your-key
```

### 3. Run the Pipeline

```bash
meetscribe run --config config.yaml
```

---

## Configuration

### Basic Configuration

```yaml
input:
  provider: file
  params:
    audio_path: ./recording.mp3

convert:
  engine: whisper
  params:
    model: whisper-1
    language: en

llm:
  engine: chatgpt
  params:
    model: gpt-4-turbo
    temperature: 0.3

output:
  format: markdown
  params:
    output_dir: ./meetings
    include_toc: true

working_dir: ./meetings
cleanup_audio: false
```

### Multiple Outputs

```yaml
output:
  - format: markdown
    params:
      output_dir: ./meetings
  - format: json
    params:
      output_dir: ./meetings
  - format: pdf
    params:
      output_dir: ./meetings
```

### Environment Variable Expansion

Use `${VAR_NAME}` to reference environment variables:

```yaml
input:
  provider: file
  params:
    audio_path: ${AUDIO_PATH}

llm:
  engine: chatgpt
  params:
    api_key: ${OPENAI_API_KEY}
```

---

## Running Pipelines

### Basic Run

```bash
meetscribe run --config config.yaml
```

### Override Input File

```bash
meetscribe run --config config.yaml --input ./new_recording.mp3
```

### Verbose Output

```bash
meetscribe run --config config.yaml --verbose
```

### Dry Run

```bash
meetscribe run --config config.yaml --dry-run
```

---

## Discord Daemon

### Setup Discord Bot

1. Create a Discord application at https://discord.com/developers/applications
2. Create a bot and copy the token
3. Invite the bot to your server with voice permissions

### Daemon Configuration

```yaml
input:
  provider: discord
  params:
    bot_token: ${DISCORD_BOT_TOKEN}
    guild_id: "123456789"

daemon:
  mode: auto_record
  guild_ids:
    - "123456789"
  channel_patterns:
    - "meeting-*"
    - "standup"
  min_users: 2
  max_silence: 300
```

### Run Daemon

```bash
meetscribe daemon --config config.yaml
```

### Daemon Modes

- `notify`: Send notification when meeting starts (no recording)
- `auto_record`: Automatically join and record matching channels

---

## Output Formats

### Markdown

Creates a well-formatted Markdown document:

```yaml
output:
  format: markdown
  params:
    output_dir: ./meetings
    include_toc: true
    include_participants: true
    include_statistics: true
```

### JSON

Structured JSON for programmatic access:

```yaml
output:
  format: json
  params:
    output_dir: ./meetings
    include_statistics: true
```

### PDF

Professional PDF documents:

```yaml
output:
  format: pdf
  params:
    output_dir: ./meetings
    page_size: A4
    title_font_size: 16
    body_font_size: 11
```

### Google Docs

Create documents in Google Drive:

```yaml
output:
  format: docs
  params:
    folder_id: your-folder-id
    share_with:
      - email@example.com
```

### Discord Webhook

Post to Discord channel:

```yaml
output:
  format: webhook
  params:
    webhook_url: ${DISCORD_WEBHOOK_URL}
    username: MeetScribe
    include_action_items: true
    include_decisions: true
```

---

## Input Sources

### Local File

```yaml
input:
  provider: file
  params:
    audio_path: ./recording.mp3
```

### Directory (Process Latest)

```yaml
input:
  provider: file
  params:
    audio_path: ./recordings/
    pattern: "*.mp3"
```

### ZIP Archive

```yaml
input:
  provider: zip
  params:
    zip_path: ./meeting.zip
    mode: single  # or "multiple" for all files
```

### Google Meet (Drive)

```yaml
input:
  provider: meet
  params:
    download_dir: ./downloads
    keep_downloaded: true
```

### OBS Recording

```yaml
input:
  provider: obs
  params:
    recording_dir: ./obs_recordings
    pattern: "*.mkv"
    extract_audio: true
```

---

## Transcription Engines

### OpenAI Whisper API

```yaml
convert:
  engine: whisper
  params:
    model: whisper-1
    language: en
    temperature: 0.0
```

### Local faster-whisper

```yaml
convert:
  engine: faster-whisper
  params:
    model_size: large-v3
    device: cuda
    language: en
    vad_filter: true
```

### Deepgram

```yaml
convert:
  engine: deepgram
  params:
    model: nova-2
    diarize: true
    language: en
```

### Passthrough (No Transcription)

For LLMs that accept audio directly:

```yaml
convert:
  engine: passthrough
  params:
    include_audio_info: true
```

---

## LLM Engines

### OpenAI ChatGPT

```yaml
llm:
  engine: chatgpt
  params:
    model: gpt-4-turbo
    temperature: 0.3
    max_tokens: 4096
```

### Anthropic Claude

```yaml
llm:
  engine: claude
  params:
    model: claude-3-opus-20240229
    temperature: 0.3
```

### Google Gemini

```yaml
llm:
  engine: gemini
  params:
    model: gemini-1.5-pro
    temperature: 0.3
```

### NotebookLM

```yaml
llm:
  engine: notebooklm
  params:
    notebook_title_prefix: Meeting
```

---

## Troubleshooting

### Common Issues

#### "ffmpeg not found"

Install ffmpeg and ensure it's in your PATH:
```bash
ffmpeg -version
```

#### "API key not set"

Check your environment variables:
```bash
echo $OPENAI_API_KEY
```

Or set in `.env` file and load with python-dotenv.

#### "Audio file too large"

Split large files or use a streaming transcription service:
```yaml
convert:
  engine: faster-whisper
  params:
    vad_filter: true  # Removes silence
```

#### "Rate limit exceeded"

Add delay between API calls or use local transcription:
```yaml
convert:
  engine: faster-whisper
```

### Debug Mode

Enable debug logging:
```bash
meetscribe run --config config.yaml --log-level debug
```

### Log Files

Check log files in the working directory:
```bash
cat ./meetings/meetscribe.log
```

---

## Best Practices

1. **Use environment variables** for API keys - never commit them to git
2. **Set `cleanup_audio: false`** initially for debugging
3. **Use `passthrough` converter** with NotebookLM for best results
4. **Enable `vad_filter`** with faster-whisper for long meetings
5. **Use multiple outputs** to generate different formats in one run
6. **Monitor Discord daemon** logs for connection issues

---

## Use Case Guides

### Use Case 1: Generate Minutes from Local Audio File

The most basic use case. Generate meeting minutes from a pre-recorded audio file.

**Configuration:**

```yaml
input:
  provider: file
  params:
    audio_path: ./meeting_2024-01-15.mp3

convert:
  engine: whisper
  params:
    model: whisper-1
    language: en

llm:
  engine: chatgpt
  params:
    model: gpt-4-turbo
    temperature: 0.3

output:
  format: markdown
  params:
    output_dir: ./meetings
    include_toc: true
```

**Run:**

```bash
meetscribe run --config config.yaml
```

### Use Case 2: Discord Meeting Auto-Recording

Monitor Discord voice channels and automatically record and transcribe meetings.

**Prerequisites:**
- Discord Bot created and invited (see [Discord Daemon](#discord-daemon) section)

**Configuration:**

```yaml
input:
  provider: discord
  params:
    bot_token: ${DISCORD_BOT_TOKEN}
    guild_id: "123456789"

convert:
  engine: faster-whisper
  params:
    model_size: large-v3
    language: en

llm:
  engine: chatgpt
  params:
    model: gpt-4-turbo

output:
  - format: markdown
    params:
      output_dir: ./meetings
  - format: webhook
    params:
      webhook_url: ${DISCORD_WEBHOOK_URL}

daemon:
  mode: auto_record
  channel_patterns:
    - "meeting-*"
    - "standup"
  min_users: 2
```

**Run as Daemon:**

```bash
meetscribe daemon --config config.yaml
```

### Use Case 3: Process Google Meet Recordings

Process Google Meet recordings stored in Google Drive.

**Configuration:**

```yaml
input:
  provider: meet
  params:
    credentials_file: ./google_credentials.json
    download_dir: ./downloads
    keep_downloaded: false

convert:
  engine: gemini
  params:
    model: gemini-1.5-pro

llm:
  engine: gemini
  params:
    model: gemini-1.5-pro

output:
  format: docs
  params:
    folder_id: "your-google-drive-folder-id"
```

### Use Case 4: Multiple Output Formats

Generate multiple output formats from a single processing run.

**Configuration:**

```yaml
input:
  provider: file
  params:
    audio_path: ./recording.mp3

convert:
  engine: whisper
  params:
    model: whisper-1
    language: en

llm:
  engine: chatgpt
  params:
    model: gpt-4-turbo

output:
  - format: markdown
    params:
      output_dir: ./meetings
      include_toc: true
  - format: json
    params:
      output_dir: ./meetings
  - format: pdf
    params:
      output_dir: ./meetings
      page_size: A4
  - format: webhook
    params:
      webhook_url: ${DISCORD_WEBHOOK_URL}
```

### Use Case 5: Cost-Effective Processing

Minimize API costs by using local transcription and efficient LLMs.

**Configuration:**

```yaml
input:
  provider: file
  params:
    audio_path: ./recording.mp3

convert:
  engine: faster-whisper  # Free, runs locally
  params:
    model_size: base      # Smaller model for faster processing
    device: cuda
    vad_filter: true      # Remove silence to reduce processing time

llm:
  engine: gemini
  params:
    model: gemini-1.5-flash  # Lower cost than Pro

output:
  format: markdown
  params:
    output_dir: ./meetings
```

---

## FAQ

### Q: What audio formats are supported?

A: MeetScribe supports almost all formats that ffmpeg supports:
- MP3, WAV, M4A, FLAC, OGG, WebM, MP4, MKV, and more

### Q: Can I transcribe in languages other than English?

A: Yes, all transcription engines support multiple languages. Set the `language` parameter:
```yaml
convert:
  engine: whisper
  params:
    language: ja  # Japanese
```

### Q: Can I use MeetScribe offline?

A: Yes, using local faster-whisper with an offline-capable LLM:
```yaml
convert:
  engine: faster-whisper
  params:
    model_size: large-v3
    device: cuda
```

### Q: Can I process long meetings (4+ hours)?

A: Yes, but we recommend:
- Using local faster-whisper (no API limits)
- Setting `vad_filter: true` to remove silence
- Ensuring sufficient memory and disk space

### Q: Is speaker diarization supported?

A: Yes, Deepgram supports speaker diarization:
```yaml
convert:
  engine: deepgram
  params:
    diarize: true
```

### Q: Can I process multiple files at once?

A: Yes, specify a directory to process multiple files:
```yaml
input:
  provider: file
  params:
    audio_path: ./recordings/
    pattern: "*.mp3"
```

### Q: Can I use custom templates?

A: Yes, you can customize Markdown templates. See the API Reference for details.

### Q: How can I reduce costs?

A: Several strategies:
1. Use local faster-whisper (free)
2. Use cost-effective LLMs like Gemini Flash
3. Use smaller models for shorter meetings

### Q: How do I handle large files that exceed API limits?

A: Options:
1. Use local faster-whisper (no size limits)
2. Split files before processing
3. Enable `vad_filter` to reduce file size by removing silence

### Q: Can I run MeetScribe in Docker?

A: Yes, use the provided Dockerfile:
```bash
docker build -t meetscribe .
docker run -v $(pwd)/meetings:/app/meetings meetscribe run --config config.yaml
```

---

## Glossary

| Term | Description |
|------|-------------|
| **Pipeline** | The processing flow from input to output |
| **Provider** | Component that retrieves input from a source |
| **Converter** | Component that converts audio to text |
| **Renderer** | Component that outputs minutes in a specific format |
| **Daemon** | Background process that runs continuously |
| **Transcription** | The process of converting audio to text |
| **Diarization** | Speaker identification and separation |
| **VAD** | Voice Activity Detection - detects speech vs silence |
| **LLM** | Large Language Model |
| **Minutes** | Structured meeting summary with decisions and action items |
| **Passthrough** | Mode where audio is passed directly to LLM without transcription |

---

## Next Steps

- [API Reference](api-reference.md) - Detailed API documentation
- [Architecture](architecture.md) - System design details
- [Contributing Guide](contributing.md) - How to contribute
- [Tutorial](tutorial.md) - Step-by-step tutorials
- [日本語ガイド](user-guide-ja.md) - Japanese User Guide
