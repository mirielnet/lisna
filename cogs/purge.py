# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands


class PurgeChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="purge", description="チャンネルを再作成します。（サーバー管理者のみ）"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def purge(self, interaction: discord.Interaction):
        # コマンドを実行したチャンネルを取得
        channel = interaction.channel

        # サーバー管理者かどうかをチェック
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "このコマンドはサーバー管理者のみが使用できます。", ephemeral=True
            )
            return

        # チャンネルの情報を取得
        channel_name = channel.name
        category = channel.category
        position = channel.position
        topic = channel.topic
        nsfw = channel.nsfw
        overwrites = channel.overwrites
        slowmode_delay = channel.slowmode_delay

        # チャンネルを削除
        await channel.delete()

        # チャンネルを再作成
        new_channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            position=position,
            topic=topic,
            nsfw=nsfw,
            overwrites=overwrites,
            slowmode_delay=slowmode_delay,
        )

        # 完了メッセージをEmbedで送信
        embed = discord.Embed(
            title="チャンネル再作成完了",
            description=f"チャンネル {new_channel.mention} が再作成されました。",
            color=discord.Color.green(),
        )
        await new_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PurgeChannel(bot))
