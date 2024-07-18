# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
from discord import app_commands

class RolePanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="panel", description="指定されたロールパネルを作成します。")
    @app_commands.describe(
        role1="ロール1を選択してください。",
        role2="ロール2を選択してください。",
        role3="ロール3を選択してください。",
        role4="ロール4を選択してください。",
        role5="ロール5を選択してください。",
        role6="ロール6を選択してください。",
        role7="ロール7を選択してください。",
        role8="ロール8を選択してください。",
        role9="ロール9を選択してください。",
        role10="ロール10を選択してください。",
        description="説明を入力してください。"
    )
    async def panel(self, interaction: discord.Interaction, role1: discord.Role = None, role2: discord.Role = None, role3: discord.Role = None, role4: discord.Role = None, role5: discord.Role = None, role6: discord.Role = None, role7: discord.Role = None, role8: discord.Role = None, role9: discord.Role = None, role10: discord.Role = None, description: str = None):
        await interaction.response.defer(ephemeral=True)

        roles = [role1, role2, role3, role4, role5, role6, role7, role8, role9, role10]
        roles = [role for role in roles if role is not None]
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        embed = discord.Embed(title="Role Panel", description=description or "リアクションを付けてロールを取得しましょう！")
        for i, role in enumerate(roles):
            embed.add_field(name=emojis[i], value=role.mention, inline=False)

        # Send the embed message and get the message object
        message = await interaction.followup.send(content="ロールパネルを作成しました。", ephemeral=True)

        # Add reactions to the message
        for emoji in emojis[:len(roles)]:
            await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        channel = reaction.message.channel
        message = reaction.message

        if not message.embeds:
            return

        embed = message.embeds[0]
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        for i, field in enumerate(embed.fields):
            if str(reaction.emoji) == emojis[i]:
                role_id = int(field.value.strip('<@&>'))
                role = user.guild.get_role(role_id)
                if role:
                    await user.add_roles(role)
                    await channel.send(f"{user.mention} に {role.name} ロールが付与されました。", delete_after=10)
                break

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user.bot:
            return

        channel = reaction.message.channel
        message = reaction.message

        if not message.embeds:
            return

        embed = message.embeds[0]
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        for i, field in enumerate(embed.fields):
            if str(reaction.emoji) == emojis[i]:
                role_id = int(field.value.strip('<@&>'))
                role = user.guild.get_role(role_id)
                if role:
                    await user.remove_roles(role)
                    await channel.send(f"{user.mention} から {role.name} ロールが削除されました。", delete_after=10)
                break

async def setup(bot):
    await bot.add_cog(RolePanel(bot))
