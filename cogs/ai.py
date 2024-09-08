# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
from discord import app_commands
from g4f.client import Client  # G4Fクライアントのインポート

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_last_ai_message = {}  # Guildごとに最後のAIメッセージIDを保持

    @app_commands.command(name="ai", description="AIに質問してください。")
    @app_commands.describe(prompt="AIに聞きたいことを書いてください。")
    async def ai(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()

        try:
            client = Client()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )

            ai_response = response.choices[0].message.content

            # Embedメッセージの作成
            embed = discord.Embed(
                title="AIの応答",
                description=ai_response,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Powered by GPT-3.5 Turbo")

            # 応答を送信し、送信されたメッセージIDを保持
            message = await interaction.followup.send(embed=embed)

            # Guildごとに最後のAIメッセージIDを記録
            self.guild_last_ai_message[interaction.guild.id] = message.id

        except Exception as e:
            embed = discord.Embed(
                title="エラー",
                description="AIの応答を取得できませんでした。",
                color=discord.Color.red()
            )
            embed.add_field(name="詳細", value=str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # BOT自身のメッセージには反応しない
        if message.author == self.bot.user:
            return

        # メッセージがリプライかどうかを確認
        if message.reference and message.reference.message_id:
            # GuildのIDを取得
            guild_id = message.guild.id

            # そのGuildでの最後のAIメッセージIDと一致するか確認
            if guild_id in self.guild_last_ai_message and message.reference.message_id == self.guild_last_ai_message[guild_id]:
                prompt = message.content  # ユーザーのリプライ内容

                # G4Fを使ってAIに質問を送信
                try:
                    client = Client()
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}]
                    )

                    ai_response = response.choices[0].message.content

                    # 新しいEmbedメッセージでAIの応答を返す
                    embed = discord.Embed(
                        title="AIの応答",
                        description=ai_response,
                        color=discord.Color.blue()
                    )
                    embed.set_footer(text="Powered by GPT-3.5 Turbo")

                    # 新しい応答メッセージのIDを再度保存
                    new_message = await message.channel.send(embed=embed)
                    self.guild_last_ai_message[message.guild.id] = new_message.id

                except Exception as e:
                    embed = discord.Embed(
                        title="エラー",
                        description="AIの応答を取得できませんでした。",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="詳細", value=str(e))
                    await message.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
