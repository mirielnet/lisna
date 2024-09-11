# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="serverinfo", description="サーバーの情報を表示します。")
    async def server_info(self, interaction: discord.Interaction):
        guild = interaction.guild

        if not guild:
            await interaction.response.send_message("このコマンドはサーバー内で使用してください。", ephemeral=True)
            return

        # deferで応答を保留
        await interaction.response.defer()

        # サーバー情報の取得
        guild_name = guild.name or "不明"
        guild_id = guild.id or "不明"
        guild_created_at = guild.created_at.strftime('%Y/%m/%d %H:%M:%S') if guild.created_at else "不明"
        member_count = guild.member_count or "不明"
        bot_count = len([member for member in guild.members if member.bot])
        
        text_channels = len([channel for channel in guild.channels if isinstance(channel, discord.TextChannel)])
        voice_channels = len([channel for channel in guild.channels if isinstance(channel, discord.VoiceChannel)])

        emojis = guild.emojis
        emoji_count = len(emojis)
        animated_emoji_count = len([emoji for emoji in emojis if emoji.animated])

        icon_url = guild.icon.url if guild.icon else None

        # オーナー情報の取得
        owner = guild.owner
        owner_tag = owner.display_name if owner else "不明"

        # Embedの作成
        embed = discord.Embed(title="サーバー情報", description=f"**サーバー名:**\n{guild_name}\n\n**サーバーID:**\n{guild_id}", color=discord.Color.blue())
        embed.add_field(name="オーナー", value=owner_tag, inline=True)
        embed.add_field(name="作成日時", value=guild_created_at, inline=True)
        embed.add_field(name="メンバー数", value=str(member_count), inline=True)
        embed.add_field(name="ボット数", value=str(bot_count), inline=True)
        embed.add_field(name="テキストチャンネル数", value=str(text_channels), inline=True)
        embed.add_field(name="ボイスチャンネル数", value=str(voice_channels), inline=True)
        embed.add_field(name="絵文字数", value=str(emoji_count), inline=True)
        embed.add_field(name="アニメーション絵文字数", value=str(animated_emoji_count), inline=True)

        if icon_url:
            embed.set_thumbnail(url=icon_url)

        # 絵文字のリスト
        emoji_list = ''.join([str(emoji) for emoji in emojis[:50]])  # 最大50個の絵文字を表示
        if emoji_list:
            embed.add_field(name="絵文字", value=emoji_list, inline=False)
        else:
            embed.add_field(name="絵文字", value="なし", inline=False)

        # メッセージ送信
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerInfo(bot))
