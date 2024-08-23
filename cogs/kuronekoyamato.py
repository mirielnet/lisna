# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
import requests
from discord import app_commands
from discord.ext import commands


class KuronekoYamato(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="kuronekoyamato",
        description="クロネコヤマトの追跡番号を調べて表示します。",
    )
    async def kuronekoyamato(
        self, interaction: discord.Interaction, tracking_number: str
    ):
        await interaction.response.defer()

        try:
            # クロネコヤマトAPIにリクエストを送信
            response = requests.get(
                f"http://nanoappli.com/tracking/api/{tracking_number}.json"
            )
            response.raise_for_status()
            jsonData = response.json()
            resultCode = int(jsonData.get("result", 1))

            if resultCode == 0:
                statusList = jsonData.get("statusList", [])
                if statusList:
                    latestStatus = statusList[-1]
                    embed = discord.Embed(
                        title=f"クロネコヤマト 追跡番号: {jsonData.get('slipNo', '情報なし')}",
                        description=f"最新の配送状況: {latestStatus.get('status', '情報なし')}",
                        color=0x00FF00,
                    )
                    embed.add_field(
                        name="お届け予定日",
                        value=latestStatus.get("date", "情報なし"),
                        inline=True,
                    )
                    embed.add_field(
                        name="お届け先",
                        value=jsonData.get("destination", "情報なし"),
                        inline=True,
                    )
                    embed.add_field(
                        name="配達担当",
                        value=latestStatus.get("placeName", "情報なし"),
                        inline=True,
                    )
                    embed.add_field(
                        name="荷物の詳細",
                        value=latestStatus.get("placeCode", "情報なし"),
                        inline=True,
                    )
                else:
                    embed = discord.Embed(
                        title="クロネコヤマト 追跡情報",
                        description="追跡情報が見つかりませんでした。",
                        color=0xFF0000,
                    )
            else:
                embed = discord.Embed(
                    title=f"クロネコヤマト 追跡番号: {tracking_number}",
                    description="追跡番号が誤っているか未登録です。",
                    color=0xFF0000,
                )

            await interaction.followup.send(embed=embed)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching tracking info: {e}")
            await interaction.followup.send(
                "追跡番号の情報を取得する際にエラーが発生しました。", ephemeral=True
            )


async def setup(bot):
    print("Setting up KuronekoYamato Cog")
    await bot.add_cog(KuronekoYamato(bot))
    print("KuronekoYamato Cog setup complete")
