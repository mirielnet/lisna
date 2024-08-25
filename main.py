# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet) and tuna2134

import asyncio
import logging
import os
import secrets
from contextlib import asynccontextmanager

import aiofiles
import discord
import core.connect
from discord.ext import commands, tasks
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from jinja2 import Template

from version import BOT_VERSION
from core.bot import MWBot

# .envファイルからトークンと管理者のユーザー名とパスワードを読み込み
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# ロギングの設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# インテントの設定
intents = discord.Intents.all()
intents.message_content = True

# ボットのインスタンスを作成
bot = MWBot(command_prefix="!", intents=intents)

# Basic認証の設定
security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(start_bot())
    yield

app = FastAPI(lifespan=lifespan)

# グローバルスラッシュコマンドの登録
@bot.event
async def on_ready():
    # ステータス更新タスクを開始
    update_status.start()

    logger.info(f"{bot.user}がDiscordに接続されました。")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandError):
        logger.error(f"Error in command {ctx.command}: {error}")

@tasks.loop(minutes=5)  # 5分ごとに実行
async def update_status():
    # サーバー数を取得してステータスを設定
    server_count = len(bot.guilds)
    activity = discord.Game(name=f"/help / {BOT_VERSION} / {server_count} servers")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    logger.info(f"ステータスが更新されました: {server_count}サーバー")

# 静的ファイルの設定
app.mount("/static", StaticFiles(directory="static"), name="static")

# /static/index.htmlを表示するエンドポイント
@app.get("/", response_class=HTMLResponse)
async def read_root():
    async with aiofiles.open("static/index.html", mode="r", encoding="utf-8") as f:
        return HTMLResponse(await f.read())

# /static/terms.txtを表示するエンドポイント
@app.get("/terms", response_class=PlainTextResponse)
async def read_root():
    async with aiofiles.open("static/terms.txt", mode="r", encoding="utf-8") as f:
        return PlainTextResponse(await f.read())

# /admin/index.htmlを表示するエンドポイント
@app.get("/admin/", response_class=HTMLResponse, dependencies=[Depends(authenticate)])
async def read_index(request: Request):
    guilds_info = []
    for guild in bot.guilds:
        icon_url = guild.icon.url if guild.icon else "https://via.placeholder.com/100"
        owner = await bot.fetch_user(guild.owner_id)
        invite_url = await get_existing_invite(guild)
        guilds_info.append(
            {
                "name": guild.name,
                "icon_url": icon_url,
                "owner_name": owner.name,
                "invite_url": invite_url,
            }
        )

    async with aiofiles.open("static/admin/index.html", mode="r", encoding="utf-8") as f:
        template = Template(await f.read())
    content = template.render(server_count=len(bot.guilds), guilds=guilds_info)
    return HTMLResponse(content=content)

async def get_existing_invite(guild):
    for channel in guild.text_channels:
        try:
            invites = await channel.invites()
            for invite in invites:
                if invite.inviter.id == bot.user.id:
                    return invite.url
        except discord.Forbidden:
            continue
    return await create_invite(guild)

async def create_invite(guild):
    for channel in guild.text_channels:
        try:
            invite = await channel.create_invite(max_age=0, max_uses=0)
            return invite.url
        except discord.Forbidden:
            continue
    return "招待リンクを作成できませんでした。"

# ボットの起動
async def start_bot():
    await bot.start(TOKEN)

if __name__ == "__main__":
    import uvicorn

    # uvicorn.run(app, host="0.0.0.0", port=8000)
    bot.run(TOKEN)
