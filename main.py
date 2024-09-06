# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet) and tuna2134

import discord
import logging
import os
import asyncio
import core.webservice as webservice  # Import the new webservice module
from dotenv import load_dotenv
import core.connect
from discord.ext import commands, tasks
from core.bot import MWBot

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create bot instance
intents = discord.Intents.all()
bot = MWBot(command_prefix="!", intents=intents)

# Event to trigger when bot is ready
@bot.event
async def on_ready():
    update_status.start()
    logger.info(f"{bot.user}がDiscordに接続されました。")

@tasks.loop(minutes=5)
async def update_status():
    server_count = len(bot.guilds)
    activity = discord.Game(name=f"/help / {BOT_VERSION} / {server_count} servers")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    logger.info(f"Status updated: {server_count} servers")

# Start bot and webserver
async def start_services():
    await asyncio.gather(
        bot.start(TOKEN),
        webservice.app.router.start(bot=bot)  # Pass bot to the webservice
    )

if __name__ == "__main__":
    asyncio.run(start_services())