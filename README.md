# Discord Bot for Fetching Zenn Articles
[![My Skills](https://skillicons.dev/icons?i=python,discord)](https://skillicons.dev)

このプロジェクトは、Zennの技術トレンド記事を取得し、指定されたDiscordチャンネルに投稿するDiscordボットです。

## 必要な環境変数

以下の環境変数を`.env`ファイルに設定してください：

- `DISCORD_BOT_TOKEN`: Discordボットのトークン
- `DISCORD_CHANNEL_ID`: メッセージを送信するDiscordチャンネルのID

## セットアップ

1. リポジトリをクローンします。
    ```sh
    git clone <リポジトリのURL>
    cd <リポジトリのディレクトリ>
    ```

2. 必要なパッケージをインストールします。
    ```sh
    pip install -r requirements.txt
    ```

3. `.env`ファイルを作成し、必要な環境変数を設定します。
    ```env
    DISCORD_BOT_TOKEN=your_discord_bot_token
    DISCORD_CHANNEL_ID=your_discord_channel_id
    ```

4. SQLiteデータベースを初期化します。
    ```sh
    python -c "import sqlite3; conn = sqlite3.connect('posted_articles.db'); c = conn.cursor(); c.execute('''CREATE TABLE IF NOT EXISTS articles (id TEXT PRIMARY KEY)'''); conn.commit(); conn.close()"
    ```

## 実行方法

以下のコマンドでボットを実行します。
```sh
python main.py