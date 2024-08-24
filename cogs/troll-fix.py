# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from core.connect import db  # Import the global db instance

class TrollFix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.create_tables()

    def create_tables(self):
        db.connect()
        # Create settings table
        create_troll_settings_table = """
        CREATE TABLE IF NOT EXISTS troll_settings (
            guild_id BIGINT PRIMARY KEY,
            enabled BOOLEAN DEFAULT FALSE,
            notification_channel_id BIGINT,
            exempt_channel_ids TEXT
        );
        """
        db.execute_query(create_troll_settings_table)

        # Create violations table
        create_troll_violations_table = """
        CREATE TABLE IF NOT EXISTS troll_violations (
            user_id BIGINT,
            guild_id BIGINT,
            violation_type TEXT,
            count INTEGER,
            last_violation TIMESTAMP,
            PRIMARY KEY (user_id, guild_id, violation_type)
        );
        """
        db.execute_query(create_troll_violations_table)

    @app_commands.command(name="tr-fix", description="荒らし対策を設定します。")
    @app_commands.describe(
        enabled="荒らし対策を有効化するか無効化するか",
        notification_channel="通知チャンネル",
        exempt_channels="保護対象外のチャンネルをカンマ区切りで指定します",
    )
    @commands.has_permissions(administrator=True)
    async def tr_fix(
        self,
        interaction: discord.Interaction,
        enabled: bool,
        notification_channel: discord.TextChannel = None,
        exempt_channels: str = "",
    ):
        try:
            await interaction.response.defer(ephemeral=True)  # Defer the response

            guild_id = interaction.guild.id
            exempt_channel_ids = ",".join(
                str(discord.utils.get(interaction.guild.text_channels, name=ch.strip()).id)
                for ch in exempt_channels.split(",") if ch.strip()
            )

            upsert_settings_query = """
            INSERT INTO troll_settings (guild_id, enabled, notification_channel_id, exempt_channel_ids) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT(guild_id) 
            DO UPDATE SET enabled=excluded.enabled, notification_channel_id=excluded.notification_channel_id, exempt_channel_ids=excluded.exempt_channel_ids;
            """
            db.execute_query(upsert_settings_query, (guild_id, enabled, notification_channel.id if notification_channel else None, exempt_channel_ids))

            await interaction.followup.send(
                f"荒らし対策が{'有効化' if enabled else '無効化'}されました。",
                ephemeral=True,
            )

        except Exception as e:
            await interaction.followup.send(
                f"エラーが発生しました: {str(e)}", ephemeral=True
            )

    @app_commands.command(
        name="tr-reset", description="特定ユーザーの違反回数をリセットします。"
    )
    @app_commands.describe(user="違反回数をリセットするユーザー")
    @commands.has_permissions(administrator=True)
    async def tr_reset(self, interaction: discord.Interaction, user: discord.User):
        try:
            await interaction.response.defer(ephemeral=True)  # Defer the response

            delete_violations_query = """
            DELETE FROM troll_violations WHERE user_id = %s AND guild_id = %s;
            """
            db.execute_query(delete_violations_query, (user.id, interaction.guild.id))

            await interaction.followup.send(
                f"{user.mention}の違反回数がリセットされました。", ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(
                f"エラーが発生しました: {str(e)}", ephemeral=True
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        try:
            guild_id = message.guild.id
            channel_id = message.channel.id

            select_settings_query = """
            SELECT enabled, notification_channel_id, exempt_channel_ids FROM troll_settings WHERE guild_id = %s;
            """
            settings = db.execute_query(select_settings_query, (guild_id,))

            if not settings or not settings[0][0]:
                return

            exempt_channels = settings[0][2].split(",") if settings[0][2] else []
            if str(channel_id) in exempt_channels:
                return

            # Handle spam detection
            await self.handle_spam_detection(message)

            # Handle Discord TOKEN leak detection
            await self.handle_token_leak_detection(message)

            # Handle invite link detection
            await self.handle_invite_link_detection(message)

        except Exception as e:
            print(f"Error handling message: {str(e)}")

    async def handle_spam_detection(self, message):
        # Detect if the user sends more than 3 messages in 1 second
        async for msg in message.channel.history(limit=3):
            if msg.author == message.author and (datetime.now(timezone.utc) - msg.created_at).total_seconds() < 1:
                violation_type = "spam"
                await self.process_violation(message, violation_type)
                break

    async def handle_token_leak_detection(self, message):
        if "discord.com/api" in message.content and "Bot" in message.content:
            violation_type = "token_leak"
            await self.process_violation(message, violation_type)

    async def handle_invite_link_detection(self, message):
        if "discord.gg" in message.content:
            violation_type = "invite_link"
            await self.process_violation(message, violation_type)

    async def process_violation(self, message, violation_type):
        user_id = message.author.id
        guild_id = message.guild.id
        now = datetime.now(timezone.utc)

        # UPSERTクエリ: 既にレコードが存在する場合は更新、存在しない場合は挿入
        upsert_violations_query = """
        INSERT INTO troll_violations (user_id, guild_id, violation_type, count, last_violation) 
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id, guild_id, violation_type)
        DO UPDATE SET count = troll_violations.count + 1, last_violation = excluded.last_violation;
        """
        db.execute_query(upsert_violations_query, (user_id, guild_id, violation_type, 1, now))

        # タイムアウト期間を計算
        select_count_query = """
        SELECT count FROM troll_violations WHERE user_id = %s AND guild_id = %s AND violation_type = %s;
        """
        result = db.execute_query(select_count_query, (user_id, guild_id, violation_type))
        count = result[0][0] if result else 1

        timeout_duration = min(timedelta(minutes=10 * count), timedelta(hours=24))

        # タイムアウト実行
        await message.author.edit(timeout_until=now + timeout_duration, reason=f"違反: {violation_type}")

        # 通知チャンネルにメッセージを送信
        select_settings_query = """
        SELECT notification_channel_id FROM troll_settings WHERE guild_id = %s;
        """
        settings = db.execute_query(select_settings_query, (guild_id,))
        if settings and settings[0][0]:
            notification_channel = self.bot.get_channel(settings[0][0])
            if notification_channel:
                await notification_channel.send(
                    embed=discord.Embed(
                        title="違反検出",
                        description=f"{message.author.mention} が `{violation_type}` によりタイムアウトされました。",
                        color=discord.Color.red(),
                    )
                )

async def setup(bot):
    await bot.add_cog(TrollFix(bot))
