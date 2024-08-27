# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
import httpx

class Wikipedia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="wikipedia", description="指定したWikipediaの記事を表示します。")
    @app_commands.describe(word="検索するワードを入力してください。")
    async def wikipedia(self, interaction: discord.Interaction, word: str):
        await interaction.response.defer()

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                # Get the initial response with the possibility of a 302 redirect
                response = await client.get(f"https://ja.wikipedia.org/api/rest_v1/page/summary/{httpx.URL(word)}")
                data = response.json()

            embed = discord.Embed(
                color=discord.Color.green(),
                title=data["title"],
                url=data["content_urls"]["desktop"]["page"],
                description=data["extract"]
            )
            embed.set_footer(text="Powered by Wikipedia")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                color=discord.Color.red(),
                title="取得できませんでした",
                description=f"検索ワードを変えて、もう一度実行してください。\nエラー: {str(e)}"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Wikipedia(bot))
