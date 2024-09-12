# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import os

import discord
import requests
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# .envファイルからトークンを読み込み
load_dotenv()
CHUNIREC_TOKEN = os.getenv("CHUNIREC_TOKEN")


class Chunithm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="chu-profile",
        description="CHUNIREC(CHUNITHM)のプレイヤープロフィールを取得します。",
    )
    async def chu_profile(self, interaction: discord.Interaction, user_name: str):
        await interaction.response.defer()

        # CHUNIREC APIにリクエストを送信
        url = f"https://api.chunirec.net/2.0/records/profile.json?user_name={user_name}&region=jp2&token={CHUNIREC_TOKEN}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            embed = discord.Embed(title=f"{data['player_name']}のCHUNITHMプロフィール")
            embed.add_field(
                name="プレイヤー名", value=data["player_name"], inline=False
            )
            embed.add_field(name="称号", value=data["title"], inline=False)
            embed.add_field(
                name="称号のレアリティ", value=data["title_rarity"], inline=True
            )
            embed.add_field(name="レベル", value=data["level"], inline=True)
            embed.add_field(name="レーティング", value=data["rating"], inline=True)
            embed.add_field(
                name="最大レーティング", value=data["rating_max"], inline=True
            )
            embed.add_field(
                name="クラスエンブレム", value=data["classemblem"], inline=True
            )
            embed.add_field(
                name="チームに参加",
                value="はい" if data["is_joined_team"] else "いいえ",
                inline=True,
            )
            embed.set_footer(text=f"最終更新: {data['updated_at']}")

            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(
                "プレイヤープロフィールを取得できませんでした。Chinirecのプレイヤー名を確認してください。",
                ephemeral=True,
            )


async def setup(bot):
    await bot.add_cog(Chunithm(bot))
