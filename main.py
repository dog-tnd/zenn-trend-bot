import os
import discord
import aiohttp
import asyncio
from dotenv import load_dotenv
import sqlite3
from datetime import datetime, timedelta

# 環境変数を読み込む
load_dotenv()

# SQLiteデータベースを初期化
conn = sqlite3.connect('posted_articles.db')
c = conn.cursor()
# 記事テーブルに日時カラムを追加
c.execute('''CREATE TABLE IF NOT EXISTS articles
             (id TEXT PRIMARY KEY, posted_at TEXT)''')
conn.commit()

# メッセージを送信するチャンネルID
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))


# 新しい記事をチェックして送信
async def fetch_and_send_updates(client):
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://zenn-api.vercel.app/api/trendTech') as response:
                if response.status == 200:
                    data = await response.json()
                    posted_count = 0
                    for article in data:
                        article_id = article['id']
                        # 記事IDが既にデータベースに存在するかチェック
                        c.execute(
                            "SELECT * FROM articles WHERE id=?", (article_id,))
                        if c.fetchone() is None and posted_count < 1:  # テスト用に1つの記事のみ送信
                            title = article['title']
                            path = article['path']
                            message = f"新たな記事「{
                                title}」が投稿されました。\nhttps://zenn.dev/{path}\n\n"
                            await channel.send(message)
                            # 現在時刻を記録
                            posted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            c.execute(
                                "INSERT INTO articles VALUES (?, ?)", (article_id, posted_at))
                            conn.commit()
                            posted_count += 1

                    if posted_count == 0:
                        print("新しい記事はありません。")
                else:
                    print("APIからデータを取得できませんでした。")
    else:
        print(f"Channel with ID {CHANNEL_ID} not found")


# 1週間以上経ったデータを削除
def remove_old_articles():
    one_week_ago = datetime.now() - timedelta(days=7)
    one_week_ago_str = one_week_ago.strftime('%Y-%m-%d %H:%M:%S')
    c.execute("DELETE FROM articles WHERE posted_at < ?", (one_week_ago_str,))
    conn.commit()


# 10分ごとにチェックと削除を行うバックグラウンドタスク
async def background_task(client):
    while True:
        await fetch_and_send_updates(client)
        remove_old_articles()  # 古い記事を削除
        # 10分間スリープ (10分 = 600秒)
        await asyncio.sleep(10)  # テスト用に10秒に変更


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@ client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    # バックグラウンドタスクを起動
    client.loop.create_task(background_task(client))


if __name__ == "__main__":
    client.run(os.getenv('DISCORD_BOT_TOKEN'))
