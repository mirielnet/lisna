# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
import re
import asyncio

class Timer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_time(self, time_str: str) -> int:
        """
        Parse a time string like '2m30s' into total seconds.
        Supports formats like '2m', '30s', '2m30s', etc.
        """
        minutes = 0
        seconds = 0
        time_regex = re.match(r"(?:(\d+)m)?(?:(\d+)s)?", time_str)
        
        if time_regex:
            if time_regex.group(1):  # Minutes part
                minutes = int(time_regex.group(1))
            if time_regex.group(2):  # Seconds part
                seconds = int(time_regex.group(2))

        return minutes * 60 + seconds

    @app_commands.command(name="timer", description="指定した時間後にメンションします。")
    @app_commands.describe(time="時間を指定してください。（例: 2m30s）")
    async def timer(self, interaction: discord.Interaction, time: str):
        total_seconds = self.parse_time(time)
        if total_seconds <= 0:
            await interaction.response.send_message("有効な時間を指定してください。", ephemeral=True)
            return

        await interaction.response.send_message(f"タイマーを {time} にセットしました。", ephemeral=True)
        
        await asyncio.sleep(total_seconds)
        await interaction.channel.send(f"{interaction.user.mention} タイマーが終了しました！")

async def setup(bot):
    await bot.add_cog(Timer(bot))
