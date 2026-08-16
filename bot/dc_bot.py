import os
import logging

import discord
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


intents = discord.Intents.default()
bot = DoorbellBot(command_prefix="!", intents=intents)


@bot.event
async def on_ready() -> None:
    logger.info("Bot ready, user: %s (id: %s)", bot.user, bot.user.id)


async def start_bot(token: str) -> None:
    await bot.start(token)


async def stop_bot() -> None:
    await bot.close()