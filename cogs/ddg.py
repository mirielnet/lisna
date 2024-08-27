# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

class DuckDuckGo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ddg", description="DuckDuckGoで検索します。")
    @app_commands.describe(query="検索したい文字列を指定してください。")
    async def ddg(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        search_url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"

        async with aiohttp.ClientSession() as session:
            async with session.get(search_url) as response:
                if response.status != 200:
                    await interaction.followup.send("検索中にエラーが発生しました。もう一度お試しください。", ephemeral=True)
                    return

                html = await response.text()

        # Construct and send the search result message
        embed = discord.Embed(
            title="DuckDuckGo 検索結果",
            description=f"[{query}]({search_url}) の検索結果を表示します。",
            color=0x1a73e8
        )
        embed.add_field(name="リンク", value=f"[こちらから検索結果をご覧ください]({search_url})")
        embed.set_footer(text="Powered by DuckDuckGo")

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DuckDuckGo(bot))
