# MeetScribe Tutorial

A step-by-step guide to using MeetScribe for meeting transcription and minutes generation.

## Prerequisites

Before starting, make sure you have:

1. Python 3.9 or higher installed
2. ffmpeg installed and in your PATH
3. An API key for at least one transcription service (OpenAI recommended)

## Part 1: Installation

### Install MeetScribe

```bash
# Install from PyPI
pip install meetscribe

# Or install from source
git clone https://github.com/m96-chan/MeetScribe.git
cd MeetScribe
pip install -e ".[all]"
```

### Verify Installation

```bash
meetscribe --version
```

## Part 2: Your First Pipeline

### Step 1: Create a Configuration File

Create a file called `config.yaml`:

```yaml
# Basic configuration for processing a local audio file

input:
  provider: file
  params:
    audio_path: ./my_meeting.mp3

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

### Step 2: Set Up API Keys

Create a `.env` file:

```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Step 3: Run the Pipeline

```bash
meetscribe run --config config.yaml
```

### Step 4: View Results

The meeting minutes will be saved in `./meetings/<meeting_id>/minutes.md`.

## Part 3: Understanding the Pipeline

MeetScribe processes meetings in four stages:

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  INPUT  │───>│ CONVERT │───>│   LLM   │───>│ OUTPUT  │
│ (Audio) │    │(Whisper)│    │(ChatGPT)│    │(Markdown)│
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

1. **INPUT**: Load audio from file, Discord, Google Meet, etc.
2. **CONVERT**: Transcribe audio to text using Whisper, Deepgram, etc.
3. **LLM**: Generate structured minutes using ChatGPT, Claude, etc.
4. **OUTPUT**: Render results as Markdown, PDF, JSON, etc.

## Part 4: Multiple Output Formats

Generate multiple formats in one run:

```yaml
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
```

## Part 5: Using Different Transcription Engines

### Local Transcription with faster-whisper

No API key needed! Uses your GPU for fast local transcription.

```yaml
convert:
  engine: faster-whisper
  params:
    model_size: base  # tiny, base, small, medium, large-v3
    device: auto      # cuda, cpu, auto
    language: en
```

### Deepgram with Speaker Diarization

Great for meetings with multiple speakers:

```yaml
convert:
  engine: deepgram
  params:
    model: nova-2
    diarize: true
    language: en
```

Environment variable: `DEEPGRAM_API_KEY`

## Part 6: Using Different LLM Providers

### Claude

```yaml
llm:
  engine: claude
  params:
    model: claude-3-opus-20240229
    temperature: 0.3
```

Environment variable: `ANTHROPIC_API_KEY`

### Gemini

```yaml
llm:
  engine: gemini
  params:
    model: gemini-1.5-pro
    temperature: 0.3
```

Environment variable: `GOOGLE_API_KEY`

### NotebookLM

For long meetings, NotebookLM is excellent:

```yaml
convert:
  engine: passthrough  # Don't transcribe - send audio directly

llm:
  engine: notebooklm
  params:
    notebook_title_prefix: Meeting

output:
  format: url
  params:
    output_dir: ./meetings
```

## Part 7: Discord Integration

### Setting Up the Discord Bot

1. Create a Discord application at https://discord.com/developers/applications
2. Create a bot and copy the token
3. Enable "Message Content Intent" and "Voice" permissions
4. Invite bot to your server with voice permissions

### Discord Daemon Configuration

```yaml
input:
  provider: discord
  params:
    bot_token: ${DISCORD_BOT_TOKEN}

convert:
  engine: faster-whisper
  params:
    model_size: base

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
  guild_ids:
    - "123456789012345678"
  channel_patterns:
    - "meeting-*"
    - "standup"
  min_users: 2
```

### Run the Daemon

```bash
meetscribe daemon --config config.yaml
```

The bot will:
1. Monitor voice channels matching the patterns
2. Automatically join when users start talking
3. Record the meeting
4. Generate minutes when the meeting ends
5. Post results to the Discord webhook

## Part 8: Processing ZIP Archives

For meetings exported from other tools:

```yaml
input:
  provider: zip
  params:
    zip_path: ./meeting_export.zip
    mode: single  # or "multiple" for batch processing
```

## Part 9: Best Practices

### 1. Use Environment Variables for Secrets

```yaml
llm:
  engine: chatgpt
  params:
    api_key: ${OPENAI_API_KEY}  # Never hardcode!
```

### 2. Keep Raw Audio for Debugging

```yaml
cleanup_audio: false  # Keep until you're confident in the output
```

### 3. Use VAD Filter for Long Meetings

```yaml
convert:
  engine: faster-whisper
  params:
    vad_filter: true  # Removes silence
```

### 4. Test with Passthrough First

When trying new LLMs:

```yaml
convert:
  engine: passthrough
  params:
    include_audio_info: true
```

## Part 10: Troubleshooting

### "ffmpeg not found"

Install ffmpeg:
- Windows: `winget install ffmpeg`
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

### "API key not set"

Check your `.env` file and ensure variables are loaded:

```python
from dotenv import load_dotenv
load_dotenv()
```

### "Audio file too large"

OpenAI Whisper has a 25MB limit. Options:
1. Use `faster-whisper` (no limit)
2. Split the audio file
3. Use Deepgram (supports larger files)

### Debug Logging

```bash
meetscribe run --config config.yaml --log-level debug
```

## Next Steps

- Read the [API Reference](api-reference.md) for detailed options
- Check the [Architecture](architecture.md) for system design
- See [Contributing](contributing.md) to add new features
