import discord
from discord.ext import commands
from discord import app_commands
import logging

from db import db_module
import core.exceptions as exceptions

logger = logging.getLogger(__name__)

class SubscribeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(
        name="subscribe"
    )
    @app_commands.guild_only()
    async def subscribe(
        self,
        interaction: discord.Interaction,
        serial_number: str,
        pairing_code: str,
        channel: discord.TextChannel,
    ):
        guild_id = interaction.guild_id
        
        try:
            if not await db_module.verify_pair_code(serial_number, pairing_code):
                await interaction.response.send_message(
                    "❌ Invalid serial number or pairing code. Please check your credentials and try again.",
                    ephemeral=True,
                )
                return
            await db_module.add_subscription(serial_number, guild_id, channel.id)
        except exceptions.DatabaseError:
            logger.exception("Failed to subscribe device %s", serial_number)
            await interaction.response.send_message("⚠️ Internal error.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"✅ Device `{serial_number}` successfully subscribed to {channel.mention}!",
            ephemeral=True,
        )

    @app_commands.command(
            name="unsubscribe"
        )
    @app_commands.guild_only()
    async def unsubscribe(
        self,
        interaction: discord.Interaction,
        serial_number: str,
    ):
        guild_id = interaction.guild_id
        
        try:
            if not await db_module.remove_subscription(serial_number, guild_id):
                await interaction.response.send_message(
                    f"❌ No active subscription found for device `{serial_number}` in this server.",
                    ephemeral=True
                )
                return
            
        except exceptions.DatabaseError:
            logger.exception("Failed to unsubscribe device %s", serial_number)
            await interaction.response.send_message("⚠️ Internal error.", ephemeral=True)
            return
        
        await interaction.response.send_message(
            f"✅ Device {serial_number} has been unsubscribed from this server.",
            ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SubscribeCog(bot))