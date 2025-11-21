---
description: Create a full GitHub template set inside .github/
---

タスク: .github/ ディレクトリ内に、プルリクエストおよびIssue（バグ報告、機能要求）のテンプレートファイル一式を作成してください。

以下の手順でタスクを遂行してください。

1. タスク内容（GitHubテンプレートファイルの作成）を理解する。
2. mainにチェックアウトし、pullを行い、最新のリモートの状態を取得する。
3. タスクの内容を元に、適切な命名でブランチを作成、チェックアウトする（例: feat/add-github-templates）。

4. 【重要】以下のファイルを.github/ディレクトリ内に作成する。　TDDができるようなテンプレートにすること

    - .github/PULL_REQUEST_TEMPLATE.md
    - .github/ISSUE_TEMPLATE.md

5. 作成したファイルを適切な粒度でコミットする。

6. テストとLintは不要。

7. 以下のルールに従ってPRを作成する。
    - PRのdescriptionのテンプレートは @.github/PULL_REQUEST_TEMPLATE.md を参照し、それに従うこと
    - PRのdescriptionのテンプレート内でコメントアウトされている箇所は必ず削除すること
    - PRのdescriptionにはCloses #$ARGUMENTSと記載すること