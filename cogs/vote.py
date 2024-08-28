# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Button, View
import datetime
from core.connect import db

class Vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_votes.start()  # 定期的に期限切れの投票をチェックするタスク
        self.init_db()  # DB初期化コード

    # データベースの初期化
    def init_db(self):
        db.execute_query("""
        CREATE TABLE IF NOT EXISTS votes (
            message_id BIGINT PRIMARY KEY,
            channel_id BIGINT NOT NULL,
            title TEXT NOT NULL,
            options TEXT[] NOT NULL,
            deadline TIMESTAMP NOT NULL,
            creator_id BIGINT NOT NULL
        );
        """)

        db.execute_query("""
        CREATE TABLE IF NOT EXISTS vote_results (
            message_id BIGINT NOT NULL,
            option_index INT NOT NULL,
            user_id BIGINT NOT NULL,
            PRIMARY KEY (message_id, user_id)
        );
        """)

    @app_commands.command(name="vote", description="新しい投票を作成します")
    @app_commands.describe(
        title="投票のタイトル",
        options="必須のオプション",
        options2="オプション2",
        options3="オプション3",
        options4="オプション4",
        options5="オプション5",
        options6="オプション6",
        options7="オプション7",
        options8="オプション8",
        options9="オプション9",
        options10="オプション10",
        deadline="投票の締め切り（例: 2024/08/28 21:15）"
    )
    async def create_vote(self, interaction: discord.Interaction, title: str, options: str, deadline: str, 
                          options2: str = None, options3: str = None, options4: str = None, 
                          options5: str = None, options6: str = None, options7: str = None, 
                          options8: str = None, options9: str = None, options10: str = None):
        # 選択肢のリスト作成
        option_list = [options]
        for opt in [options2, options3, options4, options5, options6, options7, options8, options9, options10]:
            if opt:
                option_list.append(opt)

        # 締め切りのパース
        try:
            deadline_dt = datetime.datetime.strptime(deadline, '%Y/%m/%d %H:%M')
            deadline_dt = deadline_dt.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=9)))  # JSTに設定
        except ValueError:
            await interaction.response.send_message("締め切り日時の形式が正しくありません。", ephemeral=True)
            return

        # Embedメッセージ作成
        embed = discord.Embed(title=title, description="投票してください！", color=discord.Color.blue())
        for idx, option in enumerate(option_list, start=1):
            embed.add_field(name=f"オプション{idx}", value=option, inline=False)
        
        # ボタンを設定するビューを作成
        view = VoteView(bot=self.bot, option_list=option_list, creator_id=interaction.user.id)

        # メッセージ送信
        message = await interaction.channel.send(embed=embed, view=view)
        
        # データベースに保存
        db.execute_query("""
        INSERT INTO votes (message_id, channel_id, title, options, deadline, creator_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (message.id, interaction.channel.id, title, option_list, deadline_dt, interaction.user.id))

        await interaction.response.send_message("投票を作成しました。", ephemeral=True)

    @tasks.loop(minutes=1)
    async def check_votes(self):
        # 期限切れの投票をチェック
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))  # JSTで現在時刻取得
        results = db.execute_query("SELECT message_id, options FROM votes WHERE deadline <= %s", (now,))
        
        for row in results:
            message_id, options = row
            channel_id = db.execute_query("SELECT channel_id FROM votes WHERE message_id = %s", (message_id,))[0][0]
            channel = self.bot.get_channel(channel_id)
            message = await channel.fetch_message(message_id)
            view = message.components[0] if message.components else None
            if view:
                # 結果を表示
                await self.display_results(message, options)

            # データベースから削除
            db.execute_query("DELETE FROM votes WHERE message_id = %s", (message_id,))
            db.execute_query("DELETE FROM vote_results WHERE message_id = %s", (message_id,))

    async def display_results(self, message, options):
        results = db.execute_query("SELECT option_index, COUNT(*) FROM vote_results WHERE message_id = %s GROUP BY option_index", (message.id,))
        total_votes = sum([row[1] for row in results])
        embed = message.embeds[0]
        embed.clear_fields()

        # 結果をフィールドに追加
        for idx, option in enumerate(options):
            count = next((row[1] for row in results if row[0] == idx), 0)
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            embed.add_field(name=option, value=f"{count}票 ({percentage:.2f}%)", inline=False)

        # メッセージを更新
        await message.edit(embed=embed, view=None)

    # 永続化用DB操作
    def record_vote(self, message_id, option_index, user_id):
        db.execute_query("""
        INSERT INTO vote_results (message_id, option_index, user_id)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING
        """, (message_id, option_index, user_id))


class VoteView(View):
    def __init__(self, bot, option_list, creator_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.option_list = option_list
        self.creator_id = creator_id

        # 投票用ボタン追加
        for idx, option in enumerate(option_list):
            self.add_item(VoteButton(label=option, option_index=idx))

        # 投票終了ボタンを追加
        self.add_item(EndVoteButton(bot=self.bot, creator_id=creator_id))


class VoteButton(Button):
    def __init__(self, label, option_index):
        super().__init__(label=label)
        self.option_index = option_index

    async def callback(self, interaction: discord.Interaction):
        vote_cog = interaction.client.get_cog("Vote")
        vote_cog.record_vote(interaction.message.id, self.option_index, interaction.user.id)
        await interaction.response.send_message(f"{self.label}に投票しました。", ephemeral=True)


class EndVoteButton(Button):
    def __init__(self, bot, creator_id):
        super().__init__(label="投票終了", style=discord.ButtonStyle.danger)
        self.bot = bot
        self.creator_id = creator_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.creator_id and not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("投票を終了する権限がありません。", ephemeral=True)
            return

        vote_cog = interaction.client.get_cog("Vote")
        await vote_cog.display_results(interaction.message, vote_cog.get_options(interaction.message.id))
        await interaction.response.send_message("投票を終了しました。", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Vote(bot))
