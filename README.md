# MeetScribe

MeetScribe は **あらゆる Web 会議を自動で記録・文字起こしし、複数の LLM（NotebookLM / ChatGPT / Claude / Gemini など）を用いて議事録を生成する OSS パイプラインフレームワーク** です。

Discord / Zoom / Google Meet / WebRTC / ProcTap（秘匿録音）など異なる会議媒体を統一的に扱い、  
録音 → テキスト化 → 議事録生成 → PDF / Google Docs / NotebookLM URL / Markdown 出力  
までをすべて自動化します。

---

## ✨ Features

### ✔ 1. マルチ会議媒体に対応（Input 層）
複数の会議ソースを **共通インターフェイスで抽象化**。

- **Discord BOT**（録音 & 録画）
- **Zoom Cloud Recordings**（API経由で自動取得）
- **Google Meet / Drive Recordings**
- **ProcTap（秘匿ケースのローカル録音）**
- **WebRTC / OBS / カスタム入力**

`inputs/` ディレクトリ配下に追加すれば拡張可能。

---

### ✔ 2. Transcription 層（CONVERT 層）
音声 → テキスト化をモジュール単位で差し替え可能。

- Whisper API（OpenAI Whisper-1）
- faster-whisper（GPUローカル）
- Gemini 2 Flash Audio
- Deepgram（予定）

出力は共通の Transcript JSON 形式：

```json
{
  "text": "...",
  "segments": [ ... ],
  "speaker_map": { ... }
}
```

✔ 3. LLM 層（NotebookLM / ChatGPT / Gemini / Claude）
議事録生成エンジンを自由に選択：

NotebookLM（最強の議事録モデル）

ChatGPT (GPT-5 / GPT-o1) — 整形・Docs 生成に最適

Claude 3.7 — 構造化要約に強い

Gemini 2 Ultra / Flash — 高速・低コスト

共通 Minutes 形式に変換：

```json
コードをコピーする
{
  "summary": "...",
  "decisions": [...],
  "action_items": [...],
  "url": "https://..."
}
```
NotebookLM は API Key / ServiceAccount の両方に対応。

✔ 4. Output 層（最終成果物生成）
最終出力形式も自由に設定可能。

NotebookLM ノート URL（Open in NotebookLM）

Google Docs（Drive API）

PDF（ReportLab）

Markdown

JSON

outputs/ 配下に追加するだけでカスタム renderer を作成可能。

✔ 5. Daemon（Discord 自動監視）
MeetScribe は Discord の会議を**常時監視（オプション）**できる。

新しい会議が開始 → 通知（デフォルト）

設定次第で 自動参加 → 自動録音 も可能

録音終了後、自動で Pipeline を実行

meetscribe daemon で起動。

✔ 6. 完全 CLI / Docker 実行モデル
MeetScribe は Docker/CLI 原理主義で設計。

```arduino
meetscribe run --config configs/discord.yaml
```

Daemon:
```arduino
meetscribe daemon --config configs/discord.yaml
```
Config-driven pipeline により、ユーザーは自由に INPUT / LLM / OUTPUT を切替可能。

📦 Directory Structure (v0.1)
```markdown
meetscribe/
  core/
    runner.py
    daemon.py
    meeting_id.py
    config.py

  inputs/
    discord_bot/
      recorder.py
    proctap/
      tap.py
    zoom/
      cloud_downloader.py
    google_meet/
      drive_fetch.py

  converters/
    whisper_api/
      transcribe.py
    whisper_local/
      transcribe.py
    gemini_audio/
      transcribe.py

  llm/
    notebooklm/
      client.py
    chatgpt/
      client.py
    claude/
      client.py
    gemini/
      client.py

  outputs/
    google_docs/
      writer.py
    pdf/
      writer.py
    markdown/
      writer.py
    json/
      writer.py

  templates/
    minutes_default.md

  utils/
    audio.py
    file.py
```

🚀 Quick Start (MVP)
1. 会議テンプレ生成
`meetscribe init discord`

2. Discord 会議を録音・議事録化
`meetscribe run --config configs/discord.yaml`
3. Discord 会議を自動監視
`meetscribe daemon --config configs/discord.yaml`
⚙ Config Example
configs/discord.yaml

```yaml
meeting:
  source: discord
  channel_id: "1234"
  auto_join: false
  notify_only: true

pipeline:
  converter: whisper_api
  llm: notebooklm
  output: google_docs

auth:
  notebooklm:
    mode: apikey
    apikey: "${NLM_API_KEY}"

  chatgpt:
    key: "${OPENAI_API_KEY}"

  google_docs:
    service_account: "keys/google.json"
```

🧪 Status
MeetScribe は現在 v0.1 - Core Architecture Draft
主要機能は順次開発中。

 Directory design

 meeting_id 仕様

 Discord recorder

 Whisper converter

 NotebookLM / ChatGPT LLM clients

 Output renderers (Docs / PDF / MD)

 Daemon

 CLI

📜 License
Apache License 2.0

商用利用可能・特許保護・OSS適性が高い。

👥 Contributing
MeetScribe はオープンソースプロジェクトです。
Issue・PR・機能提案を歓迎します。

💡 Vision
「すべての会議から価値を生成する」
「会議は自動で終わる」
「会議内容はAIが統合し、ナレッジとして蓄積される」

MeetScribe は、そんな未来の Meeting OS を目指しています。
