# MeetScribe ユーザーガイド

このガイドでは、MeetScribe を効果的に使用するために必要なすべての情報を説明します。

## 目次

- [はじめに](#はじめに)
- [インストール](#インストール)
- [クイックスタート](#クイックスタート)
- [設定](#設定)
- [ユースケース別ガイド](#ユースケース別ガイド)
- [Discord Daemon](#discord-daemon)
- [トラブルシューティング](#トラブルシューティング)
- [FAQ](#faq)
- [用語集](#用語集)

---

## はじめに

MeetScribe は、あらゆる Web 会議を自動で記録・文字起こしし、複数の LLM（NotebookLM / ChatGPT / Claude / Gemini など）を用いて議事録を生成する OSS パイプラインフレームワークです。

### 主な機能

- **マルチソース対応**: Discord、Zoom、Google Meet、WebRTC、ローカルファイルなど
- **複数の文字起こしエンジン**: Whisper API、faster-whisper、Deepgram、Gemini Audio
- **複数のLLMエンジン**: ChatGPT、Claude、Gemini、NotebookLM
- **柔軟な出力形式**: Markdown、PDF、JSON、Google Docs、Discord Webhook

---

## インストール

### 必要条件

- Python 3.9 以上
- ffmpeg（音声処理用）
- 各サービスの API キー（使用するサービスに応じて）

### pip でのインストール

```bash
pip install meetscribe
```

### ソースからのインストール

```bash
git clone https://github.com/m96-chan/MeetScribe.git
cd MeetScribe
pip install -e ".[all]"
```

### オプション依存関係のインストール

```bash
# 音声処理機能
pip install meetscribe[audio]

# Whisper API
pip install meetscribe[whisper]

# ローカル faster-whisper
pip install meetscribe[faster-whisper]

# すべての機能
pip install meetscribe[all]
```

### ffmpeg のインストール

ffmpeg は音声ファイルの処理に必要です。

**Windows:**
```bash
# winget を使用
winget install ffmpeg

# または Chocolatey を使用
choco install ffmpeg

# または https://ffmpeg.org/download.html からダウンロード
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install ffmpeg
```

### Docker での実行

```bash
# イメージのビルド
docker build -t meetscribe .

# 実行
docker run -v $(pwd)/meetings:/app/meetings meetscribe run --config config.yaml
```

---

## クイックスタート

### 1. 設定ファイルの作成

```bash
meetscribe init
```

これにより、デフォルト設定の `config.yaml` が作成されます。

### 2. 環境変数の設定

`.env` ファイルを作成します：

```bash
# OpenAI API キー（Whisper API や ChatGPT 用）
OPENAI_API_KEY=sk-your-key-here

# その他のサービス（必要に応じて）
ANTHROPIC_API_KEY=your-claude-key
GOOGLE_API_KEY=your-google-key
DEEPGRAM_API_KEY=your-deepgram-key
DISCORD_BOT_TOKEN=your-discord-bot-token
```

### 3. 最小構成での動作確認

音声ファイルから議事録を生成する最小構成：

```yaml
# config.yaml
input:
  provider: file
  params:
    audio_path: ./recording.mp3

convert:
  engine: whisper
  params:
    model: whisper-1
    language: ja

llm:
  engine: chatgpt
  params:
    model: gpt-4-turbo

output:
  format: markdown
  params:
    output_dir: ./meetings
```

### 4. パイプラインの実行

```bash
meetscribe run --config config.yaml
```

---

## 設定

### 基本構成

MeetScribe の設定ファイルは YAML 形式で、4つのメインセクションで構成されます：

```yaml
input:      # 入力ソースの設定
convert:    # 文字起こしエンジンの設定
llm:        # LLM エンジンの設定
output:     # 出力形式の設定
```

### 環境変数の展開

設定ファイル内で `${VAR_NAME}` を使用して環境変数を参照できます：

```yaml
llm:
  engine: chatgpt
  params:
    api_key: ${OPENAI_API_KEY}
```

### 複数出力の設定

複数の出力形式を同時に生成できます：

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

### 入力プロバイダー設定

#### ローカルファイル

```yaml
input:
  provider: file
  params:
    audio_path: ./recording.mp3
```

#### ディレクトリ（最新ファイルを処理）

```yaml
input:
  provider: file
  params:
    audio_path: ./recordings/
    pattern: "*.mp3"
```

#### ZIP アーカイブ

```yaml
input:
  provider: zip
  params:
    zip_path: ./meeting.zip
    mode: single  # または "multiple"
```

#### Google Meet (Drive)

```yaml
input:
  provider: meet
  params:
    download_dir: ./downloads
    keep_downloaded: true
```

#### OBS 録画

```yaml
input:
  provider: obs
  params:
    recording_dir: ./obs_recordings
    pattern: "*.mkv"
    extract_audio: true
```

### 変換エンジン設定

#### OpenAI Whisper API

```yaml
convert:
  engine: whisper
  params:
    model: whisper-1
    language: ja
    temperature: 0.0
```

#### ローカル faster-whisper

```yaml
convert:
  engine: faster-whisper
  params:
    model_size: large-v3
    device: cuda  # または "cpu"
    language: ja
    vad_filter: true
```

#### Deepgram

```yaml
convert:
  engine: deepgram
  params:
    model: nova-2
    diarize: true
    language: ja
```

#### パススルー（文字起こしなし）

LLM が直接音声を処理する場合：

```yaml
convert:
  engine: passthrough
  params:
    include_audio_info: true
```

### LLM エンジン設定

#### OpenAI ChatGPT

```yaml
llm:
  engine: chatgpt
  params:
    model: gpt-4-turbo
    temperature: 0.3
    max_tokens: 4096
```

#### Anthropic Claude

```yaml
llm:
  engine: claude
  params:
    model: claude-3-opus-20240229
    temperature: 0.3
```

#### Google Gemini

```yaml
llm:
  engine: gemini
  params:
    model: gemini-1.5-pro
    temperature: 0.3
```

#### NotebookLM

```yaml
llm:
  engine: notebooklm
  params:
    notebook_title_prefix: Meeting
```

### 出力フォーマット設定

#### Markdown

```yaml
output:
  format: markdown
  params:
    output_dir: ./meetings
    include_toc: true
    include_participants: true
    include_statistics: true
```

#### JSON

```yaml
output:
  format: json
  params:
    output_dir: ./meetings
    include_statistics: true
```

#### PDF

```yaml
output:
  format: pdf
  params:
    output_dir: ./meetings
    page_size: A4
    title_font_size: 16
    body_font_size: 11
```

#### Google Docs

```yaml
output:
  format: docs
  params:
    folder_id: your-folder-id
    share_with:
      - email@example.com
```

#### Discord Webhook

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

## ユースケース別ガイド

### ユースケース 1: ローカル音声ファイルから議事録を生成

最も基本的なユースケースです。録音済みの音声ファイルから議事録を生成します。

**設定ファイル:**

```yaml
input:
  provider: file
  params:
    audio_path: ./meeting_2024-01-15.mp3

convert:
  engine: whisper
  params:
    model: whisper-1
    language: ja

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

**実行:**

```bash
meetscribe run --config config.yaml
```

### ユースケース 2: Discord 会議の自動録音・議事録化

Discord のボイスチャンネルを監視し、会議を自動で録音・議事録化します。

**前提条件:**
- Discord Bot の作成と招待（後述の「Discord Daemon」セクション参照）

**設定ファイル:**

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
    language: ja

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

**Daemon として実行:**

```bash
meetscribe daemon --config config.yaml
```

### ユースケース 3: Google Meet 録画からの処理

Google Drive に保存された Google Meet 録画を処理します。

**設定ファイル:**

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

### ユースケース 4: 複数フォーマットでの同時出力

1回の処理で複数の形式で出力します。

**設定ファイル:**

```yaml
input:
  provider: file
  params:
    audio_path: ./recording.mp3

convert:
  engine: whisper
  params:
    model: whisper-1
    language: ja

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

### ユースケース 5: PDF/Google Docs への出力

フォーマルな議事録を PDF や Google Docs で作成します。

**PDF 出力:**

```yaml
output:
  format: pdf
  params:
    output_dir: ./meetings
    page_size: A4
    title_font_size: 18
    body_font_size: 11
    margin_top: 72
    margin_bottom: 72
```

**Google Docs 出力:**

```yaml
output:
  format: docs
  params:
    folder_id: "your-folder-id"
    share_with:
      - team@example.com
    notify: true
```

---

## Discord Daemon

### Discord Bot の作成

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」をクリック
3. アプリケーション名を入力
4. 「Bot」セクションで「Add Bot」をクリック
5. 「TOKEN」をコピーして環境変数に設定

### Bot の招待

以下の権限が必要です：
- Connect（ボイスチャンネルに接続）
- Speak（音声を送信）
- Use Voice Activity（音声アクティビティを使用）

招待 URL の生成:
1. 「OAuth2」→「URL Generator」
2. Scopes: `bot`
3. Bot Permissions: `Connect`, `Speak`, `Use Voice Activity`
4. 生成された URL でサーバーに招待

### Daemon の設定

```yaml
input:
  provider: discord
  params:
    bot_token: ${DISCORD_BOT_TOKEN}
    guild_id: "123456789"

daemon:
  mode: auto_record  # または "notify"
  guild_ids:
    - "123456789"
  channel_patterns:
    - "meeting-*"
    - "standup"
  min_users: 2
  max_silence: 300  # 5分間無音で終了
```

### Daemon モード

- `notify`: 会議開始時に通知のみ（録音しない）
- `auto_record`: 条件に合致するチャンネルに自動参加して録音

### Daemon の起動

```bash
meetscribe daemon --config config.yaml
```

---

## トラブルシューティング

### よくあるエラーと解決方法

#### "ffmpeg not found" エラー

ffmpeg がインストールされていないか、PATH に含まれていません。

**確認方法:**
```bash
ffmpeg -version
```

**解決方法:**
- [ffmpeg のインストール](#ffmpeg-のインストール) セクションを参照してインストール
- Windows の場合、システム環境変数の PATH に ffmpeg の bin ディレクトリを追加

#### "API key not set" エラー

API キーが設定されていません。

**確認方法:**
```bash
# Windows (PowerShell)
echo $env:OPENAI_API_KEY

# macOS/Linux
echo $OPENAI_API_KEY
```

**解決方法:**
1. `.env` ファイルに API キーを設定
2. または環境変数として直接設定:
   ```bash
   # Windows (PowerShell)
   $env:OPENAI_API_KEY = "sk-your-key-here"

   # macOS/Linux
   export OPENAI_API_KEY="sk-your-key-here"
   ```

#### "Audio file too large" エラー

音声ファイルが API の制限を超えています（Whisper API は 25MB まで）。

**解決方法:**
1. 音声ファイルを分割する
2. ローカルの faster-whisper を使用する:
   ```yaml
   convert:
     engine: faster-whisper
     params:
       model_size: large-v3
       vad_filter: true  # 無音部分を除去
   ```

#### "Rate limit exceeded" エラー

API のレート制限に達しました。

**解決方法:**
1. しばらく待ってから再試行
2. ローカルの文字起こしエンジンを使用:
   ```yaml
   convert:
     engine: faster-whisper
   ```

#### 文字化けが発生する

文字エンコーディングの問題です。

**解決方法:**
1. 設定ファイルを UTF-8 で保存
2. Windows の場合、PowerShell で文字コードを設定:
   ```powershell
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   ```

### ログの確認方法

```bash
# デバッグレベルでログを出力
meetscribe run --config config.yaml --log-level debug

# ログファイルの確認
cat ./meetings/meetscribe.log
```

### デバッグモード

詳細なログを出力するデバッグモード:

```bash
meetscribe run --config config.yaml --verbose
```

ドライラン（実際には処理を実行しない）:

```bash
meetscribe run --config config.yaml --dry-run
```

---

## FAQ

### Q: 対応している音声フォーマットは？

A: ffmpeg がサポートするほぼすべてのフォーマットに対応しています：
- MP3, WAV, M4A, FLAC, OGG, WebM, MP4, MKV など

### Q: 日本語の文字起こしはできますか？

A: はい、対応しています。`language: ja` を設定してください：
```yaml
convert:
  engine: whisper
  params:
    language: ja
```

### Q: オフラインで使用できますか？

A: ローカルの faster-whisper とオフライン対応の LLM を使用すれば可能です：
```yaml
convert:
  engine: faster-whisper
  params:
    model_size: large-v3
    device: cuda
```

### Q: 長時間（4時間以上）の会議を処理できますか？

A: はい、可能です。ただし以下を推奨します：
- ローカルの faster-whisper を使用（API 制限なし）
- `vad_filter: true` で無音部分を除去
- 十分なメモリとディスク容量を確保

### Q: 話者分離（話者ダイアライゼーション）はできますか？

A: はい、Deepgram を使用すると話者分離が可能です：
```yaml
convert:
  engine: deepgram
  params:
    diarize: true
```

### Q: 複数の会議を一括処理できますか？

A: ディレクトリを指定することで、複数のファイルを処理できます：
```yaml
input:
  provider: file
  params:
    audio_path: ./recordings/
    pattern: "*.mp3"
```

### Q: カスタムテンプレートは使えますか？

A: はい、Markdown テンプレートをカスタマイズできます。詳細は API リファレンスを参照してください。

### Q: コストを抑えるにはどうすればいいですか？

A: 以下の方法があります：
1. ローカルの faster-whisper を使用（無料）
2. Gemini Flash など低コストの LLM を使用
3. 短い会議では小さなモデルを使用

---

## 用語集

| 用語 | 説明 |
|------|------|
| **パイプライン** | 入力から出力までの処理フロー |
| **プロバイダー** | 入力ソースを取得するコンポーネント |
| **コンバーター** | 音声をテキストに変換するコンポーネント |
| **レンダラー** | 議事録を特定の形式で出力するコンポーネント |
| **Daemon** | バックグラウンドで動作する常駐プロセス |
| **文字起こし** | 音声をテキストに変換する処理 |
| **話者ダイアライゼーション** | 話者を識別して分離する処理 |
| **VAD** | Voice Activity Detection（音声活動検出） |
| **LLM** | Large Language Model（大規模言語モデル） |

---

## 次のステップ

- [API リファレンス](api-reference.md) - 詳細な API ドキュメント
- [アーキテクチャ](architecture.md) - システム設計の詳細
- [コントリビューションガイド](contributing.md) - 開発への参加方法
- [チュートリアル](tutorial.md) - ステップバイステップのチュートリアル
