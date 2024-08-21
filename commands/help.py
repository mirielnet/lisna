# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
import os
import importlib.util

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="すべてのスラッシュコマンドとその説明を表示します。")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="ヘルプ", description="使用可能なスラッシュコマンド一覧", color=0x00ff00)

        command_dir = "./commands"
        command_files = [f for f in os.listdir(command_dir) if f.endswith(".py")]

        for command_file in command_files:
            module_name = command_file[:-3]
            module_path = os.path.join(command_dir, command_file)

            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "setup"):
                for name, obj in vars(module).items():
                    if isinstance(obj, app_commands.Command):
                        embed.add_field(
                            name=f"/{obj.name}",
                            value=obj.description or "説明なし",
                            inline=False,
                        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
