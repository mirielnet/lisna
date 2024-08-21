# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
import os

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Help Service OK.')

    @commands.slash_command(name="help", description="すべてのスラッシュコマンドとその説明を表示します。")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="ヘルプ", description="使用可能なスラッシュコマンド一覧", color=0x00ff00)
        
        command_dir = "./commands"
        command_files = [f for f in os.listdir(command_dir) if f.endswith(".py")]

        for command_file in command_files:
            module_name = command_file[:-3]
            module = __import__(f"commands.{module_name}", fromlist=[module_name])
            if hasattr(module, "setup"):
                for name, obj in vars(module).items():
                    if isinstance(obj, commands.Command):
                        embed.add_field(
                            name=f"/{obj.name}",
                            value=obj.description or "説明なし",
                            inline=False,
                        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
