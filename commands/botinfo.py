# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import platform

import cpuinfo
import discord
import psutil
from discord.ext import commands

from version import BOT_VERSION


class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(
        name="botinfo",
        description="BOTの実行環境を確認できます。 / You can check the bot's execution environment.",
    )
    async def botinfo(self, interaction: discord.Interaction):
        print("botinfo コマンドが実行されました。")
        await interaction.response.defer()

        # 各種情報の取得
        print("Pythonバージョンを取得しています...")
        python_version = platform.python_version()
        print(f"Pythonバージョン: {python_version}")

        print("Discord.pyバージョンを取得しています...")
        discord_version = discord.__version__
        print(f"Discord.pyバージョン: {discord_version}")

        print("OSバージョンを取得しています...")
        os_version = platform.version()
        print(f"OSバージョン: {os_version}")

        print("カーネルバージョンを取得しています...")
        kernel_version = platform.release()
        print(f"カーネルバージョン: {kernel_version}")

        print("プロセッサー情報を取得しています...")
        cpu_info = cpuinfo.get_cpu_info()["brand_raw"]
        print(f"CPU情報: {cpu_info}")

        print("CPU利用率を取得しています...")
        cpu_usage = psutil.cpu_percent(interval=1)
        print(f"CPU利用率: {cpu_usage}%")

        print("メモリ情報を取得しています...")
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        print(f"メモリ利用率: {memory_usage}%")

        # 埋め込みメッセージの作成
        embed = discord.Embed(title="システム情報グラフ", color=discord.Color.blue())
        embed.add_field(name="BOTのバージョン", value=BOT_VERSION, inline=True)
        embed.add_field(name="Pythonバージョン", value=python_version, inline=True)
        embed.add_field(name="Discord.pyバージョン", value=discord_version, inline=True)
        embed.add_field(name="OSバージョン", value=os_version, inline=True)
        embed.add_field(name="カーネルバージョン", value=kernel_version, inline=True)
        embed.add_field(name="CPU情報", value=cpu_info, inline=True)
        embed.add_field(name="CPU利用率", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="メモリ利用率", value=f"{memory_usage}%", inline=True)

        print("埋め込みメッセージを送信しています...")
        await interaction.followup.send(embed=embed)


async def setup(bot):
    print("BotInfo Cog をセットアップしています...")
    await bot.add_cog(BotInfo(bot))
    print("BotInfo Cog のセットアップが完了しました。")
