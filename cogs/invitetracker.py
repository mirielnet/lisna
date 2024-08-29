# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
from discord import app_commands, ui
from core.connect import db

class InviteTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.server_settings = {}
        self.invites = {}
        bot.loop.create_task(self.load_invites())

    async def load_invites(self):
        await self.bot.wait_until_ready()
        # すべてのサーバーの招待情報をロード
        for guild in self.bot.guilds:
            try:
                self.invites[guild.id] = await guild.invites()
            except:
                pass

    def find_invite_by_code(self, inv_list, code):
        for inv in inv_list:
            if inv.code == code:
                return inv

    async def init_db(self):
        # データベースの初期化とマイグレーション
        db.execute_query("""
        CREATE TABLE IF NOT EXISTS invite_tracker_settings (
            guild_id BIGINT PRIMARY KEY,
            is_enabled BOOLEAN NOT NULL,
            channel_id BIGINT
        );
        """)
        
        db.execute_query("""
        CREATE TABLE IF NOT EXISTS invite_tracker (
            guild_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            inviter_id BIGINT,
            invites INT DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
        );
        """)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.init_db()
        print("InviteTrackerが起動しました。")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = self.get_server_settings(member.guild.id)
        if not settings or not settings['is_enabled']:
            return
        
        # 招待を特定
        invs_before = self.invites[member.guild.id]
        invs_after = await member.guild.invites()
        self.invites[member.guild.id] = invs_after
        inviter = None

        for invite in invs_before:
            if invite.uses < self.find_invite_by_code(invs_after, invite.code).uses:
                inviter = invite.inviter
                break
        
        # データベースに保存
        self.add_invite(member.guild.id, member.id, inviter.id if inviter else None)

        # メッセージ送信
        if settings['channel_id']:
            channel = member.guild.get_channel(settings['channel_id'])
            if channel:
                embed = discord.Embed(
                    title=f"{member.name}さんが{member.guild.name}に参加しました！",
                    description=f"{member.mention}は{inviter.mention}からの招待です。現在{self.get_invite_count(member.guild.id, inviter.id)}人招待しています。",
                    color=discord.Color.green()
                )
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        settings = self.get_server_settings(member.guild.id)
        if not settings or not settings['is_enabled']:
            return
    
        inviter_id = self.get_inviter(member.guild.id, member.id)
        if inviter_id:
            # 招待数をデクリメント
            self.decrement_invite(member.guild.id, inviter_id)
    
        # メッセージ送信
        if settings['channel_id']:
            channel = member.guild.get_channel(settings['channel_id'])
            if channel:
                inviter = member.guild.get_member(inviter_id) if inviter_id else None
                inviter_mention = inviter.mention if inviter else "不明な招待者"
    
                embed = discord.Embed(
                    title=f"{member.name}さんが{member.guild.name}を退出しました。",
                    description=f"{member.mention}は{inviter_mention}からの招待でした。現在{self.get_invite_count(member.guild.id, inviter_id)}人招待しています。" if inviter_id else f"{member.mention}の招待者は不明です。",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)    

    @app_commands.command(name="invitetracker-set", description="Invite Trackerの設定を行います。")
    @app_commands.describe(is_enabled="機能を有効にするかどうか", channel="入出メッセージのチャンネルを選択してください。")
    async def set_invite_tracker(self, interaction: discord.Interaction, is_enabled: bool, channel: discord.TextChannel = None):
        self.update_server_settings(interaction.guild.id, is_enabled, channel.id if channel else None)
        await interaction.response.send_message(f"Invite Tracker設定を更新しました。")

    @app_commands.command(name="invitetracker", description="自分の招待数を確認します。")
    async def invite_tracker(self, interaction: discord.Interaction):
        invite_count = self.get_invite_count(interaction.guild.id, interaction.user.id)
        embed = discord.Embed(
            title=f"{interaction.user.name}の招待数",
            description=f"あなたは現在{invite_count}人を招待しています。",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="invitetracker-server", description="サーバーの招待数ランキングを表示します。")
    async def invite_tracker_server(self, interaction: discord.Interaction):
        # ランキングの取得
        rankings = self.get_server_ranking(interaction.guild.id)
        embeds = []
        for i in range(0, len(rankings), 10):
            embed = discord.Embed(
                title=f"{interaction.guild.name}の招待ランキング",
                description="\n".join([f"{idx + 1}. {self.bot.get_user(row[1]).mention}: {row[2]}招待" for idx, row in enumerate(rankings[i:i + 10])]),
                color=discord.Color.purple()
            )
            embeds.append(embed)
        
        paginator = ui.Paginator(embeds=embeds, timeout=60)
        await paginator.send(interaction)

    # Helper Methods for DB Operations
    def get_server_settings(self, guild_id):
        result = db.execute_query("SELECT is_enabled, channel_id FROM invite_tracker_settings WHERE guild_id = %s", (guild_id,))
        if result:
            return {'is_enabled': result[0][0], 'channel_id': result[0][1]}  # 辞書形式で返す
        return None

    def update_server_settings(self, guild_id, is_enabled, channel_id):
        db.execute_query("""
        INSERT INTO invite_tracker_settings (guild_id, is_enabled, channel_id) VALUES (%s, %s, %s)
        ON CONFLICT (guild_id) DO UPDATE SET is_enabled = EXCLUDED.is_enabled, channel_id = EXCLUDED.channel_id
        """, (guild_id, is_enabled, channel_id))

    def add_invite(self, guild_id, user_id, inviter_id):
        # 招待数を正しくインクリメント
        db.execute_query("""
        INSERT INTO invite_tracker (guild_id, user_id, inviter_id, invites) 
        VALUES (%s, %s, %s, 1)
        ON CONFLICT (guild_id, user_id) 
        DO UPDATE SET invites = invite_tracker.invites + 1
        """, (guild_id, inviter_id, inviter_id))

    def get_inviter(self, guild_id, user_id):
        result = db.execute_query("SELECT inviter_id FROM invite_tracker WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        return result[0][0] if result else None

    def decrement_invite(self, guild_id, inviter_id):
        db.execute_query("UPDATE invite_tracker SET invites = invites - 1 WHERE guild_id = %s AND user_id = %s", (guild_id, inviter_id))

    def get_invite_count(self, guild_id, user_id):
        result = db.execute_query("SELECT invites FROM invite_tracker WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        return result[0][0] if result else 0

    def get_server_ranking(self, guild_id):
        return db.execute_query("SELECT guild_id, user_id, invites FROM invite_tracker WHERE guild_id = %s ORDER BY invites DESC", (guild_id,))

async def setup(bot):
    await bot.add_cog(InviteTracker(bot))
