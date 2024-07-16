import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp as youtube_dl
import asyncio
import os

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
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        print(f"Filename: {filename}")
        return cls(discord.FFmpegPCMAudio(filename, options='-vn'), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []

    @app_commands.command(name="play", description="YouTube音楽を再生します。")
    async def play(self, interaction: discord.Interaction, url: str, channel: discord.VoiceChannel):
        print("Received play command")
        if not interaction.user.voice:
            await interaction.response.send_message("音楽を再生するためにボイスチャンネルに接続してください。")
            return

        await interaction.response.defer()
        voice_client = interaction.guild.voice_client

        if not voice_client:
            try:
                print(f"Connecting to voice channel: {channel.name}")
                await channel.connect()
                print("Connected to voice channel")
            except Exception as e:
                print(f"Failed to connect to voice channel: {e}")
                await interaction.followup.send(f"ボイスチャンネルへの接続に失敗しました: {e}")
                return
            voice_client = interaction.guild.voice_client

        async with interaction.channel.typing():
            print(f"Loading player for URL: {url}")
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            self.queue.append(player)
            print(f'Queueing: {player.title}')
            await interaction.followup.send(f'再生中: {player.title}')

        if not voice_client.is_playing():
            await self.play_next(interaction)

    async def play_next(self, interaction):
        print("Playing next in queue")
        if self.queue:
            voice_client = interaction.guild.voice_client
            player = self.queue.pop(0)
            print(f"Now playing: {player.title}")
            try:
                voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(self.bot.loop.create_task, self.play_next(interaction)))
            except Exception as e:
                print(f"Error playing audio: {e}")
        else:
            print("Queue is empty, disconnecting")
            await interaction.guild.voice_client.disconnect()

    @app_commands.command(name="pause", description="再生中の音楽を一時停止します。")
    async def pause(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            print("Pausing current track")
            voice_client.pause()
            await interaction.response.send_message("音楽を一時停止しました。")
        else:
            await interaction.response.send_message("再生中の音楽がありません。")

    @app_commands.command(name="resume", description="一時停止した音楽を再生します。")
    async def resume(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_paused():
            print("Resuming paused track")
            voice_client.resume()
            await interaction.response.send_message("音楽を再生しました。")
        else:
            await interaction.response.send_message("一時停止した音楽がありません。")

    @app_commands.command(name="stop", description="再生中の音楽を停止します。")
    async def stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            print("Stopping current track")
            voice_client.stop()
            await interaction.response.send_message("音楽を停止しました。")
        else:
            await interaction.response.send_message("再生中の音楽がありません。")

    @app_commands.command(name="queue", description="現在の再生キューを表示します。")
    async def queue(self, interaction: discord.Interaction):
        if self.queue:
            queue_titles = "\n".join([player.title for player in self.queue])
            print(f"Queue: {queue_titles}")
            await interaction.response.send_message(f"再生キュー:\n{queue_titles}")
        else:
            await interaction.response.send_message("再生キューは空です。")

async def setup(bot):
    print("Setting up Music Cog")
    await bot.add_cog(Music(bot))
    print("Music Cog setup complete")
