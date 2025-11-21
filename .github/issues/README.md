# Issue Batch Creation

このディレクトリにZIPファイルを配置すると、GitHub Actionsが自動的にIssueを作成します。

## 使い方

### 1. JSONファイルを作成

各IssueのデータをJSON形式で作成します。

**JSON構造例**:
```json
{
  "title": "[INPUT] Implement Discord PCM receiver with aligned frame buffers (Task 1)",
  "overview": "Implement detailed INPUT-layer functionality:\nImplement Discord PCM receiver with aligned frame buffers\n\nINPUT レイヤーの機能実装タスク。",
  "layer": "INPUT",
  "directory": "inputs/",
  "components": "input_component_1",
  "priority": "P0",
  "labels": [
    "feature",
    "input"
  ],
  "milestone": "v0.1",
  "tasks": [
    "[ ] Implement the functionality",
    "[ ] Add logging",
    "[ ] Add unit tests",
    "[ ] Validate with sample input",
    "[ ] Integrate with Runner pipeline",
    "[ ] Update documentation"
  ],
  "implementation_notes": "Must correctly implement: Implement Discord PCM receiver with aligned frame buffers",
  "acceptance_criteria": [
    "No runtime errors",
    "Passes unit tests",
    "Works in integrated pipeline",
    "Handles edge cases",
    "Documentation updated"
  ],
  "related_files": [
    "Claude.md",
    "architecture.md",
    "pipeline.md"
  ],
  "doc_references": "docs/input/task_1.md"
}
```

### 2. ZIPファイルを作成

複数のJSONファイルを1つのZIPファイルにまとめます。

```bash
# 例: 001_issue.json, 002_issue.json, ... をZIPに圧縮
zip meetscribe_batch1.zip *.json
```

### 3. ZIPを配置

作成したZIPファイルをこのディレクトリ (`.github/issues/`) に配置します。

```bash
# ZIPをコピー
cp meetscribe_batch1.zip .github/issues/

# Gitにコミット
git add .github/issues/meetscribe_batch1.zip
git commit -m "Add issue batch for processing"
git push
```

### 4. 自動処理

プッシュすると、GitHub Actionsが自動的に：

1. ZIPファイルを検出
2. 展開してJSONファイルを抽出
3. 各JSONからIssueを作成
4. 処理済みZIPを `processed/` フォルダにアーカイブ
5. コミット＆プッシュ

## フィールド説明

| フィールド | 必須 | 説明 |
|-----------|------|------|
| `title` | ✅ | Issueのタイトル |
| `overview` | ✅ | Issue概要（詳細説明） |
| `layer` | ❌ | レイヤー名 (INPUT, CONVERT, LLM, OUTPUT, CORE) |
| `directory` | ❌ | 実装ディレクトリ |
| `components` | ❌ | コンポーネント名 |
| `priority` | ❌ | 優先度 (P0, P1, P2) |
| `labels` | ❌ | ラベルの配列 |
| `milestone` | ❌ | マイルストーン名 |
| `tasks` | ❌ | タスクチェックリストの配列 |
| `implementation_notes` | ❌ | 実装メモ |
| `acceptance_criteria` | ❌ | 受入基準の配列 |
| `related_files` | ❌ | 関連ファイルの配列 |
| `doc_references` | ❌ | ドキュメント参照 |

## 作成されるIssueの例

```markdown
## Overview

Implement detailed INPUT-layer functionality:
Implement Discord PCM receiver with aligned frame buffers

INPUT レイヤーの機能実装タスク。

## Details

- **Layer**: INPUT
- **Directory**: `inputs/`
- **Components**: input_component_1
- **Priority**: P0
- **Milestone**: v0.1

## Tasks

- [ ] Implement the functionality
- [ ] Add logging
- [ ] Add unit tests
- [ ] Validate with sample input
- [ ] Integrate with Runner pipeline
- [ ] Update documentation

## Implementation Notes

Must correctly implement: Implement Discord PCM receiver with aligned frame buffers

## Acceptance Criteria

- No runtime errors
- Passes unit tests
- Works in integrated pipeline
- Handles edge cases
- Documentation updated

## Related Files

- `Claude.md`
- `architecture.md`
- `pipeline.md`

## Documentation

See: `docs/input/task_1.md`

---

*Auto-generated from: meetscribe_batch1.zip / 001_issue.json*
```

## トラブルシューティング

### Issueが作成されない

1. **GitHub Actionsのログを確認**
   - リポジトリの「Actions」タブで実行ログを確認

2. **JSON構文をチェック**
   ```bash
   # JSONが正しいか検証
   jq empty 001_issue.json
   ```

3. **パーミッション確認**
   - ワークフローが `issues: write` 権限を持っているか確認

### 手動実行

GitHub Actionsの「Workflow Dispatch」から手動で実行できます：

1. リポジトリの「Actions」タブを開く
2. 「Create Issues from ZIP」ワークフローを選択
3. 「Run workflow」をクリック

## ディレクトリ構造

```
.github/
└── issues/
    ├── README.md           # このファイル
    ├── *.zip              # 処理待ちZIPファイル（自動削除）
    └── processed/         # 処理済みアーカイブ
        └── 20251121_123456_meetscribe_batch1.zip
```

## 注意事項

- ZIPファイル名には半角英数字とアンダースコアを推奨
- 1つのZIPに含めるJSONは100個以下を推奨（API rate limit対策）
- 処理済みZIPは自動的に `processed/` に移動されます
- `[skip ci]` でコミットされるため、無限ループにはなりません

## 関連

- ワークフローファイル: [.github/workflows/issue_creator.yml](../workflows/issue_creator.yml)
- Issue YAML (旧形式): [issues.yaml](issues.yaml)
