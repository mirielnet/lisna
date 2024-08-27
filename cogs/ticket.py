# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from core.connect import db

class TicketManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        await self.migrate_db()
        await self.init_db()

    async def migrate_db(self):
        db.execute_query("ROLLBACK;")  # トランザクションエラーが発生している場合、トランザクションを明示的に終了

        alter_table_query = """
        ALTER TABLE tickets
        ADD COLUMN IF NOT EXISTS category VARCHAR(255) NOT NULL DEFAULT '';
        """
        try:
            db.execute_query(alter_table_query)
            print("テーブルのマイグレーションが正常に完了しました。")
        except Exception as e:
            print(f"マイグレーション中にエラーが発生しました: {e}")

    async def init_db(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS tickets (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            channel_id BIGINT NOT NULL,
            category VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            closed BOOLEAN DEFAULT FALSE
        );
        """
        db.execute_query(create_table_query)

    @app_commands.command(name="ticket", description="Ticketシステムの設定")
    @app_commands.describe(category="チケットを作成するカテゴリー名を指定", custom_message="カスタムメッセージを設定する")
    async def ticket(self, interaction: discord.Interaction, category: str, custom_message: str = None):
        if not interaction.user.guild_permissions.administrator and not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True)
            return

        embed = discord.Embed(
            title="チケットシステム",
            description=custom_message if custom_message else "サポートが必要な場合は以下のボタンをクリックしてチケットを発行してください。",
            color=discord.Color.blue()
        )

        button = discord.ui.Button(label="チケットを発行", style=discord.ButtonStyle.green, custom_id="create_ticket")
        view = discord.ui.View(timeout=None)
        view.add_item(button)

        await interaction.response.send_message(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        # custom_idが"create_ticket"の場合
        if interaction.data.get("custom_id") == "create_ticket":
            await self.create_ticket(interaction)
        # custom_idが"close_ticket"の場合
        elif interaction.data.get("custom_id") == "close_ticket":
            await self.close_ticket(interaction)

    async def create_ticket(self, interaction: discord.Interaction):
        category_name = "サポート"
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        category_channel = discord.utils.get(interaction.guild.categories, name=category_name)
        if not category_channel:
            await interaction.response.send_message(f"カテゴリー '{category_name}' が見つかりませんでした。", ephemeral=True)
            return

        ticket_channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.display_name}",
            category=category_channel,
            overwrites=overwrites
        )

        insert_query = """
        INSERT INTO tickets (user_id, channel_id, category)
        VALUES (%s, %s, %s);
        """
        db.execute_query(insert_query, (interaction.user.id, ticket_channel.id, category_name))

        ticket_embed = discord.Embed(
            title="チケットが作成されました",
            description="ご用件を書いてお待ちください。サポートスタッフが対応いたします。",
            color=discord.Color.green()
        )
        close_button = discord.ui.Button(label="チケットを閉じる", style=discord.ButtonStyle.red, custom_id="close_ticket")
        close_view = discord.ui.View(timeout=None)
        close_view.add_item(close_button)

        await ticket_channel.send(embed=ticket_embed, view=close_view)
        await interaction.response.send_message(f"チケットチャンネルが {ticket_channel.mention} に作成されました。", ephemeral=True)

    async def close_ticket(self, interaction: discord.Interaction):
        channel = interaction.channel
        try:
            await interaction.response.send_message("チケットが閉じられました。", ephemeral=True)
            await channel.delete()

            update_query = """
            UPDATE tickets SET closed = TRUE WHERE channel_id = %s;
            """
            db.execute_query(update_query, (channel.id,))
        except discord.errors.NotFound:
            await interaction.followup.send("チャンネルが見つかりませんでした。既に削除されている可能性があります。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketManager(bot))
