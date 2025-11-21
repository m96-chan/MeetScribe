# Discord Webhook Renderer - 設計書

## 概要

Discord Webhook を使って、生成された議事録をDiscordチャンネルに自動投稿するOutputレンダラー。

### 設計原則
- **1ファイル1Webhook**: `discord_webhook_renderer.py` は1つのWebhookのみ扱う
- **Config で複数登録可能**: 複数のDiscord Webhookに投稿したい場合は、`outputs` 配列で複数定義

---

## 要件定義

### 機能要件

#### 1. Discord Webhook への投稿
- 議事録サマリーをDiscord Embedとして投稿
- 決定事項、アクションアイテム、キーポイントを整形して表示
- 色分けとアイコンで視認性を向上

#### 2. 複数Webhook対応（Config レベル）
```yaml
outputs:
  - format: discord_webhook
    params:
      webhook_url: "https://discord.com/api/webhooks/xxx/yyy"
      channel_name: "開発チーム"
      mention_roles: ["@dev-team"]

  - format: discord_webhook
    params:
      webhook_url: "https://discord.com/api/webhooks/aaa/bbb"
      channel_name: "経営陣"
      mention_roles: ["@executives"]
      include_action_items_only: true
```

#### 3. カスタマイズオプション
- **メンション**: 特定のロールやユーザーをメンション
- **フィルタリング**: アクションアイテムのみ投稿、など
- **カラー**: Embed の色をカスタマイズ
- **投稿形式**: 詳細版 or サマリー版

---

## アーキテクチャ設計

### クラス構造

```python
# meetscribe/outputs/discord_webhook_renderer.py

import requests
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from ..core.providers import OutputRenderer
from ..core.models import Minutes, Decision, ActionItem


logger = logging.getLogger(__name__)


class DiscordWebhookRenderer(OutputRenderer):
    """
    Discord Webhook OUTPUT レンダラー。

    議事録をDiscord Embedとして指定されたWebhookに投稿。
    1インスタンス = 1Webhook（複数Webhookはconfig で複数定義）
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Discord Webhook renderer.

        Config params:
            webhook_url: Discord Webhook URL (必須)
            bot_username: Webhookのユーザー名 (optional, default: "MeetScribe Bot")
            avatar_url: Webhookのアイコン画像URL (optional)
            channel_name: チャンネル表示名（ログ用、optional）
            mention_roles: メンションするロール ID のリスト (optional)
            mention_users: メンションするユーザー ID のリスト (optional)
            include_summary: サマリーを含める (default: True)
            include_decisions: 決定事項を含める (default: True)
            include_action_items: アクションアイテムを含める (default: True)
            include_key_points: キーポイントを含める (default: True)
            include_action_items_only: アクションアイテムのみ投稿 (default: False)
            embed_color: Embed の色 (16進数、default: 0x5865F2 Discord Blue)
            max_description_length: 説明の最大文字数 (default: 2048)
            max_fields: Embed field の最大数 (default: 25, Discord limit)
            add_notebooklm_link: NotebookLM URLをリンクとして追加 (default: True)
            timeout: リクエストタイムアウト秒数 (default: 10)
        """
        super().__init__(config)

        # 必須設定
        self.webhook_url = config.get('webhook_url')
        if not self.webhook_url:
            raise ValueError("webhook_url is required for DiscordWebhookRenderer")

        # 基本設定
        self.bot_username = config.get('bot_username', 'MeetScribe Bot')
        self.avatar_url = config.get('avatar_url')
        self.channel_name = config.get('channel_name', 'Discord')

        # メンション設定
        self.mention_roles = config.get('mention_roles', [])
        self.mention_users = config.get('mention_users', [])

        # 表示内容フィルター
        self.include_summary = config.get('include_summary', True)
        self.include_decisions = config.get('include_decisions', True)
        self.include_action_items = config.get('include_action_items', True)
        self.include_key_points = config.get('include_key_points', True)
        self.include_action_items_only = config.get('include_action_items_only', False)

        # スタイル設定
        self.embed_color = config.get('embed_color', 0x5865F2)  # Discord Blue
        self.max_description_length = config.get('max_description_length', 2048)
        self.max_fields = config.get('max_fields', 25)

        # その他
        self.add_notebooklm_link = config.get('add_notebooklm_link', True)
        self.timeout = config.get('timeout', 10)

    def render(self, minutes: Minutes, meeting_id: str) -> str:
        """
        議事録を Discord Webhook に投稿。

        Args:
            minutes: Minutes オブジェクト
            meeting_id: ミーティング識別子

        Returns:
            投稿成功時のWebhook URL

        Raises:
            requests.RequestException: Webhook投稿失敗
        """
        logger.info(f"Rendering Discord Webhook for {meeting_id} to {self.channel_name}")

        # Embed を構築
        embed = self._build_embed(minutes, meeting_id)

        # メンションテキストを構築
        content = self._build_mention_text()

        # Webhook ペイロードを構築
        payload = {
            'username': self.bot_username,
            'embeds': [embed]
        }

        if self.avatar_url:
            payload['avatar_url'] = self.avatar_url

        if content:
            payload['content'] = content

        # Webhook に投稿
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            logger.info(f"Successfully posted to Discord Webhook: {self.channel_name}")
            return self.webhook_url

        except requests.RequestException as e:
            logger.error(f"Failed to post to Discord Webhook: {e}")
            raise

    def _build_embed(self, minutes: Minutes, meeting_id: str) -> Dict[str, Any]:
        """
        Discord Embed を構築。

        Args:
            minutes: Minutes オブジェクト
            meeting_id: ミーティング識別子

        Returns:
            Discord Embed 辞書
        """
        embed = {
            'title': f'📝 議事録: {meeting_id}',
            'color': self.embed_color,
            'timestamp': minutes.generated_at.isoformat(),
            'footer': {
                'text': 'Generated by MeetScribe'
            }
        }

        # アクションアイテムのみモード
        if self.include_action_items_only:
            embed['description'] = self._truncate_text(
                f"**アクションアイテム ({len(minutes.action_items)}件)**",
                self.max_description_length
            )
            embed['fields'] = self._build_action_items_fields(minutes.action_items)
            return embed

        # 通常モード: サマリー
        if self.include_summary and minutes.summary:
            embed['description'] = self._truncate_text(
                minutes.summary,
                self.max_description_length
            )

        # Fields を構築
        fields = []

        # 決定事項
        if self.include_decisions and minutes.decisions:
            fields.extend(self._build_decisions_fields(minutes.decisions))

        # アクションアイテム
        if self.include_action_items and minutes.action_items:
            fields.extend(self._build_action_items_fields(minutes.action_items))

        # キーポイント
        if self.include_key_points and minutes.key_points:
            fields.extend(self._build_key_points_fields(minutes.key_points))

        # NotebookLM リンク
        if self.add_notebooklm_link and minutes.url:
            fields.append({
                'name': '🔗 NotebookLM',
                'value': f'[詳細を見る]({minutes.url})',
                'inline': False
            })

        # Discord の制限: 最大25フィールド
        embed['fields'] = fields[:self.max_fields]

        if len(fields) > self.max_fields:
            logger.warning(
                f"Embed has {len(fields)} fields, truncated to {self.max_fields}"
            )

        return embed

    def _build_decisions_fields(self, decisions: List[Decision]) -> List[Dict[str, Any]]:
        """決定事項のフィールドを構築"""
        if not decisions:
            return []

        fields = [{
            'name': f'✅ 決定事項 ({len(decisions)}件)',
            'value': '\n'.join(
                f"{i+1}. {d.description}" +
                (f" (担当: {d.responsible})" if d.responsible else "")
                for i, d in enumerate(decisions[:5])  # 最大5件
            ),
            'inline': False
        }]

        return fields

    def _build_action_items_fields(self, action_items: List[ActionItem]) -> List[Dict[str, Any]]:
        """アクションアイテムのフィールドを構築"""
        if not action_items:
            return []

        # 優先度別にソート
        priority_order = {'high': 0, 'medium': 1, 'low': 2, None: 3}
        sorted_items = sorted(
            action_items,
            key=lambda x: priority_order.get(x.priority, 3)
        )

        items_text = []
        for i, item in enumerate(sorted_items[:10]):  # 最大10件
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(item.priority, '⚪')

            text = f"{priority_emoji} {item.description}"
            if item.assignee:
                text += f" (担当: {item.assignee})"
            if item.deadline:
                text += f" [期限: {item.deadline}]"

            items_text.append(f"{i+1}. {text}")

        fields = [{
            'name': f'📋 アクションアイテム ({len(action_items)}件)',
            'value': '\n'.join(items_text),
            'inline': False
        }]

        return fields

    def _build_key_points_fields(self, key_points: List[str]) -> List[Dict[str, Any]]:
        """キーポイントのフィールドを構築"""
        if not key_points:
            return []

        fields = [{
            'name': f'💡 キーポイント ({len(key_points)}件)',
            'value': '\n'.join(
                f"• {point}" for point in key_points[:10]  # 最大10件
            ),
            'inline': False
        }]

        return fields

    def _build_mention_text(self) -> Optional[str]:
        """メンションテキストを構築"""
        mentions = []

        # ロールメンション
        for role_id in self.mention_roles:
            if role_id.startswith('@'):
                # @dev-team 形式の場合はそのまま
                mentions.append(role_id)
            else:
                # IDの場合は <@&ID> 形式
                mentions.append(f"<@&{role_id}>")

        # ユーザーメンション
        for user_id in self.mention_users:
            if user_id.startswith('@'):
                mentions.append(user_id)
            else:
                mentions.append(f"<@{user_id}>")

        return ' '.join(mentions) if mentions else None

    def _truncate_text(self, text: str, max_length: int) -> str:
        """テキストを切り詰める"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + '...'

    def validate_config(self) -> bool:
        """
        レンダラー設定を検証。

        Returns:
            True if config is valid

        Raises:
            ValueError: webhook_url が未設定
        """
        if not self.webhook_url:
            raise ValueError("webhook_url is required")

        if not self.webhook_url.startswith('https://discord.com/api/webhooks/'):
            logger.warning(
                f"webhook_url does not look like a Discord webhook: {self.webhook_url}"
            )

        return True
```

---

## 設定例

### 例1: 単一 Discord Webhook
```yaml
outputs:
  - format: discord_webhook
    params:
      webhook_url: "https://discord.com/api/webhooks/123456789/abcdefg"
      bot_username: "議事録Bot"
      channel_name: "開発チーム"
      mention_roles: ["@dev-team"]
      embed_color: 0x00FF00  # Green
```

### 例2: 複数 Discord Webhook（異なるチャンネル）
```yaml
outputs:
  # 詳細版: 開発チーム用
  - format: discord_webhook
    params:
      webhook_url: "https://discord.com/api/webhooks/111111/aaaaa"
      channel_name: "開発チーム"
      mention_roles: ["@dev-team"]
      include_summary: true
      include_decisions: true
      include_action_items: true
      include_key_points: true

  # サマリー版: 経営陣用（アクションアイテムのみ）
  - format: discord_webhook
    params:
      webhook_url: "https://discord.com/api/webhooks/222222/bbbbb"
      channel_name: "経営陣"
      mention_roles: ["@executives"]
      include_action_items_only: true
      embed_color: 0xFF0000  # Red
```

### 例3: NotebookLM + Discord Webhook
```yaml
outputs:
  - format: url
    params:
      save_metadata: true

  - format: discord_webhook
    params:
      webhook_url: "https://discord.com/api/webhooks/333333/ccccc"
      add_notebooklm_link: true
```

---

## Discord API 仕様

### Webhook POST エンドポイント
```
POST https://discord.com/api/webhooks/{webhook.id}/{webhook.token}
```

### ペイロード構造
```json
{
  "username": "MeetScribe Bot",
  "avatar_url": "https://example.com/avatar.png",
  "content": "<@&123456789> 議事録が生成されました",
  "embeds": [
    {
      "title": "📝 議事録: 2025-11-22T10-00_discord_channel1234",
      "description": "今日の開発MTGのサマリー",
      "color": 5814015,
      "timestamp": "2025-11-22T10:30:00Z",
      "fields": [
        {
          "name": "✅ 決定事項 (2件)",
          "value": "1. 新機能の実装を開始\n2. 来週リリース予定",
          "inline": false
        }
      ],
      "footer": {
        "text": "Generated by MeetScribe"
      }
    }
  ]
}
```

### Discord Embed 制限
- **Title**: 最大256文字
- **Description**: 最大4096文字（推奨2048文字）
- **Fields**: 最大25個
- **Field name**: 最大256文字
- **Field value**: 最大1024文字
- **Footer text**: 最大2048文字
- **合計文字数**: 6000文字まで

---

## エラーハンドリング

### 1. Webhook URL が無効
```python
ValueError: webhook_url is required
```

### 2. Webhook 投稿失敗
```python
requests.RequestException: HTTP 404 / 401 / 429
```
- **404**: Webhook が存在しない or 削除された
- **401**: Webhookトークンが無効
- **429**: Rate limit exceeded（1秒に30リクエストまで）

### 3. タイムアウト
```python
requests.Timeout: Request timed out after 10 seconds
```

---

## テスト戦略

### 単体テスト

#### Test 1: 基本的な Embed 構築
```python
def test_build_embed_basic():
    """基本的な Embed が正しく構築されることを確認"""
    config = {'webhook_url': 'https://discord.com/api/webhooks/test/test'}
    renderer = DiscordWebhookRenderer(config)

    minutes = create_mock_minutes()
    embed = renderer._build_embed(minutes, "test-meeting-id")

    assert embed['title'] == '📝 議事録: test-meeting-id'
    assert embed['color'] == 0x5865F2
    assert 'description' in embed
    assert 'fields' in embed
```

#### Test 2: アクションアイテムのみモード
```python
def test_action_items_only_mode():
    """include_action_items_only=True でアクションアイテムのみ表示"""
    config = {
        'webhook_url': 'https://discord.com/api/webhooks/test/test',
        'include_action_items_only': True
    }
    renderer = DiscordWebhookRenderer(config)

    minutes = create_mock_minutes()
    embed = renderer._build_embed(minutes, "test-meeting-id")

    assert 'アクションアイテム' in embed['description']
    assert len(embed['fields']) > 0
```

#### Test 3: メンションテキスト構築
```python
def test_mention_text_roles():
    """ロールメンションが正しく構築される"""
    config = {
        'webhook_url': 'https://discord.com/api/webhooks/test/test',
        'mention_roles': ['123456789', '@dev-team']
    }
    renderer = DiscordWebhookRenderer(config)

    mention_text = renderer._build_mention_text()

    assert '<@&123456789>' in mention_text
    assert '@dev-team' in mention_text
```

#### Test 4: Discord 制限の遵守
```python
def test_embed_respects_discord_limits():
    """Embed が Discord の制限を守る"""
    config = {'webhook_url': 'https://discord.com/api/webhooks/test/test'}
    renderer = DiscordWebhookRenderer(config)

    # 30個のフィールドを持つ Minutes
    minutes = create_minutes_with_many_fields(30)
    embed = renderer._build_embed(minutes, "test-meeting-id")

    # 最大25フィールドに制限される
    assert len(embed['fields']) <= 25
```

### 統合テスト

#### Test 5: Webhook 投稿（モック）
```python
@patch('requests.post')
def test_render_posts_to_webhook(mock_post):
    """Webhook に正しく投稿される"""
    mock_post.return_value.status_code = 204

    config = {'webhook_url': 'https://discord.com/api/webhooks/test/test'}
    renderer = DiscordWebhookRenderer(config)

    minutes = create_mock_minutes()
    result = renderer.render(minutes, "test-meeting-id")

    assert result == config['webhook_url']
    assert mock_post.called
    assert 'embeds' in mock_post.call_args[1]['json']
```

#### Test 6: エラーハンドリング
```python
@patch('requests.post')
def test_render_handles_webhook_error(mock_post):
    """Webhook エラー時に適切に例外を投げる"""
    mock_post.side_effect = requests.RequestException("404 Not Found")

    config = {'webhook_url': 'https://discord.com/api/webhooks/test/test'}
    renderer = DiscordWebhookRenderer(config)

    minutes = create_mock_minutes()

    with pytest.raises(requests.RequestException):
        renderer.render(minutes, "test-meeting-id")
```

---

## 依存関係

### 必須ライブラリ
```python
# requirements.txt に追加
requests>=2.31.0
```

### インポート
```python
import requests
from typing import Dict, Any, List, Optional
import logging
```

---

## Factory 統合

```python
# meetscribe/outputs/factory.py

def get_output_renderer(format_name: str, config: Dict[str, Any]) -> OutputRenderer:
    """Get OUTPUT renderer by name."""

    if format_name == 'url':
        from .url_renderer import URLRenderer
        return URLRenderer(config)

    elif format_name == 'discord_webhook':
        from .discord_webhook_renderer import DiscordWebhookRenderer
        return DiscordWebhookRenderer(config)

    # ... 他のレンダラー ...

    else:
        raise ValueError(f"Unsupported output format: {format_name}")
```

---

## 実装チェックリスト

- [ ] `DiscordWebhookRenderer` クラスの実装
- [ ] `_build_embed()` メソッドの実装
- [ ] `_build_decisions_fields()` の実装
- [ ] `_build_action_items_fields()` の実装（優先度ソート含む）
- [ ] `_build_key_points_fields()` の実装
- [ ] `_build_mention_text()` の実装
- [ ] `_truncate_text()` ヘルパーの実装
- [ ] `validate_config()` の実装
- [ ] Discord 制限（25フィールド、文字数）の遵守
- [ ] エラーハンドリング（requests.RequestException）
- [ ] `requirements.txt` に `requests` を追加
- [ ] `outputs/factory.py` に統合
- [ ] 単体テスト作成（6件以上）
- [ ] 統合テスト作成（モック使用）
- [ ] ドキュメント作成（設定例）

---

## 所要時間見積もり

- **クラス実装**: 2-3時間
- **Embed 構築ロジック**: 2-3時間
- **エラーハンドリング**: 1時間
- **テスト**: 2-3時間
- **ドキュメント**: 1時間
- **合計**: **8-11時間**

---

## メリット

1. **1ファイル1Webhook の原則**: シンプルでテストしやすい
2. **Config で複数登録可能**: 柔軟な運用（開発チーム + 経営陣など）
3. **Discord Embed 対応**: リッチな表示で視認性向上
4. **カスタマイズ可能**: メンション、色、フィルタリング等
5. **並列実行対応**: 複数Webhook への同時投稿が可能（Issue #200 の恩恵）

---

## 注意事項

### Rate Limit
- Discord Webhook は **1秒に30リクエストまで**
- 複数Webhook を並列実行する場合は問題なし（別々のWebhook URL）
- 同一Webhook に連続投稿する場合は注意（が、MeetScribeの用途では発生しない）

### Webhook のセキュリティ
- Webhook URL は秘密情報として扱う
- 環境変数または `.env` ファイルで管理
- GitHubにコミットしない

### Embed のベストプラクティス
- **Description**: 2048文字以内推奨
- **Fields**: 10個以内推奨（視認性のため）
- **Color**: ブランドカラーまたは優先度別

---

## 将来の拡張案

### Phase 2（オプション）
1. **スレッド対応**: 特定のDiscord スレッドに投稿
2. **添付ファイル**: PDFやMarkdownを添付
3. **ボタン/アクション**: Discord ボタンで NotebookLM を開く
4. **定期レポート**: 週次/月次サマリーを自動投稿

---

## 結論

この設計により、MeetScribe は Discord Webhook を使って議事録を自動投稿できるようになります。

**1ファイル1Webhook の原則**を守りつつ、**Config で複数登録可能**にすることで、シンプルさと柔軟性を両立しています。

Issue #200（複数出力対応）と組み合わせることで、複数のDiscordチャンネルへの並列投稿が実現できます。
