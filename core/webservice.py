# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet)

import asyncio
import secrets
import aiofiles
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from jinja2 import Template
from dotenv import load_dotenv

load_dotenv()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# FastAPI and authentication setup
security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # The lifespan context manager should handle lifecycle events
    yield

app = FastAPI(lifespan=lifespan)

# Static file serving
app.mount("/static", StaticFiles(directory="static"), name="static")

# Route definitions
@app.get("/admin/", response_class=HTMLResponse, dependencies=[Depends(authenticate)])
async def read_index(request: Request, bot):
    guilds_info = []
    for guild in bot.guilds:
        icon_url = guild.icon.url if guild.icon else "https://via.placeholder.com/100"
        owner = await bot.fetch_user(guild.owner_id)
        invite_url = await get_existing_invite(guild, bot)
        guilds_info.append(
            {
                "name": guild.name,
                "icon_url": icon_url,
                "owner_name": owner.name,
                "invite_url": invite_url,
            }
        )
    async with aiofiles.open("static/admin/index.html", mode="r", encoding="utf-8") as f:
        template = Template(await f.read())
    content = template.render(server_count=len(bot.guilds), guilds=guilds_info)
    return HTMLResponse(content=content)

# Other utility functions
async def get_existing_invite(guild, bot):
    for channel in guild.text_channels:
        try:
            invites = await channel.invites()
            for invite in invites:
                if invite.inviter.id == bot.user.id:
                    return invite.url
        except discord.Forbidden:
            continue
    return await create_invite(guild, bot)

async def create_invite(guild, bot):
    for channel in guild.text_channels:
        try:
            invite = await channel.create_invite(max_age=0, max_uses=0)
            return invite.url
        except discord.Forbidden:
            continue
    return "招待リンクを作成できませんでした。"
