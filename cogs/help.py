# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import importlib.util
import inspect
import os

import discord
from discord import app_commands
from discord.ext import commands


class HelpMenu(discord.ui.View):
    def __init__(self, embeds, timeout=60):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current_page = 0

    @discord.ui.button(
        label="Previous", style=discord.ButtonStyle.primary, disabled=True
    )
    async def previous_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.current_page -= 1
        if self.current_page == 0:
            button.disabled = True
        self.children[1].disabled = False  # Enable the "Next" button
        await interaction.response.edit_message(
            embed=self.embeds[self.current_page], view=self
        )

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.current_page += 1
        if self.current_page == len(self.embeds) - 1:
            button.disabled = True
        self.children[0].disabled = False  # Enable the "Previous" button
        await interaction.response.edit_message(
            embed=self.embeds[self.current_page], view=self
        )


class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help", description="すべてのスラッシュコマンドとその説明を表示します。"
    )
    async def help(self, interaction: discord.Interaction):
        embeds = []
        embed = discord.Embed(
            title="ヘルプ",
            description="使用可能なスラッシュコマンド一覧",
            color=0x00FF00,
        )

        commands_folder = "./cogs"
        field_count = 0

        for file in os.listdir(commands_folder):
            if file.endswith(".py"):
                module_name = file[:-3]
                module_path = os.path.join(commands_folder, file)

                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for name, obj in vars(module).items():
                    if inspect.isclass(obj) and issubclass(obj, commands.Cog):
                        cog = obj(self.bot)
                        for command in cog.__cog_app_commands__:
                            embed.add_field(
                                name=f"/{command.name}",
                                value=command.description or "説明なし",
                                inline=False,
                            )
                            field_count += 1

                            # 25フィールドごとに新しいEmbedを作成
                            if field_count == 25:
                                embeds.append(embed)
                                embed = discord.Embed(
                                    title="ヘルプ",
                                    description="使用可能なスラッシュコマンド一覧",
                                    color=0x00FF00,
                                )
                                field_count = 0

        # 最後のEmbedを追加
        if field_count > 0:
            embeds.append(embed)

        view = HelpMenu(embeds)

        await interaction.response.send_message(
            embed=embeds[0], view=view, ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
