# MeetScribe User Guide

This guide covers everything you need to know to use MeetScribe effectively.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Running Pipelines](#running-pipelines)
- [Discord Daemon](#discord-daemon)
- [Output Formats](#output-formats)
- [Troubleshooting](#troubleshooting)

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
