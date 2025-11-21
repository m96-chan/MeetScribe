# MeetScribe Design Principles

MeetScribe follows several key principles to ensure extensibility, modularity, and reliability.

## 1. Modularity
Every component (input, converter, llm, output) is a pluggable module.

## 2. Transcript-Centric
The Transcript object unifies all conversions and ensures consistent processing.

## 3. Config-Driven
Pipelines are defined in YAML and executed via CLI:
```
meetscribe run --config file.yaml
```

## 4. Secure-by-Design
Raw audio may be automatically deleted after output rendering.

## 5. Extensible
Easily add new:
- meeting sources
- transcription engines
- LLM models
- output formats

## 6. OSS-Friendly
Apache 2.0 licensing to encourage contributions.

