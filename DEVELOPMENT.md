# MeetScribe Development Guide

## Project Status (v0.1.0)

MeetScribeは現在、基本的なアーキテクチャとフレームワーク構造が完成しています。

### ✅ 完了済み

- [x] プロジェクト構造の設計と実装
- [x] 4層パイプライン構造（INPUT → CONVERT → LLM → OUTPUT）
- [x] コアデータモデル（Transcript, Minutes, AudioInfo, MeetingInfo）
- [x] 設定管理システム（YAML ベース）
- [x] Meeting ID生成システム
- [x] ベースプロバイダーインターフェース
- [x] CLIフレームワーク（run, daemon, init コマンド）
- [x] パイプラインランナー
- [x] ファクトリーパターンによるプロバイダー管理
- [x] 基本的なユニットテスト
- [x] セットアップファイル（setup.py, requirements.txt）
- [x] ドキュメント（README, 設計ドキュメント）

### 🚧 実装予定

#### Phase 1: INPUT Layer
- [ ] Discord BOT録音プロバイダー
- [ ] Zoom Cloud録音プロバイダー
- [ ] Google Meet録音プロバイダー
- [ ] ProcTap（ローカル録音）プロバイダー
- [ ] OBS録音プロバイダー

#### Phase 2: CONVERT Layer
- [ ] Whisper APIコンバーター
- [ ] faster-whisperコンバーター（ローカルGPU）
- [ ] Gemini Audioコンバーター
- [ ] Passthroughコンバーター

#### Phase 3: LLM Layer
- [ ] NotebookLMプロバイダー
- [ ] ChatGPTプロバイダー
- [ ] Claudeプロバイダー
- [ ] Geminiプロバイダー

#### Phase 4: OUTPUT Layer
- [ ] Markdownレンダラー
- [ ] JSONレンダラー
- [ ] PDFレンダラー
- [ ] Google Docsレンダラー
- [ ] NotebookLM URLレンダラー

#### Phase 5: Advanced Features
- [ ] Discord Daemon実装
- [ ] 音声前処理ユーティリティ
- [ ] 統合テスト
- [ ] Dockerコンテナ化
- [ ] CI/CD パイプライン

---

## Architecture Overview

```
meetscribe/
├── core/              # コア機能
│   ├── __init__.py
│   ├── models.py      # データモデル
│   ├── meeting_id.py  # Meeting ID生成
│   ├── config.py      # 設定管理
│   ├── providers.py   # ベースプロバイダー
│   └── runner.py      # パイプライン実行
├── inputs/            # INPUT層プロバイダー
│   ├── __init__.py
│   └── factory.py
├── converters/        # CONVERT層プロバイダー
│   ├── __init__.py
│   └── factory.py
├── llm/              # LLM層プロバイダー
│   ├── __init__.py
│   └── factory.py
├── outputs/          # OUTPUT層レンダラー
│   ├── __init__.py
│   └── factory.py
├── templates/        # テンプレート
│   └── __init__.py
├── utils/            # ユーティリティ
│   └── __init__.py
├── cli.py            # CLIエントリーポイント
└── init_templates.py # 初期化テンプレート
```

---

## Development Workflow

### 1. 新しいプロバイダーの追加

各層にプロバイダーを追加する場合：

#### 例: Discord INPUTプロバイダー

1. `meetscribe/inputs/discord_provider.py` を作成
2. `InputProvider` を継承
3. `record()` メソッドを実装
4. `meetscribe/inputs/factory.py` を更新

```python
# meetscribe/inputs/discord_provider.py
from pathlib import Path
from typing import Dict, Any
from ..core.providers import InputProvider

class DiscordProvider(InputProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bot_token = config['bot_token']
        self.channel_id = config['channel_id']

    def record(self, meeting_id: str) -> Path:
        # Discord録音ロジック
        pass
```

```python
# meetscribe/inputs/factory.py 内
from .discord_provider import DiscordProvider

def get_input_provider(provider_name: str, config: Dict[str, Any]) -> InputProvider:
    providers = {
        'discord': DiscordProvider,
        # ...
    }

    provider_class = providers.get(provider_name)
    if not provider_class:
        raise ValueError(f"Unsupported provider: {provider_name}")

    return provider_class(config)
```

### 2. テストの追加

```python
# tests/test_discord_provider.py
import pytest
from meetscribe.inputs.discord_provider import DiscordProvider

def test_discord_provider():
    config = {'bot_token': 'test', 'channel_id': '1234'}
    provider = DiscordProvider(config)
    assert provider.bot_token == 'test'
```

### 3. 実行

```bash
# テスト
pytest tests/test_discord_provider.py

# 実行
meetscribe run --config config.yaml
```

---

## Design Principles

1. **モジュール性**: すべてのコンポーネントは独立したプラグイン
2. **統一データモデル**: Transcriptがパイプラインを統一
3. **設定駆動**: YAMLでパイプラインを定義
4. **セキュリティ重視**: 機密データの自動削除オプション
5. **拡張性**: 新しいプロバイダーを簡単に追加可能

---

## Contributing

1. Issue を作成
2. フィーチャーブランチを作成
3. コードを実装
4. テストを追加
5. Pull Request を作成

詳細は [CONTRIBUTING.md](CONTRIBUTING.md) を参照（今後追加予定）

---

## Resources

- [Architecture Design](Claude.md)
- [Pipeline Specification](pipeline.md)
- [Design Principles](design_principles.md)
- [API Documentation](docs/) (今後追加予定)

---

## License

Apache License 2.0 - 商用利用可能・特許保護・OSS適性が高い
