# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

# SQLite データベース設定
DB_PATH = './db/autorole.db'

def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS autoroles (
            server_id INTEGER PRIMARY KEY,
            role_ids TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_autoroles(server_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT role_ids FROM autoroles WHERE server_id = ?', (server_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0].split(',')
    return []

def set_autoroles(server_id, role_ids):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO autoroles (server_id, role_ids)
        VALUES (?, ?)
    ''', (server_id, ','.join(role_ids)))
    conn.commit()
    conn.close()

def remove_autoroles(server_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM autoroles WHERE server_id = ?', (server_id,))
    conn.commit()
    conn.close()

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        initialize_db()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role_ids = get_autoroles(member.guild.id)
        roles = [member.guild.get_role(int(role_id)) for role_id in role_ids if member.guild.get_role(int(role_id))]
        if roles:
            await member.add_roles(*roles)
            print(f"自動ロールを {member.display_name} に付与しました: {', '.join([role.name for role in roles])}")

    @app_commands.command(name="autorole_set", description="自動ロールを設定します。")
    @app_commands.describe(roles="自動付与するロールを選択してください。")
    @app_commands.checks.has_permissions(administrator=True)
    async def autorole_set(self, interaction: discord.Interaction, roles: discord.Role):
        set_autoroles(interaction.guild.id, [str(role.id) for role in roles])
        await interaction.response.send_message(f"自動ロールを設定しました: {', '.join([role.name for role in roles])}")

    @app_commands.command(name="autorole_update", description="自動ロールを変更します。")
    @app_commands.describe(roles="新しい自動付与するロールを選択してください。")
    @app_commands.checks.has_permissions(administrator=True)
    async def autorole_update(self, interaction: discord.Interaction, roles: discord.Role):
        set_autoroles(interaction.guild.id, [str(role.id) for role in roles])
        await interaction.response.send_message(f"自動ロールを変更しました: {', '.join([role.name for role in roles])}")

    @app_commands.command(name="autorole_remove", description="自動ロールの設定を解除します。")
    @app_commands.checks.has_permissions(administrator=True)
    async def autorole_remove(self, interaction: discord.Interaction):
        remove_autoroles(interaction.guild.id)
        await interaction.response.send_message("自動ロールの設定を解除しました。")

async def setup(bot):
    await bot.add_cog(AutoRole(bot))
