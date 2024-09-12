# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands


class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="userinfo", description="指定したユーザーの情報を取得します。"
    )
    @app_commands.describe(user="ユーザーを指定してください。")
    async def userinfo(
        self, interaction: discord.Interaction, user: discord.User = None
    ):
        user = user or interaction.user  # If no user is specified, use the command user

        # Profile URL
        profile_url = f"https://discord.com/users/{user.id}"

        embed = discord.Embed(
            color=discord.Color.blue(),
            title=f"{user} の情報",
            url=profile_url,  # Embed profile URL
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="ユーザータグ", value=user, inline=False)
        embed.add_field(name="ID", value=user.id, inline=False)
        embed.add_field(
            name="アカウント作成日",
            value=user.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            inline=False,
        )

        # Check if user is a bot
        embed.add_field(
            name="ボット", value="はい" if user.bot else "いいえ", inline=False
        )

        # Fetch user badges (if available)
        if user.public_flags:
            badges = [flag.name for flag in user.public_flags.all()]
            embed.add_field(
                name="バッジ",
                value=", ".join(badges) if badges else "なし",
                inline=False,
            )
        else:
            embed.add_field(name="バッジ", value="なし", inline=False)

        # Fetch guild-specific information if available
        if interaction.guild:
            member = interaction.guild.get_member(user.id)
            if member:
                joined_at = member.joined_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                roles = [
                    role.name
                    for role in member.roles
                    if role != interaction.guild.default_role
                ]

                embed.add_field(name="サーバー参加日", value=joined_at, inline=False)
                embed.add_field(
                    name="ロール",
                    value="\n".join(roles) if roles else "なし",
                    inline=False,
                )

        try:
            await interaction.response.send_message(embed=embed)
        except Exception as error:
            print(f"Error sending user info: {error}")
            await interaction.response.send_message(
                "コマンドの実行中にエラーが発生しました。", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(UserInfo(bot))
