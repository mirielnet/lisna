# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

class HitAndBlowServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}

    @app_commands.command(name="hitandblow-server", description="サーバー内でヒット＆ブローをプレイします。")
    @app_commands.describe(digits="桁数（初期値: 4桁）")
    async def hitandblow_server(self, interaction: discord.Interaction, digits: int = 4):
        if interaction.guild.id in self.sessions:
            await interaction.response.send_message("既にゲームが進行中です。", ephemeral=True)
            return

        if digits < 3 or digits > 10:
            await interaction.response.send_message("桁数は3〜10の間で設定してください。", ephemeral=True)
            return

        # コンピュータがランダムな指定桁数の数字を選択
        answer = ''.join(random.sample("0123456789", digits))
        self.sessions[interaction.guild.id] = {
            "answer": answer,
            "attempts": {}
        }

        embed = discord.Embed(
            title="ヒット＆ブロー",
            description=f"コンピュータが{digits}桁の数字を選びました。数字を予測して、チャンネル内で答えを入力してください。",
            color=discord.Color.blue()
        )
        embed.add_field(name="ルール", value=f"桁と数字が同じならHit。数字は同じで桁が違うならBlow。当ててください。桁数: {digits}桁。")

        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        session = self.sessions.get(message.guild.id)
        if not session:
            return

        if len(message.content) != len(session["answer"]) or not message.content.isdigit() or len(set(message.content)) != len(session["answer"]):
            await message.reply(f"{len(session['answer'])}桁の重複しない数字を入力してください。")
            return

        guess = message.content
        hits, blows = 0, 0

        for i in range(len(session["answer"])):
            if guess[i] == session["answer"][i]:
                hits += 1
            elif guess[i] in session["answer"]:
                blows += 1

        if hits == len(session["answer"]):
            await message.reply(f"正解です！数字 {session['answer']} を当てました。ゲーム終了です！")
            del self.sessions[message.guild.id]
        else:
            session["attempts"][message.author.id] = session["attempts"].get(message.author.id, 0) + 1
            await message.reply(f"{hits} Hit, {blows} Blow")

async def setup(bot):
    await bot.add_cog(HitAndBlowServer(bot))
