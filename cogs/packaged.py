# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
import httpx
from discord import app_commands
from discord.ext import commands


class Packaged(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="packaged", description="npm または pip のパッケージを検索します。"
    )
    @app_commands.describe(name="パッケージ名")
    @app_commands.choices(
        type=[
            app_commands.Choice(name="npm", value="npm"),
            app_commands.Choice(name="pip", value="pip"),
        ]
    )
    async def packaged(
        self,
        interaction: discord.Interaction,
        type: app_commands.Choice[str],
        name: str,
    ):
        await interaction.response.defer()

        try:
            if type.value == "npm":
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://api.npms.io/v2/search?q={name}"
                    )
                    data = response.json()

                if not data["results"]:
                    raise ValueError("Package not found")

                pkg = data["results"][0]["package"]
                embed = discord.Embed(
                    color=discord.Color.green(),
                    title=f"NPM: {pkg['name']}",
                    url=pkg["links"]["npm"],
                    description=pkg.get("description", "説明なし"),
                )
                embed.add_field(
                    name="作者",
                    value=pkg.get("author", {}).get("name", "なし"),
                    inline=True,
                )
                embed.add_field(
                    name="バージョン", value=pkg.get("version", "不明"), inline=True
                )
                embed.add_field(
                    name="リポジトリ",
                    value=pkg["links"].get("repository", "なし"),
                    inline=True,
                )
                embed.add_field(
                    name="キーワード",
                    value=", ".join(pkg.get("keywords", [])) or "なし",
                    inline=True,
                )
                embed.set_footer(text="Powered by npm")

            elif type.value == "pip":
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"https://pypi.org/pypi/{name}/json")
                    data = response.json()

                pkg = data["info"]
                embed = discord.Embed(
                    color=discord.Color.green(),
                    title=f"PYPI: {pkg['name']}",
                    url=pkg["package_url"],
                    description=pkg.get("summary", "説明なし"),
                )
                embed.add_field(
                    name="作者", value=pkg.get("author", "なし"), inline=True
                )
                embed.add_field(
                    name="バージョン", value=pkg.get("version", "不明"), inline=True
                )
                embed.add_field(
                    name="リポジトリ",
                    value=pkg.get("project_urls", {}).get("Home", "なし"),
                    inline=True,
                )
                embed.add_field(
                    name="ライセンス", value=pkg.get("license", "なし"), inline=True
                )
                embed.add_field(
                    name="キーワード", value=pkg.get("keywords", "なし"), inline=True
                )
                embed.set_footer(text="Powered by PyPI")

            else:
                raise ValueError("Invalid package type")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                color=discord.Color.red(),
                title="取得できませんでした",
                description="検索ワードを変えてやり直してください。",
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Packaged(bot))
