# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp as youtube_dl
import asyncio

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

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.current = None
        self.voice_client = None

    async def play_next(self, interaction):
        print("Playing next in queue")
        if self.queue:
            self.current = self.queue.pop(0)
            print(f"Now playing: {self.current.title}")

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
                self.voice_client.play(self.current, after=after_playing)
                await self.update_queue_message(interaction)
            except Exception as e:
                print(f"Error playing audio: {e}")
                await self.play_next(interaction)
        else:
            self.current = None
            await self.update_queue_message(interaction)
            print("Queue is empty, waiting for next command")

    async def update_queue_message(self, interaction):
        if self.current:
            embed = discord.Embed(title="再生キュー")
            embed.add_field(name="再生中", value=f"{self.current.title} / {interaction.user.mention}", inline=False)
            for i, player in enumerate(self.queue):
                embed.add_field(name=f"#{i + 1}", value=f"{player.title} / {interaction.user.mention}", inline=False)
            view = self.get_controls_view()
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.response.send_message(embed=embed, view=view)
        else:
            embed = discord.Embed(title="再生キュー", description="再生キューは空です。")
            view = self.get_controls_view()
            await interaction.followup.send(embed=embed, view=view)

    def get_controls_view(self):
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="再生/一時停止", style=discord.ButtonStyle.primary, custom_id="play_pause"))
        view.add_item(discord.ui.Button(label="停止", style=discord.ButtonStyle.danger, custom_id="stop"))
        view.add_item(discord.ui.Button(label="10秒スキップ", style=discord.ButtonStyle.secondary, custom_id="skip_10s"))
        return view

    @app_commands.command(name="play", description="YouTube音楽を再生します。")
    async def play(self, interaction: discord.Interaction, url: str, channel: discord.VoiceChannel):
        print("Received play command")
        if not interaction.user.voice:
            await interaction.response.send_message("音楽を再生するためにボイスチャンネルに接続してください。")
            return

        await interaction.response.defer()
        self.voice_client = interaction.guild.voice_client

        if not self.voice_client:
            try:
                print(f"Connecting to voice channel: {channel.name}")
                await channel.connect()
                print("Connected to voice channel")
            except Exception as e:
                print(f"Failed to connect to voice channel: {e}")
                await interaction.followup.send(f"ボイスチャンネルへの接続に失敗しました: {e}")
                return
            self.voice_client = interaction.guild.voice_client

        async with interaction.channel.typing():
            print(f"Loading player for URL: {url}")
            try:
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                self.queue.append(player)
                print(f'Queueing: {player.title}')
            except Exception as e:
                print(f"Error loading player: {e}")
                await interaction.followup.send(f"音楽の読み込みに失敗しました: {e}")
                return

        if not self.voice_client.is_playing():
            await self.play_next(interaction)
        else:
            await self.update_queue_message(interaction)

    @app_commands.command(name="queue", description="現在の再生キューを表示します。")
    async def queue(self, interaction: discord.Interaction):
        await self.update_queue_message(interaction)

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data['custom_id']
            if custom_id == "play_pause":
                voice_client = interaction.guild.voice_client
                if voice_client.is_playing():
                    voice_client.pause()
                    await interaction.response.send_message("音楽を一時停止しました。", ephemeral=True)
                else:
                    voice_client.resume()
                    await interaction.response.send_message("音楽を再生しました。", ephemeral=True)
            elif custom_id == "stop":
                voice_client = interaction.guild.voice_client
                voice_client.stop()
                self.queue = []  # キューをクリア
                self.current = None
                await self.update_queue_message(interaction)
            elif custom_id == "skip_10s":
                voice_client = interaction.guild.voice_client
                if voice_client.is_playing():
                    current_time = voice_client.source.stream.read(10)
                    await interaction.response.send_message(f"10秒スキップしました。新しい位置: {current_time}", ephemeral=True)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        print(f"Error in command {ctx.command}: {error}")

async def setup(bot):
    print("Setting up Music Cog")
    await bot.add_cog(Music(bot))
    print("Music Cog setup complete")
