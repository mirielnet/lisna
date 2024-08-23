# core - M.W
from os import listdir
from logging import getLogger

from discord.ext import commands


logger = getLogger(__name__)


class MWBot(commands.Bot):

    async def setup_hook(self) -> None:
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