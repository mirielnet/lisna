import discord
import random
import string
from PIL import Image
import io
from captcha.image import ImageCaptcha

class AuthCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ImageCaptcha = ImageCaptcha()

    @commands.Cog.listener()
    async def on_ready(self):
        print("AuthCog is ready")

    @commands.command(name="auth", description="AUTHENTICATION PANEL")
    async def panel_au(self, ctx: commands.Context):
        ch = ctx.channel
        embed = discord.Embed(title="認証をする", description="下の:white_check_mark:を押して認証を開始することができます。")
        button = discord.ui.Button(emoji="✅", style=discord.ButtonStyle.primary, custom_id="image_au")
        view = discord.ui.View()
        view.add_item(button)
        await ctx.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_interaction(self, inter: discord.Interaction):
        try:
            if inter.data['component_type'] == 2:
                await self.on_button_click(inter)
        except KeyError:
            pass

    async def on_button_click(self, interaction: discord.Interaction):
        custom_id = interaction.data["custom_id"]
        if custom_id == "image_au":
            text = string.ascii_letters + string.digits
            captcha_text = random.choices(text, k=5)
            captcha_text = "".join(captcha_text)
            original = self.ImageCaptcha.generate(captcha_text)
            intensity = 20
            img = Image.open(original)
            small = img.resize(
                (round(img.width / intensity), round(img.height / intensity))
            )
            blur = small.resize(
                (img.width, img.height),
                resample=Image.BILINEAR
            )
            embed = discord.Embed()
            button = discord.ui.Button(label="表示する", style=discord.ButtonStyle.primary, custom_id="picture")
            view = discord.ui.View()
            view.add_item(button)
            with io.BytesIO() as image_binary:
                blur.save(image_binary, 'PNG')
                image_binary.seek(0)
                file = discord.File(fp=image_binary, filename="captcha_img.png")
                embed.set_image(url="attachment://captcha_img.png")
                await interaction.response.send_message(file=file, embed=embed, view=view, ephemeral=True)
        elif custom_id == "picture":
            embed = discord.Embed()
            button = discord.ui.Button(label="認証", style=discord.ButtonStyle.success, custom_id="phot_au")
            view = discord.ui.View()
            view.add_item(button)

            with io.BytesIO() as image_binary:
                img.save(image_binary, 'PNG')
                image_binary.seek(0)
                file = discord.File(image_binary, filename="captcha_img.png")
                embed.set_image(url="attachment://captcha_img.png")
                await interaction.response.edit_message(attachments=[file], view=view, embed=embed)
        elif custom_id == "phot_au":
            class Questionnaire(discord.ui.Modal):
                auth_answer = discord.ui.TextInput(label=f'認証コードを入力してください', style=discord.TextStyle.short, min_length=4, max_length=7)

                def __init__(self):
                    super().__init__(title='認証をする', timeout=None)

                async def on_submit(self, interaction: discord.Interaction):
                    answer = self.auth_answer.value
                    if answer == captcha_text:
                        embed = discord.Embed(description="**認証に成功しました！**", title=None)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        embed = discord.Embed(description="**認証に失敗しました...**\n**TIP:** 全角でないと成功にはなりません。", title=None)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.response.send_modal(Questionnaire())

async def setup(bot):
    await bot.add_cog(AuthCog(bot))
