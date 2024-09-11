# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
from discord import app_commands, ui
from core.connect import db

class InviteTracker(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.server_settings = {}
        self.invites = {}
        bot.loop.create_task(self.load_invites())

    async def load_invites(self) -> None:
        await self.bot.wait_until_ready()
        # すべてのサーバーの招待情報をロード
        for guild in self.bot.guilds:
            try:
                self.invites[guild.id] = await guild.invites()
            except Exception as e:
                print(f"Failed to load invites for {guild.name} ({guild.id}): {e}")

    def find_invite_by_code(self, inv_list, code):
        for inv in inv_list:
            if inv.code == code:
                return inv

    async def init_db(self) -> None:
        # データベースの初期化とマイグレーション
        await db.execute_query("""
        CREATE TABLE IF NOT EXISTS invite_tracker_settings (
            guild_id BIGINT PRIMARY KEY,
            is_enabled BOOLEAN NOT NULL,
            channel_id BIGINT
        );
        """)
        
        await db.execute_query("""
        CREATE TABLE IF NOT EXISTS invite_tracker (
            guild_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            inviter_id BIGINT,
            invites INT DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
        );
        """)

    async def check_if_enabled(self, interaction: discord.Interaction) -> bool:
        # 機能が有効かどうかを確認する関数
        settings = await self.get_server_settings(interaction.guild.id)
        if not settings or not settings['is_enabled']:
            embed = discord.Embed(
                title="レベル機能が無効です",
                description="レベル機能が無効になっています。サーバー管理者にお問い合わせください。",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return False
        return True

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.init_db()
        print("InviteTrackerが起動しました。")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.bot:
            return
    
        # サーバー設定を取得
        settings = await self.get_server_settings(member.guild.id)
        if not settings or not settings['is_enabled']:
            return
    
        # 以前と現在の招待リストを取得
        invs_before = self.invites.get(member.guild.id, [])
        invs_after = await member.guild.invites()  # 最新の招待リストを取得
        self.invites[member.guild.id] = invs_after  # 最新のリストに更新
    
        inviter = None
    
        # 以前と現在の招待状況を比較
        for invite in invs_before:
            after_invite = self.find_invite_by_code(invs_after, invite.code)
            if after_invite and invite.uses < after_invite.uses:
                inviter = invite.inviter  # 招待者を特定
                break
    
        if inviter is None:
            return
    
        # 招待者をデータベースに保存し、招待数を増加
        await self.add_invite(member.guild.id, member.id, inviter.id)
    
        # チャンネルにメッセージ送信
        if settings['channel_id']:
            channel = member.guild.get_channel(settings['channel_id'])
            if channel:
                invite_count = await self.get_invite_count(member.guild.id, inviter.id)
                embed = discord.Embed(
                    title=f"{member.name}さんが{member.guild.name}に参加しました！",
                    description=f"{member.mention}は{inviter.mention}からの招待です。現在{invite_count}人招待しています。",
                    color=discord.Color.green()
                )
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        # サーバー設定を取得
        settings = await self.get_server_settings(member.guild.id)
        if not settings or not settings['is_enabled']:
            return
    
        inviter_id = await self.get_inviter(member.guild.id, member.id)
        if inviter_id:
            # 招待数をデクリメント
            await self.decrement_invite(member.guild.id, inviter_id)
    
        # メッセージ送信
        if settings['channel_id']:
            channel = member.guild.get_channel(settings['channel_id'])
            if channel:
                inviter = member.guild.get_member(inviter_id) if inviter_id else None
                inviter_mention = inviter.mention if inviter else "不明な招待者"
    
                embed = discord.Embed(
                    title=f"{member.name}さんが{member.guild.name}を退出しました。",
                    description=f"{member.mention}は{inviter_mention}からの招待でした。現在{await self.get_invite_count(member.guild.id, inviter_id)}人招待しています。" if inviter_id else f"{member.mention}の招待者は不明です。",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)    

    @app_commands.command(name="invitetracker-set", description="Invite Trackerの設定を行います。")
    @app_commands.describe(is_enabled="機能を有効にするかどうか", channel="入出メッセージのチャンネルを選択してください。")
    async def set_invite_tracker(self, interaction: discord.Interaction, is_enabled: bool, channel: discord.TextChannel = None) -> None:
        await self.update_server_settings(interaction.guild.id, is_enabled, channel.id if channel else None)
        await interaction.response.send_message(f"Invite Tracker設定を更新しました。")

    @app_commands.command(name="invitetracker", description="自分の招待数を確認します。")
    async def invite_tracker(self, interaction: discord.Interaction) -> None:
        # Invite Trackerが有効か確認
        if not await self.check_if_enabled(interaction):
            return
        
        invite_count = await self.get_invite_count(interaction.guild.id, interaction.user.id)
        embed = discord.Embed(
            title=f"{interaction.user.name}の招待数",
            description=f"あなたは現在{invite_count}人を招待しています。",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="invitetracker-server", description="サーバーの招待数ランキングを表示します。")
    async def invite_tracker_server(self, interaction: discord.Interaction) -> None:
        # Invite Trackerが有効か確認
        if not await self.check_if_enabled(interaction):
            return

        # ランキングの取得
        rankings = await self.get_server_ranking(interaction.guild.id)
        if not rankings:
            await interaction.response.send_message("ランキングデータがありません。")
            return
        
        embeds = []
        for i in range(0, min(len(rankings), 10), 10):  # 10位までに制限
            embed = discord.Embed(
                title=f"{interaction.guild.name}の招待ランキング",
                description="\n".join([f"{idx + 1}. {self.bot.get_user(row[1]).mention if self.bot.get_user(row[1]) else '不明なユーザー'}: {row[2]}招待" for idx, row in enumerate(rankings[i:i + 10])]),
                color=discord.Color.purple()
            )
            embeds.append(embed)
        
        paginator = ui.Paginator(embeds=embeds, timeout=60)
        await paginator.send(interaction)

    # Helper Methods for DB Operations
    async def get_server_settings(self, guild_id: int) -> dict:
        result = await db.execute_query("SELECT is_enabled, channel_id FROM invite_tracker_settings WHERE guild_id = $1", (guild_id,))
        if result:
            return {'is_enabled': result[0]['is_enabled'], 'channel_id': result[0]['channel_id']}  # 辞書形式で返す
        return None

    async def update_server_settings(self, guild_id: int, is_enabled: bool, channel_id: int) -> None:
        await db.execute_query("""
        INSERT INTO invite_tracker_settings (guild_id, is_enabled, channel_id) VALUES ($1, $2, $3)
        ON CONFLICT (guild_id) DO UPDATE SET is_enabled = EXCLUDED.is_enabled, channel_id = EXCLUDED.channel_id
        """, (guild_id, is_enabled, channel_id))

    async def add_invite(self, guild_id: int, user_id: int, inviter_id: int) -> None:
        # 招待者が既にデータベースに存在するか確認
        existing_invite = await db.execute_query("""
        SELECT invites FROM invite_tracker WHERE guild_id = $1 AND inviter_id = $2
        """, (guild_id, inviter_id))
    
        if existing_invite:
            current_invites = existing_invite[0]['invites']
    
            # 招待数が0未満の場合、0に補正
            if current_invites < 0:
                current_invites = 0
    
            # 招待数をインクリメント
            await db.execute_query("""
            UPDATE invite_tracker SET invites = $1 WHERE guild_id = $2 AND inviter_id = $3
            """, (current_invites + 1, guild_id, inviter_id))
        else:
            # 新しいレコードを作成
            await db.execute_query("""
            INSERT INTO invite_tracker (guild_id, user_id, inviter_id, invites) 
            VALUES ($1, $2, $3, 1)
            """, (guild_id, user_id, inviter_id))



    async def get_inviter(self, guild_id: int, user_id: int) -> int:
        result = await db.execute_query("SELECT inviter_id FROM invite_tracker WHERE guild_id = $1 AND user_id = $2", (guild_id, user_id))
        return result[0]['inviter_id'] if result else None

    async def decrement_invite(self, guild_id: int, inviter_id: int) -> None:
        await db.execute_query("UPDATE invite_tracker SET invites = invites - 1 WHERE guild_id = $1 AND inviter_id = $2", (guild_id, inviter_id))

    async def get_invite_count(self, guild_id: int, user_id: int) -> int:
        result = await db.execute_query("SELECT invites FROM invite_tracker WHERE guild_id = $1 AND user_id = $2", (guild_id, user_id))
        return result[0]['invites'] if result else 0

    async def get_server_ranking(self, guild_id: int) -> list:
        return await db.execute_query("SELECT guild_id, user_id, invites FROM invite_tracker WHERE guild_id = $1 ORDER BY invites DESC", (guild_id,))

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(InviteTracker(bot))
