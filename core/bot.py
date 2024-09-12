# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Author: Miriel (@mirielnet) and tuna2134

import asyncio
from logging import getLogger
from os import listdir

from discord.ext import commands

from core.connect import db  # Import your database connection class

logger = getLogger(__name__)


class MWBot(commands.Bot):

    async def setup_hook(self) -> None:
        # Ensure the database connection is established
        await db.connect()
        logger.info("Database connection established")

        # Load extensions
        await self.load_extension("jishaku")

        for filename in listdir("./cogs"):
            if filename != "__init__.py" and filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    logger.info(f"Loaded cog: {filename}")
                except Exception as e:
                    logger.error(f"Failed to load cog {filename}: {e}")

        await self.tree.sync()
        logger.info("Successfully synced app commands")
