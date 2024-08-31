# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
import json
from discord import app_commands
from discord.ext import commands
from core.connect import db  # 非同期データベース接続を想定

class RoleButtonView(discord.ui.View):
    def __init__(self, role_map):
        super().__init__(timeout=None)
        self.role_map = role_map
        # 各ロールに対応するボタンを追加
        for emoji, role_id in self.role_map.items():
            self.add_item(RoleButton(label=f"Option {emoji}", role_id=role_id, emoji=emoji))

class RoleButton(discord.ui.Button):
    def __init__(self, label, role_id, emoji):
        super().__init__(label=label, style=discord.ButtonStyle.primary, custom_id=f"role_{role_id}", emoji=emoji)
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        # ボタンのカスタムIDからロールIDを取得
        role = interaction.guild.get_role(self.role_id)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"{role.name} ロールを削除しました。", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"{role.name} ロールを付与しました。", ephemeral=True)

class RolePanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_panels = {}  # ロールパネル情報を保持する辞書
        bot.loop.create_task(self.initialize_database())
        bot.loop.create_task(self.load_role_panels())  # 起動時にロールパネル情報をロードする

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

    async def load_role_panels(self):
        # データベースからロールパネル情報をロード
        select_query = "SELECT message_id, role_map FROM role_panels"
        results = await db.execute_query(select_query)

        if results:
            for row in results:
                self.role_panels[row["message_id"]] = json.loads(row["role_map"])

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
            description=description or "ボタンをクリックしてロールを取得しましょう！",
        )
        for i, role in enumerate(roles):
            embed.add_field(name=f"Option {i+1}", value=role.mention, inline=False)

        role_map = {emoji: role.id for emoji, role in zip(emojis, roles)}
        role_map_json = json.dumps(role_map)  # 辞書をJSON文字列に変換

        insert_query = """
        INSERT INTO role_panels (message_id, guild_id, channel_id, role_map)
        VALUES ($1, $2, $3, $4)
        """
        message = await interaction.channel.send(embed=embed, view=RoleButtonView(role_map))
        await db.execute_query(insert_query, (message.id, interaction.guild.id, interaction.channel.id, role_map_json))

        # メモリ内にロールパネルを保持
        self.role_panels[message.id] = role_map

        await interaction.followup.send("ロールパネルを作成しました。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RolePanel(bot))
