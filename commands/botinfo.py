import discord
from discord.ext import commands
import platform
import psutil
from version import BOT_VERSION

class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="botinfo", description="BOTの実行環境を確認できます。 / You can check the bot's execution environment.")
    async def botinfo(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # 各種情報の取得
        python_version = platform.python_version()
        discord_version = discord.__version__
        os_version = platform.version()
        kernel_version = platform.release()
        cpu_info = f"CPU: {platform.processor()}"
        memory = psutil.virtual_memory()
        time_zone = platform.uname().nodename

        # 埋め込みメッセージの作成
        embed = discord.Embed(title="システム情報グラフ", color=discord.Color.blue())
        embed.add_field(name="BOTのバージョン", value=BOT_VERSION, inline=True)
        embed.add_field(name="Pythonバージョン", value=python_version, inline=True)
        embed.add_field(name="Discord.pyバージョン", value=discord_version, inline=True)
        embed.add_field(name="OSバージョン", value=os_version, inline=True)
        embed.add_field(name="カーネルバージョン", value=kernel_version, inline=True)
        embed.add_field(name="CPU情報", value=cpu_info, inline=True)
        embed.add_field(name="タイムゾーン", value=time_zone, inline=True)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BotInfo(bot))
