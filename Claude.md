
# MeetScribe — Architectural Principles (Design Summary)

This document summarizes the architectural philosophy and system design principles behind **MeetScribe**, a modular, extensible, multi‑source AI meeting pipeline framework.

---

## 1. Vision

MeetScribe aims to unify *all forms of meeting input* (Discord, Zoom, Google Meet, WebRTC, ProcTap, OBS, etc.) into a single, pluggable AI pipeline capable of:

- Recording / ingesting multi‑source audio  
- Converting raw audio into LLM‑ready formats  
- Generating meeting minutes using multiple LLM engines  
- Producing final artifacts (NotebookLM URL, Google Docs, PDF, Markdown, JSON, etc.)

**Core mission:**  
> “Turn every meeting into structured knowledge, automatically.”

---

## 2. High-Level Architecture

MeetScribe follows a strict **4‑layer pipeline structure**:

```
INPUT  →  CONVERT  →  LLM  →  OUTPUT
```

Each layer is modular, replaceable, and configurable via YAML.

### 2.1 INPUT Layer (Recording Providers)
Handles acquisition of raw meeting data.

Supported providers (extensible):
- Discord BOT (voice stream recording)
- Zoom Cloud (API download)
- Google Meet (Drive recordings)
- ProcTap (local process audio tapping for confidential cases)
- WebRTC streams
- OBS recordings

Each provider extends a common interface:
```python
class InputProvider:
    def record(self, meeting_id): ...
    def fetch(self, meeting_id): ...
```

---

## 3. CONVERT Layer (Transcription / Audio Handling)

**Key idea:**  
CONVERT is *not only transcription*. It transforms raw data into an LLM‑usable format.

Two operating modes:

### (A) Standard transcription  
- Whisper API (OpenAI Whisper‑1)  
- faster‑whisper (local GPU)  
- Gemini 2 Flash Audio  
- Deepgram  

### (B) Pass-through mode  
Used when the LLM directly receives audio (NotebookLM audio documents, ChatGPT Audio inputs).  
No transcription performed.

---

## 4. Unified Transcript Object

All converters output a standardized **Transcript object**, not just JSON.

```python
Transcript(
    text: Optional[str],
    audio_path: Optional[str],
    segments: List,
    audio_info: Dict,
    meeting_info: Dict,
    metadata: Dict,
    processing_history: List
)
```

### Transcript includes full metadata:
- **Audio info:** duration, samplerate, codec, LUFS, peak, noise level, silence ratio  
- **Meeting info:** meeting_id, source type, participants, timestamps  
- **Converter metadata:** model used, language, cost estimate  
- **Processing history:** step‑by‑step logs for debugging  
- **Segments:** rich diarization entries (start, end, text, speaker)

Debugging is enabled until the OUTPUT layer completes; raw files may be auto‑cleaned afterward.

---

## 5. LLM Layer (Minutes Generation)

The LLM layer converts Transcript → structured minutes.

Supported engines:
- **NotebookLM**  
  - Best for long-form meeting understanding  
  - Supports API Key & Service Account  
- **ChatGPT (GPT‑5.x / o1)**  
  - Best for document formatting & PDF/Docs generation  
- **Claude 3.7**  
  - Best for structured analysis  
- **Gemini 2 Ultra / Flash**  
  - Fast & cost‑efficient

All LLMs produce a unified Minutes schema:

```json
{
  "summary": "...",
  "decisions": [...],
  "action_items": [...],
  "url": "..."
}
```

---

## 6. OUTPUT Layer (Final Artifacts)

User-selectable final output formats:

- NotebookLM Notebook URL  
- Google Docs (Drive API)  
- PDF (ReportLab)  
- Markdown  
- JSON  
- Custom templates

Each renderer implements:

```python
class OutputRenderer:
    def render(self, minutes, meeting_id) -> str:
        return output_path_or_url
```

---

## 7. Runtime Model (Execution Architecture)

MeetScribe uses a **CLI-first, Docker-compatible runtime**.

### Primary commands:
```
meetscribe run --config file.yaml
meetscribe daemon --config file.yaml
meetscribe init discord
```

### Modes:
1. **Run Mode**: execute full pipeline (INPUT → OUTPUT)
2. **Daemon Mode**: Discord monitoring (notify or auto-join)
3. **Config-driven pipelines**: user config selects provider/LLM/output

### Why no Worker Queue for MVP?
- 4-hour audio processing fits comfortably in synchronous pipelines  
- Whisper/Gemini transcription takes minutes, not hours  
- Worker Queue can be introduced later if parallelism is needed

---

## 8. Meeting ID Specification

MeetScribe uses a machine-friendly, metadata-rich identifier:

```
YYYY-MM-DDTHH-MM_<source>_<channel-or-pid>
```

Example:
```
2025-11-21T19-00_discord_channel1234
```

This ensures:
- deterministic folder structure  
- searchability  
- safe file naming  
- future RAG-ready metadata

---

## 9. Folder Structure (v0.1)

```
meetscribe/
  core/            # Runner, Daemon, Config, ID generator
  inputs/          # Discord, Zoom, ProcTap, WebRTC...
  converters/      # Whisper, Gemini, Pass-through...
  llm/             # NotebookLM, ChatGPT, Claude...
  outputs/         # Docs, PDF, Markdown, JSON...
  templates/       # Minutes templates
  utils/           # Audio and file helpers
  README.md
```

---

## 10. Design Principles (Core Philosophy)

- **Everything is modular**  
  Every component is a plugin (input, converter, llm, output).

- **Transcript unifies the pipeline**  
  All data—raw or processed—flows through the Transcript model.

- **Config-first architecture**  
  YAML defines the pipeline; CLI executes it.

- **User‑controlled automation**  
  Daemon can notify-only or auto-join Discord meetings.

- **Security-conscious**  
  Raw audio is optionally deleted after final artifacts are generated.

- **Long-term extensibility**  
  More LLMs, audio engines, and meeting providers can be added easily.

---

## 11. Project Name

**MeetScribe**  
A combination of *“Meeting”* + *“Scribe (Secretary)”* — easy to recall, professional, and perfect for OSS branding.

---

## 12. License

Apache License 2.0  
(Commercial-friendly, patent-safe, OSS-contributor friendly.)

---

## 13. Next Steps

- Implement CLI (`run`, `daemon`, `init`)
- Implement Discord recorder (Python-based)
- Implement Whisper/Gemini converters
- Implement NotebookLM + ChatGPT clients
- Implement Output renderers (Google Docs, PDF, MD)
- Add test suite and sample configs

MeetScribe aims to become **the open-source Meeting OS** for developers, creators, and teams.

---
