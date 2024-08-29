# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from core.connect import db  # Import the PostgresConnection

class BumpNotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_notifications()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.resume_notifications()

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
                if embed.description and "アップしたよ" in embed.description:
                    await self.send_initial_notification(
                        message.channel, "UP通知", "UPを受信しました\n1時間後に通知します"
                    )
                    self.schedule_notification(
                        message.channel.id, "UP通知", 3600, "UPの時間です\n</up:1135405664852783157>でサーバーの表示順位を上げよう！"
                    )

        # DISBOARD bot check
        elif message.author.id == 302050872383242240:  # DISBOARD bot ID
            if message.embeds:
                embed = message.embeds[0]  # Get the first embed
                if embed.description and any(phrase in embed.description for phrase in ["表示順をアップしたよ", "Bump done"]):
                    await self.send_initial_notification(
                        message.channel, "BUMP通知", "BUMPを受信しました\n2時間後に通知します"
                    )
                    self.schedule_notification(
                        message.channel.id, "BUMP通知", 7200, "BUMPの時間です\n</bump:947088344167366698>でサーバーの表示順位を上げよう！"
                    )

    def schedule_notification(self, channel_id, title, delay, reminder_text):
        notify_time = datetime.now() + timedelta(seconds=delay)
        query = """
            INSERT INTO notifications (channel_id, title, notify_time, reminder_text)
            VALUES (%s, %s, %s, %s)
        """
        db.execute_query(query, (channel_id, title, notify_time, reminder_text))
    
    async def resume_notifications(self):
        query = "SELECT channel_id, title, notify_time, reminder_text FROM notifications"
        rows = db.execute_query(query)
        if rows:
            for row in rows:
                channel_id, title, notify_time, reminder_text = row
                delay = (notify_time - datetime.now()).total_seconds()
                if delay > 0:
                    await self.defer_and_notify(channel_id, delay, reminder_text)
                else:
                    channel = self.bot.get_channel(channel_id)
                    await self.send_bump_notification(channel, reminder_text)

    async def send_initial_notification(self, channel, title, description):
        try:
            await channel.send(embed=discord.Embed(
                title=title,
                description=description,
                color=discord.Color.default()  # Use default color
            ))
        except discord.Forbidden:
            print(f"Cannot send messages in {channel.name} due to lack of permissions")

    async def defer_and_notify(self, channel_id, delay, reminder_text):
        await asyncio.sleep(delay)
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.trigger_typing()
            await asyncio.sleep(5)
            await self.send_bump_notification(channel, reminder_text)

    async def send_bump_notification(self, channel, reminder_text):
        try:
            await channel.send(embed=discord.Embed(
                title="BUMP通知" if "BUMPの時間" in reminder_text else "UP通知",
                description=reminder_text,
                color=discord.Color.green()  # Use green color for bump notification
            ))
            # Remove notification from DB after sending
            query = "DELETE FROM notifications WHERE channel_id = %s AND reminder_text = %s"
            db.execute_query(query, (channel.id, reminder_text))
        except discord.Forbidden:
            print(f"Cannot send messages in {channel.name} due to lack of permissions")

    def load_notifications(self):
        query = """
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                channel_id BIGINT,
                title TEXT,
                notify_time TIMESTAMP,
                reminder_text TEXT
            )
        """
        db.execute_query(query)

async def setup(bot):
    await bot.add_cog(BumpNotify(bot))
