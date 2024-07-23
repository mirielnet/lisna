# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp as youtube_dl
import asyncio
import time

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -bufsize 64k -analyzeduration 2147483647 -probesize 2147483647'
}

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.start_time = time.time()
        self.seek_time = 0
        self.paused = False
        self.pause_start_time = 0

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        print(f"Fetching URL: {url}")
        loop = loop or asyncio.get_event_loop()
        ytdl = youtube_dl.YoutubeDL({
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        })
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        print(f"Filename: {filename}")
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)

    def get_current_time(self):
        if self.paused:
            return self.seek_time
        return time.time() - self.start_time + self.seek_time

    def set_current_time(self, current_time):
        self.seek_time = current_time
        self.start_time = time.time()

    def pause(self):
        if not self.paused:
            self.paused = True
            self.pause_start_time = time.time()

    def resume(self):
        if self.paused:
            self.paused = False
            self.seek_time += time.time() - self.pause_start_time

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # サーバーIDごとにキューを管理
        self.current = {}  # サーバーIDごとに現在の再生曲を管理
        self.voice_clients = {}  # サーバーIDごとにボイスクライアントを管理
        self.requesters = {}  # サーバーIDごとにリクエスターを管理
        self.current_messages = {}  # サーバーIDごとにメッセージを管理
        self.progress_tasks = {}  # サーバーIDごとに進行タスクを管理

    async def play_next(self, interaction):
        guild_id = interaction.guild.id
        print(f"Playing next in queue for guild: {guild_id}")
        if self.queues[guild_id]:
            self.current[guild_id], self.requesters[guild_id] = self.queues[guild_id].pop(0)
            self.current[guild_id].set_current_time(0)  # Reset the progress to 0 for new song
            print(f"Now playing: {self.current[guild_id].title}")

            def after_playing(error):
                if error:
                    print(f"Error in after_playing: {error}")
                coro = self.play_next(interaction)
                fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                try:
                    fut.result()
                except Exception as e:
                    print(f"Error in after_playing coroutine: {e}")

            try:
                self.voice_clients[guild_id].play(self.current[guild_id], after=after_playing)
                await self.update_now_playing(interaction)
            except Exception as e:
                print(f"Error playing audio: {e}")
                await self.play_next(interaction)
        else:
            self.current[guild_id] = None
            await self.update_queue_message(interaction)
            print("Queue is empty, waiting for next command")

    async def update_now_playing(self, interaction):
        guild_id = interaction.guild.id
        if self.current[guild_id]:
            embed = discord.Embed(title="再生中")
            embed.add_field(name=self.current[guild_id].title, value=f"{self.requesters[guild_id].mention}", inline=False)
            embed.add_field(name="再生時間", value=self.format_progress_bar(0, self.current[guild_id].duration), inline=False)
            view = self.get_controls_view()
            message = await interaction.followup.send(embed=embed, view=view)
            self.current_messages[guild_id] = message
            if guild_id in self.progress_tasks:
                self.progress_tasks[guild_id].cancel()
            self.progress_tasks[guild_id] = self.bot.loop.create_task(self.update_progress_bar(guild_id))

    async def update_progress_bar(self, guild_id):
        while self.voice_clients[guild_id] and (self.voice_clients[guild_id].is_playing() or self.voice_clients[guild_id].is_paused()) and self.current_messages[guild_id]:
            await asyncio.sleep(1)
            if self.current[guild_id]:
                current_time = self.current[guild_id].get_current_time()
                embed = discord.Embed(title="再生中")
                embed.add_field(name=self.current[guild_id].title, value=f"{self.requesters[guild_id].mention}", inline=False)
                embed.add_field(name="再生時間", value=self.format_progress_bar(current_time, self.current[guild_id].duration), inline=False)
                view = self.get_controls_view()
                await self.current_messages[guild_id].edit(embed=embed, view=view)

    async def update_queue_message(self, interaction):
        guild_id = interaction.guild.id
        embed = discord.Embed(title="再生キュー")
        if self.current[guild_id]:
            embed.add_field(name="再生中", value=f"{self.current[guild_id].title} / {self.requesters[guild_id].mention}", inline=False)
        if self.queues[guild_id]:
            for i, (player, requester) in enumerate(self.queues[guild_id]):
                embed.add_field(name=f"#{i + 1}", value=f"{player.title} / {requester.mention}", inline=False)
        else:
            embed.description = "再生キューは空です。"
        await interaction.followup.send(embed=embed)

    def get_controls_view(self):
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="⏯️ 再生/一時停止", style=discord.ButtonStyle.primary, custom_id="play_pause"))
        view.add_item(discord.ui.Button(label="⏹️ 停止", style=discord.ButtonStyle.danger, custom_id="stop"))
        view.add_item(discord.ui.Button(label="🔊 切断", style=discord.ButtonStyle.danger, custom_id="disconnect"))
        return view

    def format_progress_bar(self, current, total, length=20):
        filled_length = int(length * current // total)
        bar = '─' * filled_length + '●' + '─' * (length - filled_length)
        return f"{self.format_time(current)} {bar} {self.format_time(total)}"

    def format_time(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes):02}:{int(seconds):02}"

    @app_commands.command(name="play", description="YouTubeまたはSoundCloudの音楽を再生します。")
    async def play(self, interaction: discord.Interaction, url: str, channel: discord.VoiceChannel):
        guild_id = interaction.guild.id
        print(f"Received play command for guild: {guild_id}")
        if not interaction.user.voice:
            await interaction.response.send_message("音楽を再生するためにボイスチャンネルに接続してください。")
            return

        await interaction.response.defer()
        if guild_id not in self.voice_clients or self.voice_clients[guild_id] is None:
            self.voice_clients[guild_id] = interaction.guild.voice_client

        if not self.voice_clients[guild_id]:
            try:
                print(f"Connecting to voice channel: {channel.name}")
                await channel.connect()
                print("Connected to voice channel")
            except Exception as e:
                print(f"Failed to connect to voice channel: {e}")
                await interaction.followup.send(f"ボイスチャンネルへの接続に失敗しました: {e}")
                return
            self.voice_clients[guild_id] = interaction.guild.voice_client

        async with interaction.channel.typing():
            print(f"Loading player for URL: {url}")
            try:
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                if guild_id not in self.queues:
                    self.queues[guild_id] = []
                self.queues[guild_id].append((player, interaction.user))
                print(f'Queueing: {player.title}')
                await self.update_queue_message(interaction)  # Update queue message after adding new song
            except Exception as e:
                print(f"Error loading player: {e}")
                await interaction.followup.send(f"音楽の読み込みに失敗しました: {e}")
                return

        if not self.voice_clients[guild_id].is_playing():
            await self.play_next(interaction)

    @app_commands.command(name="queue", description="現在の再生キューを表示します。")
    async def queue(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.update_queue_message(interaction)

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data['custom_id']
            guild_id = interaction.guild.id
            voice_client = self.voice_clients.get(guild_id)
            if custom_id == "play_pause":
                if voice_client.is_playing():
                    voice_client.pause()
                    self.current[guild_id].pause()
                    await interaction.response.send_message("音楽を一時停止しました。", ephemeral=True)
                else:
                    voice_client.resume()
                    self.current[guild_id].resume()
                    await interaction.response.send_message("音楽を再生しました。", ephemeral=True)
                    if guild_id in self.progress_tasks:
                        self.progress_tasks[guild_id].cancel()
                    self.progress_tasks[guild_id] = self.bot.loop.create_task(self.update_progress_bar(guild_id))
            elif custom_id == "stop":
                voice_client.stop()
                self.queues[guild_id] = []  # キューをクリア
                self.current[guild_id] = None
                await self.update_queue_message(interaction)
            elif custom_id == "disconnect":
                await interaction.response.send_message("ボイスチャンネルから切断します。", ephemeral=True)
                await voice_client.disconnect()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        print(f"Error in command {ctx.command}: {error}")

async def setup(bot):
    print("Setting up Music Cog")
    await bot.add_cog(Music(bot))
    print("Music Cog setup complete")
