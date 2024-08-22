# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
import httpx  # requests から httpx へ変更

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
        target_lang: str,
        source_lang: str = None
    ):
        await interaction.response.defer(ephemeral=True)
        
        # デバッグ用のログ
        print("Translate command received. Preparing payload.")

        # Prepare the POST request payload
        payload = {
            "text": [text],  # テキストをリストで送信
            "target_lang": target_lang,
        }

        if source_lang:
            payload["source_lang"] = source_lang

        try:
            # デバッグ用のログ
            print(f"Sending request to DeeplX API with payload: {payload}")
            
            # Send the POST request to the DeeplX API using httpx
            async with httpx.AsyncClient(timeout=10.0) as client:  # タイムアウトを設定
                response = await client.post(
                    "https://translate.miriel.net/v2/translate",
                    json=payload,  # JSON形式でデータを送信
                )
                response.raise_for_status()  # Raise an error for bad HTTP status

            # デバッグ用のログ
            print("Received response from DeeplX API.")
            
            # レスポンス内容を確認
            response_json = response.json()
            print(f"Response JSON: {response_json}")

            # Parse the response JSON
            translated_text = response_json[0].get("text", None)  # テキストを取得

            if translated_text:
                # Create the Embed message
                embed = discord.Embed(
                    title="翻訳結果",
                    description=f"**{source_lang or '自動検出'}** から **{target_lang}** への翻訳結果です。",
                    color=discord.Color.blue(),
                )
                embed.add_field(name="オリジナル", value=text, inline=False)
                embed.add_field(name="翻訳", value=translated_text, inline=False)
                embed.set_footer(text="Powered by DeeplX")

                # Send the translated text in an Embed
                await interaction.followup.send(embed=embed)
            else:
                # Handle the case where translation fails
                await interaction.followup.send(
                    content="翻訳に失敗しました。もう一度お試しください。",
                    ephemeral=True,
                )

        except httpx.RequestError as e:
            # Handle network errors and API errors
            error_message = f"エラーが発生しました: {str(e)}"
            print(error_message)  # デバッグ用のログ
            await interaction.followup.send(
                content=error_message,
                ephemeral=True,
            )

async def setup(bot):
    await bot.add_cog(Translate(bot))
