# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Button, View
import datetime
from core.connect import db

class Vote(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.check_votes.start()  # 定期的に期限切れの投票をチェックするタスク
        self.init_db()  # DB初期化コード
        self.bot.loop.create_task(self.register_existing_votes())  # 再登録処理のタスクを開始

    # データベースの初期化
    async def init_db(self) -> None:
        await db.connect()
        await db.execute_query("""
        CREATE TABLE IF NOT EXISTS votes (
            message_id BIGINT PRIMARY KEY,
            channel_id BIGINT NOT NULL,
            title TEXT NOT NULL,
            options TEXT[] NOT NULL,
            deadline TIMESTAMP NOT NULL,
            creator_id BIGINT NOT NULL
        );
        """)

        await db.execute_query("""
        CREATE TABLE IF NOT EXISTS vote_results (
            message_id BIGINT NOT NULL,
            option_index INT NOT NULL,
            user_id BIGINT NOT NULL,
            PRIMARY KEY (message_id, user_id)
        );
        """)

    # 再登録処理
    async def register_existing_votes(self) -> None:
        await self.bot.wait_until_ready()
        votes = await db.execute_query("SELECT message_id, channel_id, options, creator_id FROM votes")

        for vote in votes:
            message_id, channel_id, options, creator_id = vote
            channel = self.bot.get_channel(channel_id)

            if channel is None:
                print(f"Channel with ID {channel_id} not found. Skipping message ID {message_id}.")
                continue

            try:
                message = await channel.fetch_message(message_id)
                view = VoteView(bot=self.bot, option_list=options, creator_id=creator_id)
                await message.edit(view=view)  # ビューを再登録

            except discord.NotFound:
                print(f"Message with ID {message_id} not found. Deleting from database.")
                await db.execute_query("DELETE FROM votes WHERE message_id = $1", (message_id,))
                await db.execute_query("DELETE FROM vote_results WHERE message_id = $1", (message_id,))

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
                          options8: str = None, options9: str = None, options10: str = None) -> None:
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
        embed = discord.Embed(title=title, description="投票は1回限りです。選択してください。", color=discord.Color.blue())
        for idx, option in enumerate(option_list, start=1):
            embed.add_field(name=f"オプション{idx}", value=option, inline=False)
        
        # 締め切り時刻をフッターに追加
        embed.set_footer(text=f"投票締め切り時刻: {deadline_dt.strftime('%Y/%m/%d %H:%M')}")

        # ボタンを設定するビューを作成
        view = VoteView(bot=self.bot, option_list=option_list, creator_id=interaction.user.id)

        # メッセージ送信
        message = await interaction.channel.send(embed=embed, view=view)
        
        # データベースに保存
        await db.execute_query("""
        INSERT INTO votes (message_id, channel_id, title, options, deadline, creator_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        """, (message.id, interaction.channel.id, title, option_list, deadline_dt, interaction.user.id))

        await interaction.response.send_message("投票を作成しました。", ephemeral=True)

    @tasks.loop(minutes=1)
    async def check_votes(self) -> None:
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
        results = await db.execute_query("SELECT message_id, channel_id, options FROM votes WHERE deadline <= $1", (now,))
        
        for row in results:
            message_id, channel_id, options = row
            channel = self.bot.get_channel(channel_id)
            
            if channel is None:
                print(f"Channel with ID {channel_id} not found. Skipping message ID {message_id}.")
                continue
            
            try:
                message = await channel.fetch_message(message_id)
                view = message.components[0] if message.components else None
                if view:
                    await self.display_results(message, options)

                await db.execute_query("DELETE FROM votes WHERE message_id = $1", (message_id,))
                await db.execute_query("DELETE FROM vote_results WHERE message_id = $1", (message_id,))
            
            except discord.NotFound:
                print(f"Message with ID {message_id} not found in channel {channel_id}. Deleting from database.")
                await db.execute_query("DELETE FROM votes WHERE message_id = $1", (message_id,))
                await db.execute_query("DELETE FROM vote_results WHERE message_id = $1", (message_id,))

    async def display_results(self, message: discord.Message, options: list) -> None:
        results = await db.execute_query("SELECT option_index, COUNT(*) FROM vote_results WHERE message_id = $1 GROUP BY option_index", (message.id,))
        total_votes = sum([row[1] for row in results])
        embed = message.embeds[0]
        embed.clear_fields()

        # 結果をフィールドに追加
        for idx, option in enumerate(options):
            count = next((row[1] for row in results if row[0] == idx), 0)
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            embed.add_field(name=option, value=f"{count}票 ({percentage:.2f}%)", inline=False)

        # 投票終了時刻を追加
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
        embed.set_footer(text=f"投票終了時刻: {now.strftime('%Y/%m/%d %H:%M')}")

        # メッセージを更新
        await message.edit(embed=embed, view=None)

    # 永続化用DB操作
    async def record_vote(self, message_id: int, option_index: int, user_id: int) -> None:
        await db.execute_query("""
        INSERT INTO vote_results (message_id, option_index, user_id)
        VALUES ($1, $2, $3)
        ON CONFLICT DO NOTHING
        """, (message_id, option_index, user_id))

    async def get_options(self, message_id: int) -> list:
        options = await db.execute_query("SELECT options FROM votes WHERE message_id = $1", (message_id,))
        return options[0][0] if options else []


class VoteView(View):
    def __init__(self, bot: commands.Bot, option_list: list, creator_id: int) -> None:
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
    def __init__(self, label: str, option_index: int) -> None:
        super().__init__(label=label)
        self.option_index = option_index

    async def callback(self, interaction: discord.Interaction) -> None:
        vote_cog = interaction.client.get_cog("Vote")
        existing_vote = await db.execute_query("""
        SELECT * FROM vote_results WHERE message_id = $1 AND user_id = $2
        """, (interaction.message.id, interaction.user.id))

        if existing_vote:
            await interaction.response.send_message("すでに投票しています。", ephemeral=True)
        else:
            await vote_cog.record_vote(interaction.message.id, self.option_index, interaction.user.id)
            await interaction.response.send_message(f"{self.label}に投票しました。", ephemeral=True)


class EndVoteButton(Button):
    def __init__(self, bot: commands.Bot, creator_id: int) -> None:
        super().__init__(label="投票終了", style=discord.ButtonStyle.danger)
        self.bot = bot
        self.creator_id = creator_id

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.creator_id and not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("投票を終了する権限がありません。", ephemeral=True)
            return

        vote_cog = interaction.client.get_cog("Vote")
        await vote_cog.display_results(interaction.message, await vote_cog.get_options(interaction.message.id))
        await interaction.response.send_message("投票を終了しました。", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Vote(bot))
