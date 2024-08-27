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
        await self.load_existing_tickets()

    async def migrate_db(self):
        # トランザクションエラーが発生している場合、トランザクションを明示的に終了
        db.execute_query("ROLLBACK;")

        # `category` カラムを追加するためのマイグレーションクエリ
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
        # テーブルの作成（既に存在する場合は何もしない）
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

    async def load_existing_tickets(self):
        # 既存のチケット情報を読み込んでインタラクションを再生成
        select_query = "SELECT channel_id, category FROM tickets WHERE closed = FALSE;"
        result = db.execute_query(select_query)  # クエリを実行して結果を取得

        if result:
            for row in result:
                channel_id, category = row
                channel = self.bot.get_channel(channel_id)

                if channel:
                    # チャンネルに既存のインタラクションを再生成
                    await self.send_ticket_controls(channel, category)

    @app_commands.command(name="ticket", description="Ticketシステムの設定")
    @app_commands.describe(category="チケットを作成するカテゴリー名を指定", custom_message="カスタムメッセージを設定する")
    async def ticket(self, interaction: discord.Interaction, category: str, custom_message: str = None):
        # 管理者およびモデレーター以外は実行不可
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

        async def button_callback(interaction: discord.Interaction):
            # チャンネルの作成
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            }
            category_channel = discord.utils.get(interaction.guild.categories, name=category)
            if not category_channel:
                await interaction.response.send_message(f"カテゴリー '{category}' が見つかりませんでした。", ephemeral=True)
                return

            ticket_channel = await interaction.guild.create_text_channel(
                name=f"ticket-{interaction.user.display_name}",
                category=category_channel,
                overwrites=overwrites
            )

            # DBにチケット情報を保存
            insert_query = """
            INSERT INTO tickets (user_id, channel_id, category)
            VALUES (%s, %s, %s);
            """
            db.execute_query(insert_query, (interaction.user.id, ticket_channel.id, category))

            # チャンネルにインタラクションを追加
            await self.send_ticket_controls(ticket_channel, category)

            await interaction.response.send_message(f"チケットチャンネルが {ticket_channel.mention} に作成されました。", ephemeral=True)

        button.callback = button_callback
        await interaction.response.send_message(embed=embed, view=view)

    async def send_ticket_controls(self, channel, category):
        ticket_embed = discord.Embed(
            title="チケットが作成されました",
            description="ご用件を書いてお待ちください。サポートスタッフが対応いたします。",
            color=discord.Color.green()
        )
        close_button = discord.ui.Button(label="チケットを閉じる", style=discord.ButtonStyle.red, custom_id="close_ticket")
        close_view = discord.ui.View(timeout=None)
        close_view.add_item(close_button)

        async def close_button_callback(interaction: discord.Interaction):
            # チケットを閉じる処理
            try:
                await interaction.response.send_message("チケットが閉じられました。", ephemeral=True)
                await channel.delete()

                # DBでチケットを閉じたとマーク
                update_query = """
                UPDATE tickets SET closed = TRUE WHERE channel_id = %s;
                """
                db.execute_query(update_query, (channel.id,))
            except discord.errors.NotFound:
                await interaction.followup.send("チャンネルが見つかりませんでした。既に削除されている可能性があります。", ephemeral=True)

        close_button.callback = close_button_callback
        await channel.send(embed=ticket_embed, view=close_view)

async def setup(bot):
    await bot.add_cog(TicketManager(bot))
