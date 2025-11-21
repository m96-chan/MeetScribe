# MeetScribe Project Summary

## 📋 プロジェクト概要

**MeetScribe** は、あらゆるWeb会議を自動で記録・文字起こしし、複数のLLM（NotebookLM / ChatGPT / Claude / Gemini など）を用いて議事録を生成するOSSパイプラインフレームワークです。

### Version: 0.1.0 (Initial Framework)

---

## ✅ 実装済みコンポーネント

### コアアーキテクチャ
- ✅ 4層パイプライン構造（INPUT → CONVERT → LLM → OUTPUT）
- ✅ データモデル（Transcript, Minutes, AudioInfo, MeetingInfo, Segment）
- ✅ Meeting ID生成システム（`YYYY-MM-DDTHH-MM_<source>_<channel>`）
- ✅ YAML設定管理システム
- ✅ ベースプロバイダーインターフェース

### CLI
- ✅ `meetscribe run` - パイプライン実行
- ✅ `meetscribe daemon` - Discord監視（フレームワークのみ）
- ✅ `meetscribe init` - 設定テンプレート生成

### ファクトリーシステム
- ✅ INPUT層プロバイダーファクトリー
- ✅ CONVERT層プロバイダーファクトリー
- ✅ LLM層プロバイダーファクトリー
- ✅ OUTPUT層レンダラーファクトリー

### 設定テンプレート
- ✅ Discord設定テンプレート
- ✅ Zoom設定テンプレート
- ✅ Google Meet設定テンプレート
- ✅ ProcTap設定テンプレート
- ✅ OBS設定テンプレート

### テスト
- ✅ Meeting IDテスト
- ✅ データモデルテスト

### ドキュメント
- ✅ README.md（使い方ガイド）
- ✅ Claude.md（アーキテクチャ設計）
- ✅ architecture.md（システム構成）
- ✅ pipeline.md（パイプライン仕様）
- ✅ design_principles.md（設計原則）
- ✅ DEVELOPMENT.md（開発ガイド）

---

## 📂 プロジェクト構成

```
MeetScribe/
│
├── meetscribe/                    # メインパッケージ
│   ├── __init__.py
│   ├── cli.py                     # CLIエントリーポイント
│   ├── init_templates.py          # 初期化テンプレート
│   │
│   ├── core/                      # コアモジュール
│   │   ├── __init__.py
│   │   ├── models.py              # データモデル
│   │   ├── meeting_id.py          # Meeting ID生成
│   │   ├── config.py              # 設定管理
│   │   ├── providers.py           # ベースクラス
│   │   └── runner.py              # パイプライン実行
│   │
│   ├── inputs/                    # INPUT層
│   │   ├── __init__.py
│   │   └── factory.py
│   │
│   ├── converters/                # CONVERT層
│   │   ├── __init__.py
│   │   └── factory.py
│   │
│   ├── llm/                       # LLM層
│   │   ├── __init__.py
│   │   └── factory.py
│   │
│   ├── outputs/                   # OUTPUT層
│   │   ├── __init__.py
│   │   └── factory.py
│   │
│   ├── templates/                 # テンプレート
│   │   └── __init__.py
│   │
│   └── utils/                     # ユーティリティ
│       └── __init__.py
│
├── tests/                         # テストスイート
│   ├── __init__.py
│   ├── test_meeting_id.py
│   └── test_models.py
│
├── docs/                          # ドキュメント
│
├── .env.example                   # 環境変数サンプル
├── .gitignore                     # Git除外設定
├── config.example.yaml            # 設定サンプル
├── requirements.txt               # 依存パッケージ
├── setup.py                       # セットアップ設定
│
├── README.md                      # プロジェクト説明
├── Claude.md                      # アーキテクチャ設計
├── architecture.md                # システム構成
├── pipeline.md                    # パイプライン仕様
├── design_principles.md           # 設計原則
├── DEVELOPMENT.md                 # 開発ガイド
├── PROJECT_SUMMARY.md             # このファイル
│
└── LICENSE                        # Apache 2.0
```

---

## 🔧 使い方

### 1. インストール

```bash
git clone https://github.com/yourusername/meetscribe.git
cd meetscribe
pip install -r requirements.txt
pip install -e .
```

### 2. 設定

```bash
# 環境変数設定
cp .env.example .env
nano .env

# Discord設定テンプレート生成
meetscribe init discord
nano config_discord.yaml
```

### 3. 実行

```bash
# パイプライン実行
meetscribe run --config config_discord.yaml

# デーモンモード（今後実装）
meetscribe daemon --config config_discord.yaml
```

### 4. テスト

```bash
pytest tests/
pytest --cov=meetscribe tests/
```

---

## 🚀 次のステップ

### Phase 1: 基本プロバイダー実装
1. Discord INPUTプロバイダー
2. Whisper CONVERTプロバイダー
3. NotebookLM LLMプロバイダー
4. Markdown OUTPUTレンダラー

### Phase 2: 追加プロバイダー
5. Zoom / Google Meet INPUTプロバイダー
6. Gemini / faster-whisper CONVERTプロバイダー
7. ChatGPT / Claude LLMプロバイダー
8. PDF / Google Docs OUTPUTレンダラー

### Phase 3: 高度な機能
9. Discord Daemon実装
10. 音声前処理ユーティリティ
11. 統合テスト
12. Docker化

---

## 📊 実装状況

| レイヤー | 完了 | 予定 | 進捗 |
|---------|------|------|------|
| **コアアーキテクチャ** | ✅ | - | 100% |
| **CLI** | ✅ | - | 100% |
| **INPUT層** | 🚧 | 5 | 0% |
| **CONVERT層** | 🚧 | 4 | 0% |
| **LLM層** | 🚧 | 4 | 0% |
| **OUTPUT層** | 🚧 | 5 | 0% |
| **テスト** | 🚧 | 多数 | 20% |
| **ドキュメント** | ✅ | - | 100% |

---

## 🎯 コンセプト

### 設計原則
1. **モジュール性** - すべてのコンポーネントはプラグイン
2. **統一データモデル** - Transcriptがパイプラインを統一
3. **設定駆動** - YAMLでパイプラインを定義
4. **セキュリティ** - 機密データの自動削除
5. **拡張性** - 新しいプロバイダーを簡単に追加

### ビジョン
> "Turn every meeting into structured knowledge, automatically."

すべての会議から価値を生成し、会議内容をAIが統合してナレッジとして蓄積する、未来のMeeting OSを目指しています。

---

## 📜 ライセンス

Apache License 2.0 - 商用利用可能・特許保護・OSS適性が高い

---

## 👥 コントリビューション

Issue・PR・機能提案を歓迎します！

詳細は [DEVELOPMENT.md](DEVELOPMENT.md) を参照してください。

---

**作成日**: 2025-11-21
**バージョン**: 0.1.0
**ステータス**: Framework Ready - Provider Implementation Pending
