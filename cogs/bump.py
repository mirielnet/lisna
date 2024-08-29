# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
import asyncio

class BumpNotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.application_command:
            # DIS速のコマンドが実行された場合
            if interaction.user.id == 761562078095867916 and "up" in interaction.command.name:
                await self.send_initial_notification(interaction.channel, "UP通知", "UPを受信しました\n1時間後に通知します")
                await self.send_bump_notification(interaction.channel, 3600, "UPの時間です\n</up:1135405664852783157>でサーバーの表示順位を上げよう！")
                
            # DISBOARDの /bump コマンド処理
            elif interaction.user.id == 302050872383242240 and interaction.command.name == "bump":
                await self.send_initial_notification(interaction.channel, "BUMP通知", "BUMPを受信しました\n2時間後に通知します")
                await self.send_bump_notification(interaction.channel, 7200, "BUMPの時間です\n</bump:947088344167366698>でサーバーの表示順位を上げよう！")

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
