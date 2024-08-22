# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import re
from datetime import datetime, timedelta

class TrollFix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect('./db/troll-fix.db')
        self.cursor = self.db.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                guild_id INTEGER PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                notification_channel_id INTEGER,
                exempt_channel_ids TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                user_id INTEGER,
                guild_id INTEGER,
                violation_type TEXT,
                count INTEGER,
                last_violation TIMESTAMP,
                PRIMARY KEY (user_id, guild_id, violation_type)
            )
        """)
        self.db.commit()

    @app_commands.command(name="tr-fix", description="荒らし対策を設定します。")
    @app_commands.describe(enabled="荒らし対策を有効化するか無効化するか", notification_channel="通知チャンネル", exempt_channels="保護対象外のチャンネル")
    @commands.has_permissions(administrator=True)
    async def tr_fix(self, interaction: discord.Interaction, enabled: bool, notification_channel: discord.TextChannel = None, exempt_channels: str = ""):
        await interaction.response.defer(ephemeral=True)  # Defer the response

        guild_id = interaction.guild.id
        exempt_channels_ids = ','.join([str(channel.id) for channel in exempt_channels.split(",")])

        self.cursor.execute("""
            INSERT INTO settings (guild_id, enabled, notification_channel_id, exempt_channel_ids) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id) 
            DO UPDATE SET enabled=excluded.enabled, notification_channel_id=excluded.notification_channel_id, exempt_channel_ids=excluded.exempt_channel_ids
        """, (guild_id, int(enabled), notification_channel.id if notification_channel else None, exempt_channels_ids))
        self.db.commit()

        await interaction.followup.send(f"荒らし対策が{'有効化' if enabled else '無効化'}されました。", ephemeral=True)

    @app_commands.command(name="tr-reset", description="特定ユーザーの違反回数をリセットします。")
    @app_commands.describe(user="違反回数をリセットするユーザー")
    @commands.has_permissions(administrator=True)
    async def tr_reset(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer(ephemeral=True)  # Defer the response

        self.cursor.execute("DELETE FROM violations WHERE user_id = ? AND guild_id = ?", (user.id, interaction.guild.id))
        self.db.commit()

        await interaction.followup.send(f"{user.mention}の違反回数がリセットされました。", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        guild_id = message.guild.id
        channel_id = message.channel.id

        self.cursor.execute("SELECT enabled, notification_channel_id, exempt_channel_ids FROM settings WHERE guild_id = ?", (guild_id,))
        settings = self.cursor.fetchone()

        if not settings or not settings[0]:
            return
        
        exempt_channels = settings[2].split(",") if settings[2] else []
        if str(channel_id) in exempt_channels:
            return

        # Check for spam
        self.cursor.execute("""
            SELECT count, last_violation FROM violations 
            WHERE user_id = ? AND guild_id = ? AND violation_type = 'spam'
        """, (message.author.id, guild_id))
        violation = self.cursor.fetchone()

        if violation:
            count, last_violation = violation
            last_violation_time = datetime.strptime(last_violation, "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - last_violation_time).seconds <= 1:
                count += 1
                if count >= 3:
                    await self.timeout_user(message.author, guild_id, count, "連投")
                    await self.notify_admin(settings[1], message.author, "連投", count)
            else:
                count = 1
        else:
            count = 1
        
        self.cursor.execute("""
            INSERT INTO violations (user_id, guild_id, violation_type, count, last_violation) 
            VALUES (?, ?, 'spam', ?, ?) 
            ON CONFLICT(user_id, guild_id, violation_type) 
            DO UPDATE SET count=excluded.count, last_violation=excluded.last_violation
        """, (message.author.id, guild_id, count, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.db.commit()

        # Check for Discord TOKEN
        if re.search(r'([A-Za-z0-9_\-]{24}\.[A-Za-z0-9_\-]{6}\.[A-Za-z0-9_\-]{27})', message.content):
            await self.timeout_user(message.author, guild_id, 1, "Discord TOKENの共有")
            await self.notify_admin(settings[1], message.author, "Discord TOKENの共有", 1)

        # Check for invite links spam
        if "discord.gg" in message.content:
            self.cursor.execute("""
                SELECT count, last_violation FROM violations 
                WHERE user_id = ? AND guild_id = ? AND violation_type = 'invite_spam'
            """, (message.author.id, guild_id))
            violation = self.cursor.fetchone()

            if violation:
                count, last_violation = violation
                last_violation_time = datetime.strptime(last_violation, "%Y-%m-%d %H:%M:%S")
                if (datetime.now() - last_violation_time).seconds <= 10:
                    count += 1
                    await self.timeout_user(message.author, guild_id, count, "招待リンクのスパム")
                    await self.notify_admin(settings[1], message.author, "招待リンクのスパム", count)
            else:
                count = 1
        
            self.cursor.execute("""
                INSERT INTO violations (user_id, guild_id, violation_type, count, last_violation) 
                VALUES (?, ?, 'invite_spam', ?, ?) 
                ON CONFLICT(user_id, guild_id, violation_type) 
                DO UPDATE SET count=excluded.count, last_violation=excluded.last_violation
            """, (message.author.id, guild_id, count, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.db.commit()

    async def timeout_user(self, user, guild_id, count, reason):
        timeout_duration = min(count * 10, 60)  # Example timeout logic
        until = discord.utils.utcnow() + timedelta(minutes=timeout_duration)
        await user.timeout(until, reason=reason)

    async def notify_admin(self, channel_id, user, reason, count):
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            embed = discord.Embed(
                title="荒らし行為が検出されました",
                description=f"{user.mention} が {reason} を行いました。",
                color=discord.Color.red()
            )
            embed.add_field(name="処置", value=f"{count}回の違反によりタイムアウトされました。", inline=False)
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TrollFix(bot))
