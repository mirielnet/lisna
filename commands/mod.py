# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_mod():
        async def predicate(interaction: discord.Interaction) -> bool:
            if interaction.user.guild_permissions.manage_messages:
                return True
            await interaction.response.send_message(
                "このコマンドを実行する権限がありません。", ephemeral=True
            )
            return False

        return app_commands.check(predicate)

    @app_commands.command(
        name="timeout", description="指定したユーザーをタイムアウトします。"
    )
    @is_mod()
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration: int,
        reason: str = None,
    ):
        try:
            await member.edit(
                timed_out_until=discord.utils.utcnow() + timedelta(seconds=duration),
                reason=reason,
            )
            await interaction.response.send_message(
                f"{member.display_name} を {duration} 秒間タイムアウトしました。理由: {reason}",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.response.send_message(
                f"タイムアウトに失敗しました: {e}", ephemeral=True
            )

    @app_commands.command(name="kick", description="指定したユーザーをキックします。")
    @is_mod()
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = None,
    ):
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(
                f"{member.display_name} をキックしました。理由: {reason}",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.response.send_message(
                f"キックに失敗しました: {e}", ephemeral=True
            )

    @app_commands.command(name="ban", description="指定したユーザーをバンします。")
    @is_mod()
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = None,
    ):
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(
                f"{member.display_name} をバンしました。理由: {reason}", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"バンに失敗しました: {e}", ephemeral=True
            )


async def setup(bot):
    print("Setting up Mod Cog")
    await bot.add_cog(Mod(bot))
    print("Mod Cog setup complete")
