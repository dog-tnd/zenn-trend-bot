import os
import discord
import aiohttp
import asyncio
from dotenv import load_dotenv
import sqlite3

# 環境変数を読み込む
load_dotenv()

# SQLiteデータベースを初期化
conn = sqlite3.connect('posted_articles.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS articles
             (id TEXT PRIMARY KEY)''')
conn.commit()

# メッセージを送信するチャンネルID
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))


async def fetch_and_send_updates():
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'{client.user} has connected to Discord!')
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://zenn-api.vercel.app/api/trendTech') as response:
                    if response.status == 200:
                        data = await response.json()
                        posted_count = 0
                        for article in data:
                            article_id = article['id']
                            c.execute(
                                "SELECT * FROM articles WHERE id=?", (article_id,))
                            if c.fetchone() is None and posted_count < 10:
                                title = article['title']
                                path = article['path']
                                message = f"新たな記事「{title}」が投稿されました。\nhttps://zenn.dev/{path}\n\n"
                                await channel.send(message)
                                c.execute(
                                    "INSERT INTO articles VALUES (?)", (article_id,))
                                conn.commit()
                                posted_count += 1

                        if posted_count == 0:
                            print("新しい記事はありません。")
                    else:
                        print("APIからデータを取得できませんでした。")
        else:
            print(f"Channel with ID {CHANNEL_ID} not found")

        await client.close()

    await client.start(os.getenv('DISCORD_BOT_TOKEN'))

if __name__ == "__main__":
    asyncio.run(fetch_and_send_updates())
