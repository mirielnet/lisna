# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
import asyncio

class BumpNotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.process_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        await self.process_message(after)

    async def process_message(self, message: discord.Message):
        if not message.guild:
            return  # Ensure the message is from a guild (server)

        # DIS速 bot check
        if message.author.id == 981314695543783484:  # Replace with DIS速 bot ID
            if message.embeds:
                embed = message.embeds[0]  # Get the first embed
                if embed.author and embed.author.name and "アップしたよ" in embed.author.name:
                    await self.send_initial_notification(
                        message.channel, "UP通知", "UPを受信しました\n1時間後に通知します"
                    )
                    await self.send_bump_notification(
                        message.channel, 3600, "UPの時間です\n</up:1135405664852783157>でサーバーの表示順位を上げよう！"
                    )

        # DISBOARD bot check
        elif message.author.id == 302050872383242240:  # DISBOARD bot ID
            if message.embeds:
                embed = message.embeds[0]  # Get the first embed
                if embed.description and any(phrase in embed.description for phrase in ["表示順をアップしたよ", "Bump done"]):
                    await self.send_initial_notification(
                        message.channel, "BUMP通知", "BUMPを受信しました\n2時間後に通知します"
                    )
                    await self.send_bump_notification(
                        message.channel, 7200, "BUMPの時間です\n</bump:947088344167366698>でサーバーの表示順位を上げよう！"
                    )

    async def send_initial_notification(self, channel, title, description):
        try:
            await channel.send(embed=discord.Embed(
                title=title,
                description=description,
                color=discord.Color.default()  # Use default color
            ))
        except discord.Forbidden:
            print(f"Cannot send messages in {channel.name} due to lack of permissions")

    async def send_bump_notification(self, channel, delay, reminder_text):
        try:
            await asyncio.sleep(delay)
            await channel.send(embed=discord.Embed(
                title="BUMP通知" if "BUMPの時間" in reminder_text else "UP通知",
                description=reminder_text,
                color=discord.Color.green()  # Use green color for bump notification
            ))
        except discord.Forbidden:
            print(f"Cannot send messages in {channel.name} due to lack of permissions")

async def setup(bot):
    await bot.add_cog(BumpNotify(bot))
