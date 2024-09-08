# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import discord
from discord.ext import commands
from discord import app_commands
import whois
from datetime import datetime

class WhoisLookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="whois", description="ドメインの WHOIS 情報を取得します。")
    @app_commands.describe(domain="取得したいドメイン名を入力してください。")
    async def whois_lookup(self, interaction: discord.Interaction, domain: str):
        await interaction.response.defer()  # 処理中に応答を保留
        
        try:
            # WHOIS情報を取得
            domain_info = whois.whois(domain)
            
            # 日付のフォーマット変換
            def format_date(date):
                return date.strftime('%Y-%m-%d %H:%M:%S') if isinstance(date, datetime) else "不明"
            
            # Embedメッセージの作成
            embed = discord.Embed(
                title=f"{domain} の WHOIS 情報",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="ドメイン名", value=domain_info.domain_name or "不明", inline=False)
            embed.add_field(name="レジストラー", value=domain_info.registrar or "不明", inline=False)
            embed.add_field(name="取得日時", value=format_date(domain_info.creation_date), inline=False)
            embed.add_field(name="更新日時", value=format_date(domain_info.updated_date), inline=False)
            embed.add_field(name="失効日時", value=format_date(domain_info.expiration_date), inline=False)
            embed.add_field(name="登録者名", value=domain_info.name or "不明", inline=False)
            embed.add_field(name="管理者名", value=domain_info.admin or "不明", inline=False)
            
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            embed = discord.Embed(
                title="エラー",
                description="ドメイン情報の取得に失敗しました。",
                color=discord.Color.red()
            )
            embed.add_field(name="詳細", value=str(e))
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(WhoisLookup(bot))
