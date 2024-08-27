# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands

class TicketManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

        # ボタンのcustom_idにカテゴリー名を追加する
        button = discord.ui.Button(label="チケットを発行", style=discord.ButtonStyle.green, custom_id=f"create_ticket:{category}")
        view = discord.ui.View(timeout=None)
        view.add_item(button)

        await interaction.response.send_message(embed=embed, view=view)
        self.bot.add_view(view)  # ボタンビューを再登録

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        # custom_idからアクションとカテゴリーを取得
        custom_id = interaction.data.get("custom_id")
        if custom_id and custom_id.startswith("create_ticket:"):
            category = custom_id.split(":", 1)[1]  # カテゴリー名を取得
            await self.create_ticket(interaction, category)
        elif custom_id == "close_ticket":
            await self.close_ticket(interaction)

    async def create_ticket(self, interaction: discord.Interaction, category_name: str):
        # チャンネルの作成処理
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

        # チャンネルに案内メッセージを送信
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
        self.bot.add_view(close_view)  # クローズボタンビューを再登録

    async def close_ticket(self, interaction: discord.Interaction):
        channel = interaction.channel
        try:
            await interaction.response.send_message("チケットが閉じられました。", ephemeral=True)
            await channel.delete()
        except discord.errors.NotFound:
            await interaction.followup.send("チャンネルが見つかりませんでした。既に削除されている可能性があります。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketManager(bot))
