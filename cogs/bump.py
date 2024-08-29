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
        # Embedが存在するか確認
        if not message.embeds:
            print("Embedが存在しません。")
            return
        
        embed = message.embeds[0]
        
        # DISBOARDのBUMP通知処理 (2時間後)
        if message.author.id == 302050872383242240:  # DISBOARDのBOT ID
            embed_description = embed.description if embed.description else ""
            print(f"DISBOARD Embed Description: {embed_description}")

            if "表示順をアップしたよ" in embed_description or "Bump done" in embed_description:
                await self.send_bump_notification(message.channel, 7200, "BUMPの時間です\n</bump:947088344167366698>でサーバーの表示順位を上げよう！")

        # DIS速のBUMP通知処理 (1時間後)
        elif message.author.id == 761562078095867916:  # DIS速のBOT ID
            embed_author_name = embed.author.name if embed.author and embed.author.name else ""
            print(f"DIS速 Embed Author Name: {embed_author_name}")

            if "アップしたよ!" in embed_author_name:
                await self.send_bump_notification(message.channel, 3600, "UPの時間です\n</up:1135405664852783157>でサーバーの表示順位を上げよう！")

    async def send_bump_notification(self, channel, delay, reminder_text):
        try:
            await channel.send(embed=discord.Embed(
                title="BUMP通知",
                description="UPを受信しました\nリマインダーを設定しました",
                color=discord.Color.white()
            ))

            # リマインダーを設定（指定された遅延後に通知を送信）
            await asyncio.sleep(delay)  # delay秒後にリマインダーを送信
            await channel.send(embed=discord.Embed(
                title="BUMP通知",
                description=reminder_text,
                color=discord.Color.green() if "UPの時間" in reminder_text else discord.Color.white()
            ))
        except discord.Forbidden:
            print(f"Cannot send messages in {channel.name} due to lack of permissions")

async def setup(bot):
    await bot.add_cog(BumpNotify(bot))
