# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

class HitAndBlow(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}

    @app_commands.command(name="hitandblow", description="ヒット＆ブローをプレイします。")
    async def hitandblow(self, interaction: discord.Interaction):
        if interaction.user.id in self.sessions:
            await interaction.response.send_message("既にゲームが進行中です。", ephemeral=True)
            return

        # コンピュータがランダムな4桁の数字を選択
        answer = ''.join(random.sample("0123456789", 4))
        self.sessions[interaction.user.id] = {
            "answer": answer,
            "attempts": 0
        }

        embed = discord.Embed(
            title="ヒット＆ブロー",
            description="コンピュータが4桁の数字を選びました。数字を予測して、このメッセージにリプライしてください。",
            color=discord.Color.blue()
        )
        embed.add_field(name="ルール", value="桁と数字が同じならHit。数字は同じで桁が違うならBlow。10回以内に当ててください。")

        try:
            # メッセージ送信
            message = await interaction.response.send_message(embed=embed)
            message = await interaction.original_response()
        except discord.Forbidden:
            await interaction.followup.send("ボットにメッセージを送信する権限がありません。", ephemeral=True)
            del self.sessions[interaction.user.id]
            return
        except Exception as e:
            await interaction.followup.send(f"メッセージ送信に失敗しました: {e}", ephemeral=True)
            del self.sessions[interaction.user.id]
            return

        # セッションにメッセージIDを保存
        self.sessions[interaction.user.id]["message_id"] = message.id

        # リプライを待つ処理を開始
        await self.start_guessing(interaction.user.id, interaction.channel)

    async def start_guessing(self, user_id, channel):
        def check(m):
            session = self.sessions.get(user_id)
            return m.author.id == user_id and m.reference and m.reference.message_id == session["message_id"]

        while user_id in self.sessions:
            try:
                message = await self.bot.wait_for('message', check=check, timeout=300)  # 5分間のタイムアウト
                guess = message.content

                if len(guess) != 4 or not guess.isdigit() or len(set(guess)) != 4:
                    await message.reply("4桁の重複しない数字を入力してください。")
                    continue

                session = self.sessions[user_id]
                session["attempts"] += 1
                hits, blows = 0, 0

                for i in range(4):
                    if guess[i] == session["answer"][i]:
                        hits += 1
                    elif guess[i] in session["answer"]:
                        blows += 1

                if hits == 4:
                    await message.reply(f"正解です！数字 {session['answer']} を当てました。ゲーム終了です！")
                    del self.sessions[user_id]
                elif session["attempts"] >= 10:
                    await message.reply(f"10回の試行が終わりました。残念ながら正解できませんでした。正解は {session['answer']} でした。")
                    del self.sessions[user_id]
                else:
                    await message.reply(f"{hits} Hit, {blows} Blow | 試行回数: {session['attempts']}/10")

            except asyncio.TimeoutError:
                await channel.send(f"時間切れです。ゲームは終了しました。正解は {self.sessions[user_id]['answer']} でした。")
                del self.sessions[user_id]

async def setup(bot):
    await bot.add_cog(HitAndBlow(bot))
