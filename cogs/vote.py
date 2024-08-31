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
        self.check_votes.start()
        self.bot.loop.create_task(self.init_db())
        self.bot.loop.create_task(self.register_existing_votes())

    async def init_db(self):
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

    async def register_existing_votes(self):
        await self.bot.wait_until_ready()
        votes = await db.execute_query("SELECT message_id, channel_id, options, creator_id FROM votes")

        if not votes:
            return

        for vote in votes:
            message_id, channel_id, options, creator_id = vote
            channel = self.bot.get_channel(channel_id)

            if channel is None:
                print(f"Channel with ID {channel_id} not found. Skipping message ID {message_id}.")
                continue

            try:
                message = await channel.fetch_message(message_id)
                view = VoteView(bot=self.bot, option_list=options, creator_id=creator_id)
                await message.edit(view=view)

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
                          options8: str = None, options9: str = None, options10: str = None):
        option_list = [options]
        for opt in [options2, options3, options4, options5, options6, options7, options8, options9, options10]:
            if opt:
                option_list.append(opt)

        jst = datetime.timezone(datetime.timedelta(hours=9))        
        
        try:
            deadline_dt = datetime.datetime.strptime(deadline, '%Y/%m/%d %H:%M')
            deadline_dt = deadline_dt.replace(tzinfo=jst)
        except ValueError:
            await interaction.response.send_message("締め切り日時の形式が正しくありません。", ephemeral=True)
            return
        
        now = datetime.datetime.now(jst)
        embed = discord.Embed(title=title, description="投票は1回限りです。選択してください。", color=discord.Color.blue())
        for idx, option in enumerate(option_list, start=1):
            embed.add_field(name=f"オプション{idx}", value=option, inline=False)
        
        embed.set_footer(text=f"投票締め切り時刻: {deadline_dt.strftime('%Y/%m/%d %H:%M')}")

        view = VoteView(bot=self.bot, option_list=option_list, creator_id=interaction.user.id)
        message = await interaction.channel.send(embed=embed, view=view)

        await db.execute_query("""
        INSERT INTO votes (message_id, channel_id, title, options, deadline, creator_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        """, (message.id, interaction.channel.id, title, option_list, deadline_dt.replace(tzinfo=None), interaction.user.id))

        await interaction.response.send_message("投票を作成しました。", ephemeral=True)

    @tasks.loop(minutes=1)
    async def check_votes(self):
        jst = datetime.timezone(datetime.timedelta(hours=9))
        now = datetime.datetime.now(jst).replace(tzinfo=None)  # タイムゾーンを削除して比較
        
        results = await db.execute_query("SELECT message_id, channel_id, options FROM votes WHERE deadline <= $1", (now,))
        
        if not results:
            return

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

    async def display_results(self, message, options):
        results = await db.execute_query("SELECT option_index, COUNT(*) FROM vote_results WHERE message_id = $1 GROUP BY option_index", (message.id,))
        if results is None:
            results = []

        total_votes = sum([row[1] for row in results])
        embed = message.embeds[0]
        embed.clear_fields()

        for idx, option in enumerate(options):
            count = next((row[1] for row in results if row[0] == idx), 0)
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            embed.add_field(name=option, value=f"{count}票 ({percentage:.2f}%)", inline=False)

        jst = datetime.timezone(datetime.timedelta(hours=9))
        now = datetime.datetime.now(jst)
        embed.set_footer(text=f"投票終了時刻: {now.strftime('%Y/%m/%d %H:%M')}")

        await message.edit(embed=embed, view=None)

    async def record_vote(self, message_id, option_index, user_id):
        await db.execute_query("""
        INSERT INTO vote_results (message_id, option_index, user_id)
        VALUES ($1, $2, $3)
        ON CONFLICT (message_id, user_id) DO UPDATE SET option_index = $2
        """, (message_id, option_index, user_id))

class VoteView(View):
    def __init__(self, bot, option_list, creator_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.option_list = option_list
        self.creator_id = creator_id

        for index, option in enumerate(option_list):
            button = Button(label=option, style=discord.ButtonStyle.primary, custom_id=f"vote_option_{index}")
            self.add_item(button)

    @discord.ui.button(label="終了", style=discord.ButtonStyle.danger, custom_id="vote_end")
    async def end_vote(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        if interaction.user.id != self.creator_id:
            await interaction.followup.send("投票の終了は作成者のみが可能です。", ephemeral=True)
            return
        
        results = await db.execute_query("SELECT option_index, COUNT(*) FROM vote_results WHERE message_id = $1 GROUP BY option_index", (interaction.message.id,))
        total_votes = sum(row[1] for row in results)
        embed = interaction.message.embeds[0]
        embed.clear_fields()

        for idx, option in enumerate(self.option_list):
            count = next((row[1] for row in results if row[0] == idx), 0)
            percentage = (count / total_votes * 100) if total_votes > 0 else 0
            embed.add_field(name=option, value=f"{count}票 ({percentage:.2f}%)", inline=False)

        jst = datetime.timezone(datetime.timedelta(hours=9))
        now = datetime.datetime.now(jst)
        embed.set_footer(text=f"投票終了時刻: {now.strftime('%Y/%m/%d %H:%M')}")

        await interaction.message.edit(embed=embed, view=None)
        await db.execute_query("DELETE FROM votes WHERE message_id = $1", (interaction.message.id,))
        await db.execute_query("DELETE FROM vote_results WHERE message_id = $1", (interaction.message.id,))

async def setup(bot):
    await bot.add_cog(Vote(bot))
