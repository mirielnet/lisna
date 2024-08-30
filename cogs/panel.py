# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
import json
from discord import app_commands
from discord.ext import commands
from core.connect import db  # 非同期データベース接続を想定

class RolePanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.initialize_database())

    async def initialize_database(self):
        # role_panels テーブルの作成クエリ
        create_table_query = """
        CREATE TABLE IF NOT EXISTS role_panels (
            message_id BIGINT PRIMARY KEY,
            guild_id BIGINT NOT NULL,
            channel_id BIGINT NOT NULL,
            role_map JSONB NOT NULL
        );
        """
        await db.execute_query(create_table_query)

        # discord_channel_messages テーブルの作成クエリ
        create_discord_channel_messages_query = """
        CREATE TABLE IF NOT EXISTS discord_channel_messages (
            message_id BIGINT PRIMARY KEY,
            channel_id BIGINT NOT NULL,
            guild_id BIGINT NOT NULL,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await db.execute_query(create_discord_channel_messages_query)

    @app_commands.command(
        name="panel", description="指定されたロールパネルを作成します。"
    )
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
        description="説明を入力してください。",
    )
    async def panel(
        self,
        interaction: discord.Interaction,
        role1: discord.Role = None,
        role2: discord.Role = None,
        role3: discord.Role = None,
        role4: discord.Role = None,
        role5: discord.Role = None,
        role6: discord.Role = None,
        role7: discord.Role = None,
        role8: discord.Role = None,
        role9: discord.Role = None,
        role10: discord.Role = None,
        description: str = None,
    ):
        await interaction.response.defer(ephemeral=True)

        roles = [role1, role2, role3, role4, role5, role6, role7, role8, role9, role10]
        roles = [role for role in roles if role is not None]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        embed = discord.Embed(
            title="Role Panel",
            description=description or "リアクションを付けてロールを取得しましょう！",
        )
        for i, role in enumerate(roles):
            embed.add_field(name=f"Option {i+1}", value=role.mention, inline=False)

        message = await interaction.channel.send(embed=embed)

        role_map = {emoji: role.id for emoji, role in zip(emojis, roles)}
        role_map_json = json.dumps(role_map)  # 辞書をJSON文字列に変換

        insert_query = """
        INSERT INTO role_panels (message_id, guild_id, channel_id, role_map)
        VALUES ($1, $2, $3, $4)
        """
        await db.execute_query(insert_query, (message.id, interaction.guild.id, interaction.channel.id, role_map_json))

        for emoji in emojis[: len(roles)]:
            await message.add_reaction(emoji)

        await interaction.followup.send("ロールパネルを作成しました。", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        select_query = """
        SELECT role_map FROM role_panels WHERE message_id = $1
        """
        result = await db.execute_query(select_query, (payload.message_id,))
        if not result:
            return

        role_map_json = result[0]['role_map']

        # role_map_jsonがすでに辞書である場合の対処
        if isinstance(role_map_json, str):
            role_map = json.loads(role_map_json)  # JSON文字列を辞書に変換
        else:
            role_map = role_map_json

        role_id = role_map.get(str(payload.emoji))
        if role_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        role = guild.get_role(role_id)
        if role is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        await member.add_roles(role)
        channel = guild.get_channel(payload.channel_id)
        if channel:
            await channel.send(
                f"{member.mention} に {role.name} ロールが付与されました。",
                delete_after=10,
            )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        select_query = """
        SELECT role_map FROM role_panels WHERE message_id = $1
        """
        result = await db.execute_query(select_query, (payload.message_id,))
        if not result:
            return

        role_map_json = result[0]['role_map']

        # role_map_jsonがすでに辞書である場合の対処
        if isinstance(role_map_json, str):
            role_map = json.loads(role_map_json)  # JSON文字列を辞書に変換
        else:
            role_map = role_map_json

        role_id = role_map.get(str(payload.emoji))
        if role_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        role = guild.get_role(role_id)
        if role is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        await member.remove_roles(role)
        channel = guild.get_channel(payload.channel_id)
        if channel:
            await channel.send(
                f"{member.mention} から {role.name} ロールが削除されました。",
                delete_after=10,
            )

        # メッセージが存在しない場合はデータベースから削除
        delete_query = """
        DELETE FROM role_panels WHERE message_id = $1 AND NOT EXISTS (
            SELECT 1 FROM discord_channel_messages WHERE message_id = $1
        )
        """
        await db.execute_query(delete_query, (payload.message_id,))

async def setup(bot):
    role_panel = RolePanel(bot)
    await bot.add_cog(role_panel)
