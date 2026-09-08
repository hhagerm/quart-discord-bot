import os
import logging

from discord.ext import commands

logger = logging.getLogger(__name__)


class DoorbellBot(commands.Bot):
        
    async def setup_hook(self) -> None:
        await self.load_cogs()
        await self.tree.sync()
        
    async def load_cogs(self) -> None:
        try:
            for filename in os.listdir("bot/cogs"):
                if filename.endswith(".py"):
                    try:
                        await self.load_extension(f"bot.cogs.{filename[:-3]}")
                        logger.info("Loaded cog: %s", filename)
                    except Exception:
                        logger.exception("Failed to load cog: %s", filename)
        except Exception:
                        logger.exception("Failed to read cogs directory")

