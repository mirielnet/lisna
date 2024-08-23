# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
import random
from discord import app_commands
from discord.ext import commands


class DiceGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dice", description="チンチロリンで遊びます。")
    async def dice(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # チンチロリンのロール
        dice_rolls = [random.randint(1, 6) for _ in range(3)]
        dice_result = " | ".join(f"🎲 {roll}" for roll in dice_rolls)

        # チンチロリンの結果判定
        roll_set = set(dice_rolls)
        if len(roll_set) == 1:
            result = "ピンゾロ! 全て同じ目が出ました!"
        elif len(roll_set) == 2:
            for roll in roll_set:
                if dice_rolls.count(roll) == 2:
                    result = f"目が揃いました! ペア: {roll}, {roll}"
        else:
            result = "ハズレです... 次の挑戦を！"

        # Embed作成
        embed = discord.Embed(
            title="チンチロリン",
            description=f"サイコロの結果:\n{dice_result}",
            color=discord.Color.blue(),
        )
        embed.add_field(name="結果", value=result, inline=False)

        # 結果を送信
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(DiceGame(bot))
