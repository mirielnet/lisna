# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import glob
from version import BOT_VERSION
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from starlette.templating import Jinja2Templates

# .envファイルからトークンを読み込み
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# インテントの設定
intents = discord.Intents.default()
intents.message_content = True

# ボットのインスタンスを作成
bot = commands.Bot(command_prefix='!', intents=intents)

# コマンドのロード
async def load_commands():
    for filename in glob.glob('./commands/*.py'):
        if filename.endswith('.py') and not filename.endswith('__init__.py'):
            try:
                await bot.load_extension(f'commands.{os.path.basename(filename)[:-3]}')
            except Exception as e:
                print(f'Failed to load extension {filename}: {e}')

# グローバルスラッシュコマンドの登録
@bot.event
async def on_ready():
    # コマンドの同期と登録
    await bot.tree.sync()
    
    # グローバルコマンドの登録確認メッセージ
    print("グローバルコマンドが正常に登録されました。")

    # サーバー数を取得してステータスを設定
    server_count = len(bot.guilds)
    activity = discord.Game(name=f'{BOT_VERSION} / {server_count} servers')
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f'{bot.user}がDiscordに接続され、{server_count}サーバーに参加しています。')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandError):
        print(f'Error in command {ctx.command}: {error}')

# FastAPIアプリの作成
app = FastAPI()

# Jinja2テンプレートの設定
templates = Jinja2Templates(directory="templates")

# 静的ファイルの設定
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    server_count = len(bot.guilds)
    server_names = [guild.name for guild in bot.guilds]
    invite_link = None

    try:
        invite = await bot.get_invite(bot.user.id)
        invite_link = invite.url
    except:
        invite_link = "利用できません。"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "server_count": server_count,
        "server_names": server_names,
        "invite_link": invite_link
    })

# ボットの起動
async def main():
    async with bot:
        try:
            await load_commands()
            await bot.start(TOKEN)
        except Exception as e:
            print(f'Failed to start bot: {e}')

# FastAPIの起動
def run_web():
    uvicorn.run(app, host="0.0.0.0", port=8000)

import asyncio
import threading

# FastAPIを別スレッドで実行
web_thread = threading.Thread(target=run_web)
web_thread.start()

asyncio.run(main())
