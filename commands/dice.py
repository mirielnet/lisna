# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import random
import discord
from discord.ext import commands

class DiceGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="chinchiro", description="チンチロリンをプレイします。")
    async def chinchiro(self, ctx):
        await ctx.send("🎲 チンチロリンが始まります！")

        # 3つのサイコロを振る
        dice_rolls = [random.randint(1, 6) for _ in range(3)]
        result = self.calculate_result(dice_rolls)

        # Embedメッセージの作成
        embed = discord.Embed(
            title="チンチロリン",
            description=f"{ctx.author.mention} の結果",
            color=discord.Color.blue()
        )
        embed.add_field(name="🎲 サイコロの目", value=" ".join([f"🎲{dice}" for dice in dice_rolls]), inline=False)
        embed.add_field(name="結果", value=result, inline=False)

        await ctx.send(embed=embed)

    def calculate_result(self, rolls):
        """ チンチロリンの結果を計算します """
        roll_count = {roll: rolls.count(roll) for roll in set(rolls)}
        if len(roll_count) == 1:
            return "ピンゾロ！"
        elif 2 in roll_count.values():
            for roll, count in roll_count.items():
                if count == 2:
                    return f"{roll} のゾロ目"
        else:
            return "役無し"

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await ctx.send(f"エラーが発生しました: {error}")
        print(f"コマンドエラー: {error}")

async def setup(bot):
    await bot.add_cog(DiceGame(bot))
