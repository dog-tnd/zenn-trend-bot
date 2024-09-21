import json
import os
import discord
from discord.ext import commands
import aiohttp
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, jsonify

import threading
import asyncio
from dotenv import load_dotenv

print(os.getcwd())

# 環境変数を読み込む
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
PASS_FIREBASE = os.getenv('PASS_FIREBASE')


# Firebase用のライブラリをインポート、FirebaseAppを初期化
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
cred = credentials.Certificate(PASS_FIREBASE)
app = firebase_admin.initialize_app(cred)
db = firestore.client()

# Discord Botの設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Flaskアプリの設定
app = Flask(__name__)

# Flaskのルート設定（ステータス確認など）
@app.route('/')
def home():
    return "This is the homepage of the Flask server running alongside the Discord bot!"

@app.route('/status')
def status():
    return jsonify({
        "bot_status": "running",
        "guild_count": len(bot.guilds),
        "user_count": sum(guild.member_count for guild in bot.guilds)
    })

# 新しい記事をチェックして送信
async def fetch_and_send_updates():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://zenn-api.vercel.app/api/trendTech') as response:
                if response.status == 200:
                    data = await response.json()
                    posted_count = 0
                    for article in data:
                        article_id = article['id']
                        ref = db.collection(u'articles')
                        doc = ref.where(filter=firestore.FieldFilter("id", "==", article_id))
                        count_doc = doc.count().get()[0][0].value
                        if count_doc == 0 and posted_count < 10:
                            title = article['title']
                            path = article['path']
                            message = f"新たな記事「{title}」が投稿されました。\nhttps://zenn.dev/{path}\n\n"
                            await channel.send(message)
                            posted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            ref.document(str(article_id)).set({
                                "id": article_id,
                                "posted_at": posted_at
                            })
                            print(f"{posted_at}:「{title}」を送信しました")
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
    ref = db.collection(u'articles')
    docs = ref.where(filter=firestore.FieldFilter("posted_at", "<", one_week_ago_str)).get()
    for doc in docs:
        doc.delete()

# 10分ごとにチェックと削除を行うバックグラウンドタスク
async def background_task():
    while True:
        await fetch_and_send_updates()
        remove_old_articles()
        await asyncio.sleep(600)

# Flaskをバックグラウンドで実行するためのスレッド
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# Discordのon_readyイベント
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    # バックグラウンドタスクを起動
    bot.loop.create_task(background_task())

# メイン関数でFlaskサーバーとDiscordボットの両方を起動
if __name__ == "__main__":
    # Flaskを別スレッドで起動
    threading.Thread(target=run_flask).start()

    # Discordボットを実行
    bot.run(DISCORD_TOKEN)
