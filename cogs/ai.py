# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
from discord import app_commands
import G4F

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}

    @app_commands.command(name="ai", description="AIに質問できます。")
    @app_commands.describe(prompt="AIに聞きたいことを書いてください")
    async def ai(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()

        try:
            # Use G4F module to query GPT-3.5-turbo with the user's prompt
            response = G4F.ChatCompletion.create(
                model="gpt-3.5-turbo", 
                messages=[{"role": "user", "content": prompt}]
            )

            # Storing the response session in memory for follow-up conversations
            self.sessions[interaction.user.id] = response["choices"][0]["message"]["content"]

            embed = discord.Embed(
                title="AIの応答",
                description=self.sessions[interaction.user.id],
                color=discord.Color.blue()
            )
            embed.set_footer(text="Powered by GPT 3.5 Turbo")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="エラー",
                description="AIの応答を取得できませんでした。",
                color=discord.Color.red()
            )
            embed.add_field(name="詳細", value=str(e))
            await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return  # Ignore messages from the bot itself

        # Check if this is a reply to the bot's message in an AI conversation
        if message.reference and message.reference.message_id:
            # Get the original message (embed) the user is replying to
            referenced_message = await message.channel.fetch_message(message.reference.message_id)

            if referenced_message.author == self.bot.user and "Powered by GPT 3.5 Turbo" in referenced_message.embeds[0].footer.text:
                # Continuing the conversation with GPT-3.5-turbo
                previous_session = referenced_message.embeds[0].description
                user_input = message.content

                try:
                    # Continue the conversation with the user's reply
                    response = G4F.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "user", "content": previous_session},
                            {"role": "user", "content": user_input}
                        ]
                    )
                    reply_content = response["choices"][0]["message"]["content"]

                    embed = discord.Embed(
                        title="AIの応答",
                        description=reply_content,
                        color=discord.Color.blue()
                    )
                    embed.set_footer(text="Powered by GPT 3.5 Turbo")

                    await message.channel.send(embed=embed)

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
