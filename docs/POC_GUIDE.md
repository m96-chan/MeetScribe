# MeetScribe PoC Guide

このガイドでは、MeetScribeのProof of Concept（PoC）パイプラインを実行する手順を説明します。

## PoC パイプライン構成

```
File Input → Passthrough Converter → NotebookLM (Mock) → URL Display
```

### 各コンポーネント

1. **File INPUT Provider** - 既存の音声ファイルを入力として使用
2. **Passthrough CONVERT Provider** - 文字起こしをスキップし、音声をそのまま渡す
3. **NotebookLM LLM Provider** - NotebookLMノートブックを作成（モックモード対応）
4. **URL OUTPUT Renderer** - NotebookLM URLを表示し、メタデータを保存

## セットアップ手順

### 1. 依存パッケージのインストール

```bash
# プロジェクトルートディレクトリで実行
pip install -r requirements.txt

# 開発版インストール（推奨）
pip install -e .
```

### 2. サンプル音声ファイルの準備

以下のいずれかの方法で音声ファイルを用意します：

#### 方法A: 既存の音声ファイルを使用

```bash
# お持ちの音声ファイルを sample_audio.mp3 としてコピー
cp /path/to/your/audio.mp3 ./sample_audio.mp3
```

#### 方法B: テスト用ダミーファイルを作成（Windowsの場合）

```bash
# 空のMP3ファイルを作成（動作確認用）
echo "dummy audio data" > sample_audio.mp3
```

サポートされる形式: MP3, M4A, WAV, FLAC

### 3. 設定ファイルの編集

[config.poc.yaml](config.poc.yaml)を開いて、音声ファイルのパスを確認・更新します：

```yaml
input:
  provider: file
  params:
    audio_path: "./sample_audio.mp3"  # ← 実際のパスに変更
```

## PoC実行

### 基本実行

```bash
meetscribe run --config config.poc.yaml
```

### 期待される出力

```
2025-11-21 16:00:00 - meetscribe.core.runner - INFO - Loading config: config.poc.yaml
2025-11-21 16:00:00 - meetscribe.core.runner - INFO - Initializing pipeline...
2025-11-21 16:00:00 - meetscribe.core.runner - INFO - Stage 1/4: INPUT - Recording audio...
2025-11-21 16:00:00 - meetscribe.inputs.file_provider - INFO - Using audio file: ./sample_audio.mp3
2025-11-21 16:00:00 - meetscribe.core.runner - INFO - Audio recorded: ./sample_audio.mp3

2025-11-21 16:00:00 - meetscribe.core.runner - INFO - Stage 2/4: CONVERT - Transcribing audio...
2025-11-21 16:00:00 - meetscribe.converters.passthrough_converter - INFO - Passthrough mode: skipping transcription
2025-11-21 16:00:00 - meetscribe.core.runner - INFO - Transcription complete: 0 chars

2025-11-21 16:00:00 - meetscribe.core.runner - INFO - Stage 3/4: LLM - Generating minutes...
2025-11-21 16:00:00 - meetscribe.llm.notebooklm_provider - INFO - Initializing NotebookLM client (PoC mode)
2025-11-21 16:00:00 - meetscribe.llm.notebooklm_provider - INFO - Creating NotebookLM notebook: PoC Meeting - 2025-11-21T16-00_file_sample_audio
2025-11-21 16:00:00 - meetscribe.llm.notebooklm_provider - INFO - [MOCK] Uploading audio...
2025-11-21 16:00:00 - meetscribe.llm.notebooklm_provider - INFO - [MOCK] Generating analysis...
2025-11-21 16:00:00 - meetscribe.core.runner - INFO - Minutes generated: 150 chars

2025-11-21 16:00:00 - meetscribe.core.runner - INFO - Stage 4/4: OUTPUT - Rendering output...
================================================================================
NotebookLM URL: https://notebooklm.google.com/notebook/nb_1_20251121160000
================================================================================
2025-11-21 16:00:00 - meetscribe.outputs.url_renderer - INFO - Metadata saved to: ./meetings/.../meeting_info.json

Success! Output available at:
./meetings/2025-11-21T16-00_file_sample_audio/meeting_info.json
```

### 生成されるファイル

```
meetings/
└── 2025-11-21T16-00_file_sample_audio/
    └── meeting_info.json
```

**meeting_info.json** の内容例：

```json
{
  "meeting_id": "2025-11-21T16-00_file_sample_audio",
  "notebooklm_url": "https://notebooklm.google.com/notebook/nb_1_20251121160000",
  "summary": "This is a mock meeting summary...",
  "decisions_count": 1,
  "action_items_count": 2,
  "key_points_count": 4,
  "participants": [],
  "generated_at": "2025-11-21T16:00:00",
  "metadata": {
    "llm_engine": "notebooklm",
    "notebook_title": "PoC Meeting - 2025-11-21T16-00_file_sample_audio",
    "has_audio": true,
    "has_transcript": false
  }
}
```

## トラブルシューティング

### エラー: `FileNotFoundError: Audio file not found`

音声ファイルのパスが正しいか確認してください：

```bash
ls -l sample_audio.mp3
```

設定ファイル内のパスを絶対パスに変更してみてください：

```yaml
audio_path: "C:/Users/your-name/path/to/audio.mp3"
```

### エラー: `ModuleNotFoundError: No module named 'meetscribe'`

パッケージがインストールされていません：

```bash
pip install -e .
```

### エラー: パイプラインが実行されない

Pythonパスを確認してください：

```bash
# Windows
python -m meetscribe.cli run --config config.poc.yaml

# または
python meetscribe/cli.py run --config config.poc.yaml
```

## 次のステップ

PoC動作確認後、以下の実装に進むことができます：

1. **実際のDiscord録音プロバイダー** - Discord BOTによる音声録音
2. **Whisper文字起こし** - OpenAI Whisper APIによる文字起こし
3. **本番NotebookLM連携** - 実際のNotebookLM APIとの接続
4. **追加の出力形式** - Markdown、PDF、Google Docs

詳細は [DEVELOPMENT.md](DEVELOPMENT.md) を参照してください。

## モックモードについて

現在のPoCでは、NotebookLM APIの代わりにモッククライアントを使用しています。

実際のNotebookLM APIを使用する場合：

1. NotebookLM APIキーを取得
2. `.env`ファイルにキーを設定
3. `config.poc.yaml`でAPIキーを指定
4. `notebooklm_provider.py`の`MockNotebookLMClient`を実際のSDKに置き換え

---

**質問・フィードバック**: [GitHub Issues](https://github.com/yourusername/meetscribe/issues)
