# MeetScribe Architecture Overview

This document explains the **overall system architecture** of MeetScribe, including the 4-layer pipeline, module relationships, and execution flow.

## 1. System Layers

MeetScribe is structured into four modular layers:

```
INPUT  →  CONVERT  →  LLM  →  OUTPUT
```

### INPUT Layer
Handles acquisition of multi-source meeting audio:
- Discord BOT
- Zoom Cloud
- Google Meet
- ProcTap (confidential)
- OBS / WebRTC

### CONVERT Layer
Transforms raw audio into an LLM-usable format:
- Whisper API
- faster-whisper
- Gemini Audio
- Pass-through (audio only)

### LLM Layer
Generates structured meeting minutes:
- NotebookLM
- ChatGPT
- Claude
- Gemini

### OUTPUT Layer
Creates final user-facing artifacts:
- Google Docs
- NotebookLM URL
- PDF
- Markdown
- JSON

## 2. Data Flow

```
record() → transcribe() → generate_minutes() → render()
```

## 3. Components

- **Runner**: Core orchestrator  
- **Daemon**: Discord monitoring  
- **Transcript**: Unified data model  
- **Minutes**: Unified LLM output model  

