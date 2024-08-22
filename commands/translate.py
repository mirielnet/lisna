# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
import requests

class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="translate", description="指定されたテキストを翻訳します。"
    )
    @app_commands.describe(
        text="翻訳したいテキストを入力してください。",
        source_lang="ソーステキストの言語コードを入力してください。",
        target_lang="翻訳先の言語コードを入力してください。",
    )
    async def translate(
        self,
        interaction: discord.Interaction,
        text: str,
        source_lang: str,
        target_lang: str
    ):
        await interaction.response.defer(ephemeral=True)

        # Prepare the POST request payload
        payload = {
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
        }

        try:
            # Send the POST request to the DeeplX API
            response = requests.post(
                "https://translate.miriel.net/translate",
                data=payload,
            )
            response.raise_for_status()  # Raise an error for bad HTTP status

            # Parse the response JSON
            translated_text = response.json().get("text")

            if translated_text:
                # Create the Embed message
                embed = discord.Embed(
                    title="翻訳結果",
                    description=f"**{source_lang}** から **{target_lang}** への翻訳結果です。",
                    color=discord.Color.blue(),
                )
                embed.add_field(name="オリジナル", value=text, inline=False)
                embed.add_field(name="翻訳", value=translated_text, inline=False)
                embed.set_footer(text="Powered by Deepl")

                # Send the translated text in an Embed
                await interaction.followup.send(embed=embed)
            else:
                # Handle the case where translation fails
                await interaction.followup.send(
                    content="翻訳に失敗しました。もう一度お試しください。",
                    ephemeral=True,
                )

        except requests.exceptions.RequestException as e:
            # Handle network errors and API errors
            await interaction.followup.send(
                content=f"エラーが発生しました: {str(e)}",
                ephemeral=True,
            )

async def setup(bot):
    await bot.add_cog(Translate(bot))
