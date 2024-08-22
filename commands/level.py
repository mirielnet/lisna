# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os

DB_PATH = "./db/level.db"

# Create database if not exists
def setup_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                     user_id INTEGER PRIMARY KEY,
                     server_id INTEGER,
                     xp INTEGER DEFAULT 0,
                     level INTEGER DEFAULT 1
                     )''')
        # Server settings table
        c.execute('''CREATE TABLE IF NOT EXISTS settings (
                     server_id INTEGER PRIMARY KEY,
                     level_enabled INTEGER DEFAULT 0,
                     notify_channel_id INTEGER
                     )''')

setup_db()

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_level(self, xp):
        # Simple XP to level conversion formula
        return min(100, int(xp ** (1/2.5)))

    async def handle_error(self, interaction: discord.Interaction, error_message: str):
        """Handles errors by sending an ephemeral message to the user."""
        embed = discord.Embed(title="エラー", description=error_message, color=0xff0000)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="level", description="あなたのレベルを表示します。"
    )
    async def level(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        server_id = interaction.guild.id

        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute('''SELECT xp, level FROM users WHERE user_id = ? AND server_id = ?''', (user_id, server_id))
                result = c.fetchone()

                if result:
                    xp, level = result
                else:
                    xp, level = 0, 1

                embed = discord.Embed(title="レベル", description=f"{interaction.user.name}さんのレベル情報", color=0x00ff00)
                embed.add_field(name="レベル", value=level)
                embed.add_field(name="XP", value=xp)
                await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await self.handle_error(interaction, "レベル情報の取得中にエラーが発生しました。")

    @app_commands.command(
        name="level-server", description="サーバーのレベルランキングを表示します。"
    )
    async def level_server(self, interaction: discord.Interaction):
        server_id = interaction.guild.id

        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute('''SELECT user_id, level FROM users WHERE server_id = ? ORDER BY level DESC LIMIT 10''', (server_id,))
                rankings = c.fetchall()

            embed = discord.Embed(title="レベルランキング", description=f"{interaction.guild.name}のトップ10", color=0x00ff00)

            for i, (user_id, level) in enumerate(rankings, 1):
                user = await self.bot.fetch_user(user_id)
                embed.add_field(name=f"{i}. {user.name}", value=f"レベル {level}", inline=False)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await self.handle_error(interaction, "レベルランキングの取得中にエラーが発生しました。")

    @app_commands.command(
        name="level-settings", description="サーバーのレベル設定を行います。"
    )
    @app_commands.describe(enable="レベルシステムを有効化するかどうか")
    @app_commands.describe(notify_channel="レベルアップ通知チャンネル (オプション)")
    @commands.has_permissions(administrator=True)
    async def level_settings(
        self,
        interaction: discord.Interaction,
        enable: bool,
        notify_channel: discord.TextChannel = None
    ):
        server_id = interaction.guild.id

        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute('''REPLACE INTO settings (server_id, level_enabled, notify_channel_id)
                             VALUES (?, ?, ?)''', (server_id, int(enable), notify_channel.id if notify_channel else None))
                conn.commit()

            status = "有効" if enable else "無効"
            embed = discord.Embed(title="レベル設定", description=f"レベルシステムが{status}になりました。", color=0x00ff00)
            if notify_channel:
                embed.add_field(name="通知チャンネル", value=notify_channel.mention)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await self.handle_error(interaction, "設定の更新中にエラーが発生しました。")

    def update_xp(self, user_id, server_id, xp_gain):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute('''SELECT xp, level FROM users WHERE user_id = ? AND server_id = ?''', (user_id, server_id))
                result = c.fetchone()

                if result:
                    xp, level = result
                    new_xp = xp + xp_gain
                    new_level = self.get_level(new_xp)

                    if new_level > level:
                        # Notify level up
                        c.execute('''SELECT notify_channel_id FROM settings WHERE server_id = ?''', (server_id,))
                        channel_id = c.fetchone()[0]
                        if channel_id:
                            channel = self.bot.get_channel(channel_id)
                            user = self.bot.get_user(user_id)
                            if channel and user:
                                msg = f"{user.mention} レベルが{new_level}に上がりました！！ おめでとうございます！"
                                self.bot.loop.create_task(channel.send(msg))
                    c.execute('''UPDATE users SET xp = ?, level = ? WHERE user_id = ? AND server_id = ?''', (new_xp, new_level, user_id, server_id))
                else:
                    c.execute('''INSERT INTO users (user_id, server_id, xp, level) VALUES (?, ?, ?, 1)''', (user_id, server_id, xp_gain))

        except Exception as e:
            print(f"XPの更新中にエラーが発生しました: {e}")

async def setup(bot):
    await bot.add_cog(LevelSystem(bot))
