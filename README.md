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

### ✔ 2. CONVERT 層（Transcription / Audio Handling 層）

CONVERT 層は「録音データを LLM が扱える形式に変換する」責務を持ち、  
必ずしも **音声 → テキスト化（Transcription）だけではない**。

MeetScribe の CONVERT 層は、次の2つの役割を兼ねる柔軟な層として設計されています。

#### **(A) 通常の音声 → テキスト変換（Transcription）**
Whisper / Gemini Audio / Deepgram などを用いて、  
録音した音声をテキスト化し、統一フォーマットの Transcript オブジェクトを返します。

- Whisper API（OpenAI Whisper-1）
- faster-whisper（ローカルGPU）
- Gemini 2 Flash Audio（高速・長時間対応）
- Deepgram（予定）

#### **(B) 音声をそのまま LLM に渡す「パススルー変換」**
NotebookLM や ChatGPT Audio のように、  
**音声ファイルそのものを LLM に渡せるケースでは、  
テキスト化をスキップ**して Transcript を生成します。

例：音声ファイルを NotebookLM の「音声ドキュメント」としてアップロード。

#### **Transcript オブジェクト（統一データモデル）**
CONVERT 層は最終的に必ず以下の統一データモデルを返します：

```json
{
  "text": "...",              # テキスト or None（パススルー時）
  "audio_path": "...",        # 音声ファイルパス
  "segments": [...],          # セグメント情報（任意）
  "audio_info": {...},        # 録音メタデータ（duration / codec など）
  "meeting_info": {...},      # 会議情報（source / participants など）
  "metadata": {...},          # コンバータ内部情報
  "processing_history": [...] # デバッグ用処理履歴
}
```
テキスト化した場合は text に内容が入る

テキスト化をスキップした場合は audio_path のみ

LLM 層はこの Transcript を共通入力として扱うため、
変換方式に依存しない一貫したパイプラインが構築できます

✔ 3. LLM 層（NotebookLM / ChatGPT / Gemini / Claude）
議事録生成エンジンを自由に選択：

NotebookLM（最強の議事録モデル）

ChatGPT (GPT-5 / GPT-o1) — 整形・Docs 生成に最適

Claude 3.7 — 構造化要約に強い

Gemini 2 Ultra / Flash — 高速・低コスト

共通 Minutes 形式に変換：

```json
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

### 1. インストール

```bash
# Clone repository
git clone https://github.com/yourusername/meetscribe.git
cd meetscribe

# Install dependencies
pip install -r requirements.txt

# または開発版インストール
pip install -e .
```

### 2. 環境変数の設定

```bash
# .env.example をコピー
cp .env.example .env

# .env ファイルを編集して API キーを設定
nano .env
```

### 3. 設定テンプレート生成

```bash
# Discord用の設定ファイルを生成
meetscribe init discord

# config_discord.yaml を編集
nano config_discord.yaml
```

### 4. パイプライン実行

```bash
# 会議を録音・議事録化
meetscribe run --config config_discord.yaml

# Discord 会議を自動監視（デーモンモード）
meetscribe daemon --config config_discord.yaml
```

### 5. テスト実行

```bash
# 単体テストを実行
pytest tests/

# カバレッジ付き
pytest --cov=meetscribe tests/
```
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
