# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
import httpx  # Import httpx for HTTP requests

class R18IMG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="r18-img", description="NekoBot APIからR18画像をランダムに取得します。")
    @app_commands.describe(type="取得する画像のタイプ")
    @app_commands.choices(type=[
        discord.app_commands.Choice(name="一般の画像(R18)", value="pgif"),
        discord.app_commands.Choice(name="Neko画像", value="neko"),
        discord.app_commands.Choice(name="2次元画像(R18)", value="hentai")
    ])
    async def r18_ig(self, interaction: discord.Interaction, type: str):
        # Check if the channel is NSFW
        if not interaction.channel.is_nsfw():
            await interaction.response.send_message("このコマンドはNSFWチャンネルでのみ実行できます。", ephemeral=True)
            return

        api_url = f"https://nekobot.xyz/api/image?type={type}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url)
                data = response.json()

                # Check if API response contains the image
                if data['success']:
                    image_url = data['message']
                    embed = discord.Embed(
                        color=discord.Color.red(),
                        title={
                            "pgif": "一般の画像(R18)",
                            "neko": "Neko画像",
                            "hentai": "2次元画像(R18)"
                        }[type]
                    ).set_image(url=image_url)

                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message("画像の取得中にエラーが発生しました。", ephemeral=True)

        except Exception as e:
            print(e)
            await interaction.response.send_message("画像の取得中にエラーが発生しました。", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(R18IMG(bot))
