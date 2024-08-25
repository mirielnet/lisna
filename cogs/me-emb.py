# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
import re

class MessageLinkListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Botが送信したメッセージは無視する
        if message.author.bot:
            return
        
        # メッセージリンクの正規表現パターン
        message_link_pattern = r"https://discord\.com/channels/(\d+)/(\d+)/(\d+)"
        matches = re.findall(message_link_pattern, message.content)

        # メッセージリンクが見つかった場合
        for match in matches:
            guild_id, channel_id, message_id = map(int, match)

            # サーバー、チャンネル、メッセージを取得
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue

            channel = guild.get_channel(channel_id)
            if not channel or not isinstance(channel, discord.TextChannel):
                continue

            try:
                target_message = await channel.fetch_message(message_id)
            except discord.NotFound:
                continue

            # Extract the URL from the message content without extra text
            message_link = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

            # Embedの作成
            embed = discord.Embed(
                description=target_message.content,
                color=discord.Color.blue()
            )
            embed.set_author(name=target_message.author.display_name, icon_url=target_message.author.avatar.url)
            embed.timestamp = target_message.created_at

            # メッセージへのリンクを追加
            embed.add_field(name="元のメッセージ", value=f"[こちらをクリック]({message_link})", inline=False)

            await message.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MessageLinkListener(bot))
