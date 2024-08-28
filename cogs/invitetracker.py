# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
from core.connect import db

class InviteTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_db()

    # 初期化とマイグレーション用メソッド
    def init_db(self):
        db.execute_query("""
        CREATE TABLE IF NOT EXISTS invite_tracker_settings (
            guild_id BIGINT PRIMARY KEY,
            is_enabled BOOLEAN NOT NULL,
            channel_id BIGINT
        )
        """)
        db.execute_query("""
        CREATE TABLE IF NOT EXISTS invite_tracker (
            guild_id BIGINT NOT NULL,
            inviter_id BIGINT NOT NULL,
            invitee_id BIGINT NOT NULL,
            PRIMARY KEY (guild_id, invitee_id)
        )
        """)
        db.execute_query("""
        CREATE TABLE IF NOT EXISTS invite_counts (
            guild_id BIGINT NOT NULL,
            inviter_id BIGINT NOT NULL,
            invite_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, inviter_id)
        )
        """)

    # サーバー設定を取得
    def get_server_settings(self, guild_id):
        result = db.execute_query("SELECT is_enabled, channel_id FROM invite_tracker_settings WHERE guild_id = %s", (guild_id,))
        if result:
            # タプルから辞書形式に変換
            return {'is_enabled': result[0][0], 'channel_id': result[0][1]}
        return None

    # 招待者を取得
    def get_inviter(self, guild_id, invitee_id):
        result = db.execute_query("SELECT inviter_id FROM invite_tracker WHERE guild_id = %s AND invitee_id = %s", (guild_id, invitee_id))
        return result[0][0] if result else None

    # 招待者を設定
    def set_inviter(self, guild_id, inviter_id, invitee_id):
        db.execute_query("INSERT INTO invite_tracker (guild_id, inviter_id, invitee_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", (guild_id, inviter_id, invitee_id))
        db.execute_query("INSERT INTO invite_counts (guild_id, inviter_id, invite_count) VALUES (%s, %s, 1) ON CONFLICT (guild_id, inviter_id) DO UPDATE SET invite_count = invite_counts.invite_count + 1", (guild_id, inviter_id))

    # 招待数を減らす
    def decrement_invite(self, guild_id, inviter_id):
        db.execute_query("UPDATE invite_counts SET invite_count = invite_count - 1 WHERE guild_id = %s AND inviter_id = %s AND invite_count > 0", (guild_id, inviter_id))

    # 招待数を取得
    def get_invite_count(self, guild_id, inviter_id):
        result = db.execute_query("SELECT invite_count FROM invite_counts WHERE guild_id = %s AND inviter_id = %s", (guild_id, inviter_id))
        return result[0][0] if result else 0

    # メンバーが参加したときのイベント
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = self.get_server_settings(member.guild.id)
        if not settings or not settings['is_enabled']:
            return

        inviter = member.guild.get_member(member.inviter.id) if hasattr(member, 'inviter') else None
        if inviter:
            self.set_inviter(member.guild.id, inviter.id, member.id)

        if settings['channel_id']:
            channel = member.guild.get_channel(settings['channel_id'])
            if channel:
                embed = discord.Embed(
                    title=f"{member.name}さんが{member.guild.name}に参加しました。",
                    description=f"{member.mention}は{inviter.mention}からの招待です。現在{self.get_invite_count(member.guild.id, inviter.id)}人招待しています。" if inviter else f"{member.mention}さんが参加しました。",
                    color=discord.Color.green()
                )
                await channel.send(embed=embed)

    # メンバーが退出したときのイベント
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        settings = self.get_server_settings(member.guild.id)
        if not settings or not settings['is_enabled']:
            return

        inviter_id = self.get_inviter(member.guild.id, member.id)
        if inviter_id:
            # 招待数をデクリメント
            self.decrement_invite(member.guild.id, inviter_id)

        if settings['channel_id']:
            channel = member.guild.get_channel(settings['channel_id'])
            if channel:
                inviter = member.guild.get_member(inviter_id)
                embed = discord.Embed(
                    title=f"{member.name}さんが{member.guild.name}を退出しました。",
                    description=f"{member.mention}は{inviter.mention}からの招待でした。現在{self.get_invite_count(member.guild.id, inviter.id)}人招待しています。" if inviter else f"{member.mention}さんが退出しました。",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)

    # コマンド: /invitetracker-set
    @commands.command()
    async def invitetracker_set(self, ctx, is_enabled: bool, channel: discord.TextChannel):
        db.execute_query("INSERT INTO invite_tracker_settings (guild_id, is_enabled, channel_id) VALUES (%s, %s, %s) ON CONFLICT (guild_id) DO UPDATE SET is_enabled = %s, channel_id = %s", (ctx.guild.id, is_enabled, channel.id, is_enabled, channel.id))
        await ctx.send(f"招待トラッカーを{'有効' if is_enabled else '無効'}に設定し、チャンネルを {channel.mention} に設定しました。")

    # コマンド: /invitetracker
    @commands.command()
    async def invitetracker(self, ctx):
        invite_count = self.get_invite_count(ctx.guild.id, ctx.author.id)
        await ctx.send(f"{ctx.author.mention}さんはこれまでに{invite_count}人を招待しました。")

    # コマンド: /invitetracker-server
    @commands.command()
    async def invitetracker_server(self, ctx):
        result = db.execute_query("SELECT inviter_id, invite_count FROM invite_counts WHERE guild_id = %s ORDER BY invite_count DESC LIMIT 10", (ctx.guild.id,))
        embed = discord.Embed(title=f"{ctx.guild.name}の招待ランキング", color=discord.Color.blue())
        for inviter_id, count in result:
            inviter = ctx.guild.get_member(inviter_id)
            embed.add_field(name=inviter.display_name if inviter else f"ID: {inviter_id}", value=f"{count} 人", inline=False)
        await ctx.send(embed=embed)


# Cogをbotに追加する関数
async def setup(bot):
    await bot.add_cog(InviteTracker(bot))
