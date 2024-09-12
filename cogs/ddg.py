# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import urllib.parse

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord import app_commands
from discord.ext import commands


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
                    await interaction.followup.send(
                        "検索中にエラーが発生しました。もう一度お試しください。",
                        ephemeral=True,
                    )
                    return

                html = await response.text()

        # BeautifulSoupを使用してリンクを解析
        soup = BeautifulSoup(html, "html.parser")
        results = []

        # 検索結果のリンクを取得
        for result in soup.find_all("a", {"class": "result__a"}, href=True):
            title = result.get_text()
            link = result["href"]

            # リンクが DuckDuckGo のプロキシリンクの場合、正しいURLを抽出
            if "uddg=" in link:
                parsed_link = urllib.parse.urlparse(link)
                query_params = urllib.parse.parse_qs(parsed_link.query)
                if "uddg" in query_params:
                    link = query_params["uddg"][0]  # 本来のURLを取得

            results.append((title, link))
            if len(results) >= 10:  # 最初の10件の結果のみ表示
                break

        if not results:
            await interaction.followup.send(
                "検索結果が見つかりませんでした。", ephemeral=True
            )
            return

        # 検索結果をEmbedメッセージに追加
        embed = discord.Embed(
            title="DuckDuckGo 検索結果",
            description=f"{query} の検索結果:",
            color=0x1A73E8,
        )

        for title, link in results:
            embed.add_field(name=title, value=f"[リンクはこちら]({link})", inline=False)

        embed.set_footer(text="Powered by DuckDuckGo")

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(DuckDuckGo(bot))
