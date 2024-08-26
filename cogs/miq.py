# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
import re
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class MIQCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.miq_url = os.getenv("MIQ_URL")

    @app_commands.command(name="miq", description="DiscordのメッセージリンクまたはメッセージIDから情報を取得して画像を生成します。")
    async def miq(self, interaction: discord.Interaction, message_link_or_id: str):
        # メッセージIDがリンクか直接IDかを判定
        message_id_pattern = r"https://discord\.com/channels/(\d+)/(\d+)/(\d+)"
        match = re.match(message_id_pattern, message_link_or_id)

        if match:
            guild_id, channel_id, message_id = map(int, match.groups())
        else:
            guild_id = interaction.guild.id
            channel_id = interaction.channel_id
            message_id = int(message_link_or_id)

        guild = self.bot.get_guild(guild_id)
        if not guild:
            await interaction.response.send_message("指定されたサーバーが見つかりませんでした。", ephemeral=True)
            return

        channel = guild.get_channel(channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("指定されたチャンネルが見つかりませんでした。", ephemeral=True)
            return

        try:
            target_message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await interaction.response.send_message("指定されたメッセージが見つかりませんでした。", ephemeral=True)
            return

        # メッセージの情報を取得
        name = target_message.author.display_name
        user_id = target_message.author.id
        content = target_message.content
        icon_url = target_message.author.avatar.url

        # GETリクエストを送信
        params = {
            "name": name,
            "id": user_id,
            "content": content,
            "icon": icon_url
        }

        try:
            response = requests.get(self.miq_url, params=params)
            response.raise_for_status()  # ステータスコードが200でない場合、例外を発生
            image_data = response.content

            with open("output.png", "wb") as f:
                f.write(image_data)

            await interaction.response.send_message(file=discord.File("output.png"))

        except requests.exceptions.RequestException as e:
            await interaction.response.send_message(f"リクエストに失敗しました: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MIQCog(bot))
