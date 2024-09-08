# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
from discord import app_commands
from g4f.client import Client  # G4Fクライアントのインポート

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ai", description="AIに質問してください。")
    @app_commands.describe(prompt="AIに聞きたいことを書いてください。")
    async def ai(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()

        try:
            # G4Fクライアントのインスタンスを作成
            client = Client()
            
            # GPT-3.5-turboに質問を投げる
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # 応答を取得
            ai_response = response.choices[0].message.content

            # Discord Embedを作成して、AIの応答を表示
            embed = discord.Embed(
                title="AIの応答",
                description=ai_response,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Powered by GPT-3.5 Turbo")

            # ユーザーにAIの応答を返す
            await interaction.followup.send(embed=embed)

        except Exception as e:
            # エラーハンドリング
            embed = discord.Embed(
                title="エラー",
                description="AIの応答を取得できませんでした。",
                color=discord.Color.red()
            )
            embed.add_field(name="詳細", value=str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
