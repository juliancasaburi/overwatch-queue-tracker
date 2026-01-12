"""
Registration cog for player BattleTag registration.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging

from services import database
from services.overfast_api import get_client
from utils.ranks import normalize_battletag, format_battletag_display
from utils.embeds import (
    create_registration_success_embed,
    create_registration_error_embed,
)

logger = logging.getLogger(__name__)


class Registration(commands.Cog):
    """Cog for player registration commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="register", description="Register your BattleTag to track your rank")
    @app_commands.describe(battletag="Your BattleTag (e.g., Player#1234)")
    async def register(self, interaction: discord.Interaction, battletag: str):
        """
        Register a player's BattleTag.
        
        This command:
        1. Validates the BattleTag format
        2. Fetches the player's rank from the API
        3. Stores the registration in the database
        """
        await interaction.response.defer(thinking=True)
        
        # Validate BattleTag format
        api_battletag = normalize_battletag(battletag)
        if not api_battletag:
            embed = create_registration_error_embed(
                f"Invalid BattleTag format: `{battletag}`\n\n"
                "Please use the format `Username#1234`\n"
                "Example: `/register Player#1234`"
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Fetch rank from API
        discord_id = str(interaction.user.id)
        
        try:
            client = get_client()
            rank = await client.fetch_player_rank(api_battletag)
        except Exception as e:
            logger.error(f"Error fetching rank for {battletag}: {e}")
            rank = "unknown"
        
        # Register/update player in database
        try:
            is_new = await database.register_player(discord_id, api_battletag, rank)
            
            embed = create_registration_success_embed(
                battletag=api_battletag,
                rank=rank,
                is_update=not is_new
            )
            
            logger.info(
                f"{'Registered' if is_new else 'Updated'} player: "
                f"{interaction.user} ({discord_id}) -> {battletag} ({rank})"
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Database error during registration: {e}")
            embed = create_registration_error_embed(
                "An error occurred while saving your registration. Please try again later."
            )
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function for loading the cog."""
    await bot.add_cog(Registration(bot))
