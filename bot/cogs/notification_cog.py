import logging
from datetime import datetime

import discord
from discord.ext import commands

from core import exceptions

logger = logging.getLogger(__name__)


class NotificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_discord_notification(
        self, file_path: str, guild_id: int, channel_id: int
    ) -> None:
        channel = self.bot.get_channel(channel_id)
        if not channel:
            logger.error(
                "Could not find channel %d in guild %d",
                channel_id,
                guild_id,
            )
            raise exceptions.ChannelNotFoundError(
                f"Channel {channel_id} in guild {guild_id} not found"
            )

        file = discord.File(file_path, filename="visitor.jpg")
        embed = discord.Embed(
            title="🔔 Doorbell Alert",
            description=datetime.now().strftime("%d/%m/%y %H:%M"),
            color=discord.Color.blue(),
        )
        embed.set_image(url="attachment://visitor.jpg")
        await channel.send(file=file, embed=embed)



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(NotificationCog(bot))