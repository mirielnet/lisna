# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import re  # Import regex for searching HTML content

class SafeWeb(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_url(self, url):
        safeweb_url = f"https://safeweb.norton.com/report/show?url={url}&ulang=jpn"
        async with aiohttp.ClientSession() as session:
            async with session.get(safeweb_url) as response:
                return await response.text()

    @app_commands.command(name="safeweb", description="URLの安全性をチェックします。")
    @app_commands.describe(url="安全性をチェックするURLを指定してください。")
    async def safeweb(self, interaction: discord.Interaction, url: str):
        if not url.startswith("http"):
            url = "http://" + url

        await interaction.response.defer()

        try:
            result = await self.check_url(url)

            # Use regex to search for the specific class and extract its text content
            match = re.search(r'<p[^>]*class=["\']?rating-label xl-body-text-bold["\']?[^>]*>(.*?)</p>', result)

            if match:
                rating = match.group(1).strip()  # Extract the text content and strip any extra whitespace

                if "警告" in rating:
                    color = discord.Color.red()
                    title = "このサイトは危険です"
                    description = ("これは既知の危険な Web サイトです。"
                                   "このページを表示**しない**ことを推奨します。")
                elif "注意" in rating:
                    color = discord.Color.yellow()
                    title = "このサイトは注意が必要です"
                    description = ("注意の評価を受けた Web サイトは少数の脅威または迷惑を伴いますが、"
                                   "警告に相当するほど危険とは見なされません。サイトにアクセスする場合には注意が必要です。\n\n"
                                   "※注意の評価は、誤判定の可能性があります。")
                elif "未評価" in rating:
                    color = discord.Color.gray()
                    title = "このサイトは評価されていません"
                    description = ("サイトは未評価のため、接続には注意が必要な可能性があります。")
                elif "安全" in rating:
                    color = discord.Color.green()
                    title = "このサイトは安全です"
                    description = "サイトからは脅威が確認されませんでした。安全に接続が可能です。"
                else:
                    # If no known status is found, set a default response
                    color = discord.Color.gray()
                    title = "サイトの評価が不明です"
                    description = ("サイトの安全性に関する情報を取得できませんでした。"
                                   "アクセスには注意が必要です。")

                embed = discord.Embed(
                    title=title,
                    description=description,
                    color=color,
                    url=f"https://safeweb.norton.com/report/show?url={url}&ulang=jpn"
                )
                embed.set_footer(text="Powered by Norton Safeweb")
                await interaction.followup.send(embed=embed)

            else:
                # If no rating is found
                embed = discord.Embed(
                    title="評価できませんでした",
                    description="サイトの評価が見つかりませんでした。",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="評価できませんでした",
                description="サイトの取得に失敗しました。",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SafeWeb(bot))
