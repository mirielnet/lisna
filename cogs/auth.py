# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import io
import random
import string

import discord
from captcha.image import ImageCaptcha
from discord import app_commands
from discord.ext import commands
from PIL import Image

from core.connect import db  # PostgreSQL接続をインポート


class AuthCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.image_captcha = ImageCaptcha()
        self.generated_captcha_image = None
        self.captcha_text = None

        # 初回起動時にテーブルを作成
        self.bot.loop.create_task(self.init_db())

    async def init_db(self):
        query = """
        CREATE TABLE IF NOT EXISTS auth_roles (
            guild_id BIGINT,
            role_id BIGINT,
            PRIMARY KEY (guild_id, role_id)
        )
        """
        await db.execute_query(query)

    @app_commands.command(name="auth", description="AUTHENTICATION PANEL")
    @app_commands.describe(role="認証完了時に付与するロール")
    async def auth(self, interaction: discord.Interaction, role: discord.Role):
        ch = interaction.channel
        embed = discord.Embed(
            title="認証をする",
            description="下の:white_check_mark:を押して認証を開始することができます。",
        )
        button = discord.ui.Button(
            emoji="✅", style=discord.ButtonStyle.primary, custom_id="image_au"
        )
        view = discord.ui.View()
        view.add_item(button)

        # ロール情報をDBに保存
        query = """
        INSERT INTO auth_roles (guild_id, role_id)
        VALUES ($1, $2)
        ON CONFLICT (guild_id, role_id) DO NOTHING
        """
        await db.execute_query(query, (interaction.guild.id, role.id))

        await interaction.response.send_message(":white_check_mark:", ephemeral=True)
        await ch.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        try:
            if interaction.data["component_type"] == 2:
                await self.on_button_click(interaction)
        except KeyError:
            pass

    async def on_button_click(self, interaction: discord.Interaction):
        custom_id = interaction.data["custom_id"]
        if custom_id == "image_au":
            captcha_text = "".join(
                random.choices(string.ascii_letters + string.digits, k=5)
            )
            original = self.image_captcha.generate(captcha_text)
            intensity = 20
            img = Image.open(original)
            small = img.resize(
                (round(img.width / intensity), round(img.height / intensity))
            )
            blur = small.resize((img.width, img.height), resample=Image.BILINEAR)
            embed = discord.Embed()
            button = discord.ui.Button(
                label="表示する", style=discord.ButtonStyle.primary, custom_id="picture"
            )
            view = discord.ui.View()
            view.add_item(button)
            with io.BytesIO() as image_binary:
                blur.save(image_binary, "PNG")
                image_binary.seek(0)
                file = discord.File(fp=image_binary, filename="captcha_img.png")
                embed.set_image(url="attachment://captcha_img.png")
                await interaction.response.send_message(
                    file=file, embed=embed, view=view, ephemeral=True
                )

            # 生成された画像を次の処理でも使用できるように保存
            self.generated_captcha_image = img
            self.captcha_text = captcha_text  # captcha_textを保存

        elif custom_id == "picture":
            embed = discord.Embed()

            button = discord.ui.Button(
                label="認証", style=discord.ButtonStyle.success, custom_id="phot_au"
            )
            view = discord.ui.View()
            view.add_item(button)

            if self.generated_captcha_image:
                with io.BytesIO() as image_binary:
                    self.generated_captcha_image.save(image_binary, "PNG")
                    image_binary.seek(0)
                    file = discord.File(image_binary, filename="captcha_img.png")
                    embed.set_image(url="attachment://captcha_img.png")
                    await interaction.response.edit_message(
                        attachments=[file], view=view, embed=embed
                    )
            else:
                await interaction.response.send_message(
                    "エラー: 画像が見つかりません。", ephemeral=True
                )

        elif custom_id == "phot_au":
            # Questionnaireクラスにcaptcha_textを渡す
            questionnaire = Questionnaire(captcha_text=self.captcha_text)
            await interaction.response.send_modal(questionnaire)


class Questionnaire(discord.ui.Modal):
    auth_answer = discord.ui.TextInput(
        label="認証コードを入力してください",
        style=discord.TextStyle.short,
        min_length=4,
        max_length=7,
    )

    def __init__(self, captcha_text):
        super().__init__(title="認証をする", timeout=None)
        self.captcha_text = captcha_text  # captcha_textを保存

    async def on_submit(self, interaction: discord.Interaction):
        answer = self.auth_answer.value
        print(
            f"DEBUG: captcha_text = '{self.captcha_text}', answer = '{answer}'"
        )  # ここでconsoleに出力
        if answer == self.captcha_text:
            embed = discord.Embed(description="**認証に成功しました！**", title=None)
            # ロールを付与
            query = "SELECT role_id FROM auth_roles WHERE guild_id = $1"
            role_id = await db.execute_query(query, (interaction.guild.id,))
            if role_id:
                role = interaction.guild.get_role(role_id[0][0])
                if role:
                    await interaction.user.add_roles(role)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                description="**認証に失敗しました...**\n**TIP:** 全角でないと成功にはなりません。",
                title=None,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(AuthCog(bot))
