# MeetScribe Pipeline Specification

This document explains how data flows through the MeetScribe pipeline.

## 1. Pipeline Stages

### Stage 1 — INPUT
Responsible for generating raw audio/log data.
Output: audio files + minimal metadata

### Stage 2 — CONVERT
Converts audio into a Transcript object.
Output: `Transcript(text/audio_path/segments/metadata/audio_info/meeting_info)`

### Stage 3 — LLM
Consumes Transcript and produces structured minutes.
Output schema:
```
{
  "summary": "...",
  "decisions": [...],
  "action_items": [...],
  "url": "..."
}
```

### Stage 4 — OUTPUT
Stores or renders the final document.

## 2. Transcript Object

A unified data model with full metadata:
- text
- audio_path
- segments
- meeting_info
- audio_info
- metadata
- processing_history

