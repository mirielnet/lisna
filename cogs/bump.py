# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
import asyncio

class BumpNotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # メッセージの送信者がDIS速のボットであることを確認
        if message.author.id == 761562078095867916:  # ここにDIS速のボットIDを入れてください
            if message.embeds:
                embed = message.embeds[0]  # 最初のEmbedを取得
                
                # Embedのcommand部分に「/dissoku up」が含まれているかを確認
                if "command: /dissoku up" in embed.description:
                    await self.send_initial_notification(message.channel, "UP通知", "UPを受信しました\n1時間後に通知します")
                    await self.send_bump_notification(message.channel, 3600, "UPの時間です\n</up:1135405664852783157>でサーバーの表示順位を上げよう！")

        # DISBOARDのボットIDでメッセージを検知
        elif message.author.id == 302050872383242240:  # DISBOARDのボットID
            if message.embeds:
                embed = message.embeds[0]  # 最初のEmbedを取得

                # Embedのdescriptionに特定の内容が含まれているかを確認
                if "表示順をアップしたよ" in embed.description:
                    await self.send_initial_notification(message.channel, "BUMP通知", "BUMPを受信しました\n2時間後に通知します")
                    await self.send_bump_notification(message.channel, 7200, "BUMPの時間です\n</bump:947088344167366698>でサーバーの表示順位を上げよう！")

    async def send_initial_notification(self, channel, title, description):
        try:
            await channel.send(embed=discord.Embed(
                title=title,
                description=description,
                color=discord.Color.white()
            ))
        except discord.Forbidden:
            print(f"Cannot send messages in {channel.name} due to lack of permissions")

    async def send_bump_notification(self, channel, delay, reminder_text):
        try:
            # リマインダーを設定（指定された遅延後に通知を送信）
            await asyncio.sleep(delay)
            await channel.send(embed=discord.Embed(
                title="BUMP通知" if "BUMPの時間" in reminder_text else "UP通知",
                description=reminder_text,
                color=discord.Color.green()
            ))
        except discord.Forbidden:
            print(f"Cannot send messages in {channel.name} due to lack of permissions")

async def setup(bot):
    await bot.add_cog(BumpNotify(bot))
