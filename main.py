# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet) and tuna2134

import discord
import logging
import os
import asyncio
import core.webservice as webservice  # FastAPI appをインポート
from dotenv import load_dotenv
import core.connect
from discord.ext import commands, tasks
from core.bot import MWBot
import uvicorn

# 環境変数の読み込み
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Discordボットの設定
intents = discord.Intents.all()
bot = MWBot(command_prefix="!", intents=intents)

# ボットが接続したときのイベント
@bot.event
async def on_ready():
    update_status.start()
    logger.info(f"{bot.user}がDiscordに接続されました。")

# ステータス更新タスク
@tasks.loop(minutes=5)
async def update_status():
    server_count = len(bot.guilds)
    activity = discord.Game(name=f"/help / {server_count} servers")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    logger.info(f"Status updated: {server_count} servers")

# FastAPIのアプリケーション
app = webservice.app  # FastAPI appをエイリアス

# FastAPIサーバーを起動するための関数
def start_webserver():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    return server.serve()

# Discordボットを起動するための非同期関数
async def start_bot():
    await bot.start(TOKEN)

# 両方のサービスを同時に起動する
async def start_services():
    await asyncio.gather(
        start_bot(),          # Discordボットの起動
        start_webserver()     # FastAPIサーバーの起動
    )

if __name__ == "__main__":
    asyncio.run(start_services())  # メインイベントループで両方のタスクを実行
