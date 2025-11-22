# Docker Guide for MeetScribe

MeetScribeはDocker対応しており、環境依存を排除した簡単なデプロイが可能です。

## 🐳 クイックスタート

### 1. Dockerイメージのビルド

```bash
docker build -t meetscribe:latest .
```

### 2. Docker Composeで起動

```bash
# 環境変数を設定
cp .env.example .env
# .env ファイルを編集してAPIキーを設定

# コンテナを起動
docker-compose up -d

# ログを確認
docker-compose logs -f meetscribe
```

### 3. MeetScribeを実行

```bash
# ヘルプを表示
docker-compose run --rm meetscribe --help

# 設定ファイルを使用してパイプラインを実行
docker-compose run --rm meetscribe run --config /app/config.yaml
```

## 📦 イメージの詳細

### マルチステージビルド

MeetScribeのDockerfileはマルチステージビルドを採用しており、最終イメージサイズを最小化しています。

- **Builder Stage**: ビルド依存関係を含む
- **Runtime Stage**: 実行に必要な最小限の依存関係のみ

### ベースイメージ

- `python:3.11-alpine` - 軽量なAlpine Linuxベース

### イメージサイズ

最適化されたイメージサイズ: 約 **300-400MB**

## 🔧 使用方法

### 基本的な使い方

```bash
# パイプラインを実行
docker-compose run --rm meetscribe run --config /app/config.yaml

# Daemonモード
docker-compose run --rm meetscribe daemon --config /app/config.yaml

# 設定テンプレート生成
docker-compose run --rm meetscribe init discord
```

### ボリュームマウント

以下のディレクトリ/ファイルがマウントされます:

- `./meetings:/app/meetings` - 録音ファイルと議事録の保存先
- `./config.yaml:/app/config.yaml` - 設定ファイル
- `./google-credentials.json:/app/google-credentials.json` - Google認証情報

### 環境変数

`.env`ファイルまたは環境変数で設定:

```bash
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...
DISCORD_BOT_TOKEN=...
```

## 🛠️ 開発モード

開発モードでは、ローカルのコードが自動的にコンテナにマウントされます。

```bash
# 開発モードで起動
docker-compose --profile dev up -d meetscribe-dev

# コンテナ内でシェルを起動
docker-compose exec meetscribe-dev sh

# コンテナ内でテストを実行
docker-compose exec meetscribe-dev pytest tests/
```

## 🔐 セキュリティ

- **非rootユーザー**: コンテナは`meetscribe`ユーザー（UID 1000）で実行
- **読み取り専用マウント**: 設定ファイルと認証情報は読み取り専用でマウント
- **最小限の権限**: 必要最小限のパッケージのみインストール

## 📊 リソース制限

docker-compose.ymlでリソース制限を設定:

- **CPU**: 最大2コア、予約0.5コア
- **メモリ**: 最大2GB、予約512MB

必要に応じて調整してください:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 4G
```

## 🚀 本番環境での使用

### Docker Hub へのプッシュ (将来実装予定)

```bash
# タグ付け
docker tag meetscribe:latest yourusername/meetscribe:0.1.0
docker tag meetscribe:latest yourusername/meetscribe:latest

# プッシュ
docker push yourusername/meetscribe:0.1.0
docker push yourusername/meetscribe:latest
```

### Docker Hubからのプル (将来実装予定)

```bash
docker pull yourusername/meetscribe:latest
```

## 🧪 ヘルスチェック

コンテナのヘルスチェックが自動的に実行されます:

```bash
# ヘルスステータスを確認
docker inspect --format='{{.State.Health.Status}}' meetscribe
```

## 📝 トラブルシューティング

### イメージのビルドエラー

```bash
# キャッシュなしでビルド
docker build --no-cache -t meetscribe:latest .
```

### パーミッションエラー

```bash
# meetings ディレクトリの権限を確認
ls -la meetings/

# 必要に応じて権限を変更
chmod -R 755 meetings/
```

### コンテナのログ確認

```bash
# ログを表示
docker-compose logs -f meetscribe

# 最新100行のみ表示
docker-compose logs --tail=100 meetscribe
```

## 🔄 コンテナの管理

```bash
# コンテナを停止
docker-compose stop

# コンテナを削除
docker-compose down

# コンテナとボリュームを削除
docker-compose down -v

# すべてのコンテナを再起動
docker-compose restart
```

## 📚 参考資料

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Alpine Linux](https://alpinelinux.org/)
