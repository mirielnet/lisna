# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands
from g4f.client import Client  # G4Fクライアントのインポート

# ログの設定
logging.basicConfig(level=logging.ERROR)


class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_last_ai_message = {}  # Guildごとに最後のAIメッセージIDを保持
        self.cooldowns = {}  # クールダウンの管理

    @app_commands.command(name="ai", description="AIに質問してください。")
    @app_commands.describe(prompt="AIに聞きたいことを書いてください。")
    async def ai(self, interaction: discord.Interaction, prompt: str):
        # クールダウンチェック
        user_id = interaction.user.id
        if user_id in self.cooldowns:
            remaining_time = (
                self.cooldowns[user_id] - discord.utils.utcnow().timestamp()
            )
            if remaining_time > 0:
                await interaction.response.send_message(
                    f"このコマンドは{remaining_time:.1f}秒後に再度使用可能です。",
                    ephemeral=True,
                )
                return

        await interaction.response.defer()

        try:
            # タイムアウト設定
            async def get_ai_response():
                client = Client()
                response = client.chat.completions.create(
                    model="gpt-4",  # GPT-4に変更
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content

            try:
                ai_response = await asyncio.wait_for(
                    get_ai_response(), timeout=10
                )  # タイムアウトを10秒に設定
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="タイムアウト",
                    description="AIとの接続がタイムアウトしました。後ほどお試しください。",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed)
                return

            # Embedメッセージの作成
            embed = discord.Embed(
                title="AIの応答", description=ai_response, color=discord.Color.blue()
            )
            embed.set_footer(text="Powered by GPT-4")

            # 応答を送信し、送信されたメッセージIDを保持
            message = await interaction.followup.send(embed=embed)

            # Guildごとに最後のAIメッセージIDを記録
            self.guild_last_ai_message[interaction.guild.id] = message.id

            # クールダウン設定（10秒間）
            self.cooldowns[user_id] = discord.utils.utcnow().timestamp() + 10

        except RuntimeError as e:
            logging.error(f"RuntimeError: {str(e)}")
            embed = discord.Embed(
                title="エラー",
                description=f"エラーが発生しました: {str(e)}",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logging.error(f"Unexpected Error: {str(e)}")
            embed = discord.Embed(
                title="エラー",
                description="予期しないエラーが発生しました。",
                color=discord.Color.red(),
            )
            embed.add_field(name="詳細", value=str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        if message.reference and message.reference.message_id:
            guild_id = message.guild.id

            if (
                guild_id in self.guild_last_ai_message
                and message.reference.message_id == self.guild_last_ai_message[guild_id]
            ):
                prompt = message.content

                try:
                    # タイムアウト設定
                    async def get_ai_response():
                        client = Client()
                        response = client.chat.completions.create(
                            model="gpt-4",  # GPT-4に変更
                            messages=[{"role": "user", "content": prompt}],
                        )
                        return response.choices[0].message.content

                    # タイピング処理を実行
                    async with message.channel.typing():
                        try:
                            ai_response = await asyncio.wait_for(
                                get_ai_response(), timeout=10
                            )  # タイムアウトを10秒に設定
                        except asyncio.TimeoutError:
                            embed = discord.Embed(
                                title="タイムアウト",
                                description="AIとの接続がタイムアウトしました。後ほどお試しください。",
                                color=discord.Color.red(),
                            )
                            await message.channel.send(embed=embed)
                            return

                    # 新しいEmbedメッセージでAIの応答を返す（メンション付き）
                    embed = discord.Embed(
                        title="AIの応答",
                        description=ai_response,
                        color=discord.Color.blue(),
                    )
                    embed.set_footer(text="Powered by GPT-4")

                    # メンション付きで応答メッセージを送信
                    new_message = await message.channel.send(
                        content=f"{message.author.mention}", embed=embed
                    )
                    self.guild_last_ai_message[message.guild.id] = new_message.id

                except RuntimeError as e:
                    logging.error(f"RuntimeError: {str(e)}")
                    embed = discord.Embed(
                        title="エラー",
                        description=f"エラーが発生しました: {str(e)}",
                        color=discord.Color.red(),
                    )
                    await message.channel.send(embed=embed)

                except Exception as e:
                    logging.error(f"Unexpected Error: {str(e)}")
                    embed = discord.Embed(
                        title="エラー",
                        description="予期しないエラーが発生しました。",
                        color=discord.Color.red(),
                    )
                    embed.add_field(name="詳細", value=str(e))
                    await message.channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AIChat(bot))
