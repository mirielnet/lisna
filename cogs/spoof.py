# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands

# A global variable to store the webhook
webhook = None

class Spoof(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="spoof", description="指定したユーザーまんまのWebHookを作成し、言わせたい言葉を送信します。")
    @app_commands.describe(user="なりすまししたいユーザーを指定してください。", message="言わせたい言葉を入力してください。")
    async def spoof(self, interaction: discord.Interaction, user: discord.User, message: str):
        await interaction.response.defer(ephemeral=True)

        global webhook

        try:
            # If no webhook exists, create one
            if webhook is None:
                created_webhook = await interaction.channel.create_webhook(
                    name=user.name,
                    avatar=await user.display_avatar.read()
                )
                webhook = created_webhook
            else:
                # If webhook already exists, edit it to match the target user
                await webhook.edit(name=user.name, avatar=await user.display_avatar.read())

            # Send the message using the webhook
            await webhook.send(content=message)

            await interaction.followup.send(f"{user.name} のなりすましWebHookを作成し、指定した言葉を送信しました。", ephemeral=True)
        
        except Exception as error:
            print(f"Error creating or sending webhook message: {error}")
            await interaction.followup.send("WebHookの作成やメッセージの送信中にエラーが発生しました。", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Spoof(bot))
