# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet) and tuna2134

import asyncio
import logging
import os
import secrets
import importlib.util
import inspect
from contextlib import asynccontextmanager

import aiofiles
import discord
import core.connect
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from jinja2 import Template

from version import BOT_VERSION
from core.bot import MWBot

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set intents
intents = discord.Intents.all()
intents.message_content = True

# Create bot instance
bot = MWBot(command_prefix="!", intents=intents)

# Basic authentication
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

# Global slash command registration
@bot.event
async def on_ready():
    update_status.start()
    logger.info(f"{bot.user}がDiscordに接続されました。")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandError):
        logger.error(f"Error in command {ctx.command}: {error}")

@tasks.loop(minutes=5)  # Every 5 minutes
async def update_status():
    server_count = len(bot.guilds)
    activity = discord.Game(name=f"/help / {BOT_VERSION} / {server_count} servers")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    logger.info(f"Status updated: {server_count} servers")

# Static files configuration
app.mount("/static", StaticFiles(directory="static"), name="static")

# /static/index.html endpoint
@app.get("/", response_class=HTMLResponse)
async def read_root():
    async with aiofiles.open("static/index.html", mode="r", encoding="utf-8") as f:
        return HTMLResponse(await f.read())

# /static/terms.txt endpoint
@app.get("/terms", response_class=PlainTextResponse)
async def read_terms():
    async with aiofiles.open("static/terms.txt", mode="r", encoding="utf-8") as f:
        return PlainTextResponse(await f.read())

# /admin/index.html endpoint with Basic Auth
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

# New endpoint to get all slash commands from ./cogs in JSON format
@app.get("/api/commands", response_class=JSONResponse)
async def get_commands():
    commands_list = []

    # Directory to scan for command cogs
    commands_folder = "./cogs"

    for file in os.listdir(commands_folder):
        if file.endswith(".py"):
            module_name = file[:-3]
            module_path = os.path.join(commands_folder, file)

            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for name, obj in vars(module).items():
                if inspect.isclass(obj) and issubclass(obj, commands.Cog):
                    cog = obj(bot)
                    for command in cog.__cog_app_commands__:
                        command_info = {
                            "name": command.name,
                            "description": command.description or "説明なし",
                        }
                        commands_list.append(command_info)

    return JSONResponse(content={"commands": commands_list})

# Start the bot
async def start_bot():
    await bot.start(TOKEN)

if __name__ == "__main__":
    import uvicorn

    # uvicorn.run(app, host="0.0.0.0", port=8000)
    bot.run(TOKEN)
