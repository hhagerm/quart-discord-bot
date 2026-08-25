import logging
from typing import List, Tuple
from datetime import datetime

import discord
from discord.ext import commands

from core.storage import delete_image

logger = logging.getLogger(__name__)


class NotificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_discord_notification(
        self, file_path: str, subscriptions: List[Tuple[int, int]]
    ) -> None:
        try:
            if not subscriptions:
                logger.warning("No active subscriptions to notify")
                return

            for guild_id, channel_id in subscriptions:
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    logger.error(
                        "Could not find channel %d in guild %d",
                        channel_id,
                        guild_id,
                    )
                    continue

                try:
                    file = discord.File(file_path, filename="visitor.jpg")
                    embed = discord.Embed(
                        title="🔔 Doorbell Alert",
                        description=datetime.now().strftime("%d/%m/%y %H:%M"),
                        color=discord.Color.blue(),
                    )
                    embed.set_image(url="attachment://visitor.jpg")
                    await channel.send(file=file, embed=embed)
                except Exception:
                    logger.exception(
                        "Failed to send Discord notification to channel %d in guild %d",
                        channel_id,
                        guild_id,
                    )
        finally:
            await delete_image(file_path)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(NotificationCog(bot))