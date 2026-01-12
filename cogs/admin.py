"""
Admin cog for administrative commands.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging

from services import database
from services.overfast_api import get_client
from utils.embeds import (
    create_admin_clear_embed,
    create_admin_remove_embed,
    create_admin_refresh_embed,
    create_error_embed,
    create_not_in_queue_embed,
)

logger = logging.getLogger(__name__)


class Admin(commands.Cog):
    """Cog for administrative commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    admin_group = app_commands.Group(
        name="admin",
        description="Administrative commands for queue management",
        default_permissions=discord.Permissions(administrator=True)
    )
    
    @admin_group.command(name="clear", description="Clear all players from the queue")
    async def admin_clear(self, interaction: discord.Interaction):
        """Clear the entire queue."""
        count = await database.clear_queue()
        
        embed = create_admin_clear_embed(count)
        logger.info(f"Admin {interaction.user} cleared queue ({count} players)")
        
        await interaction.response.send_message(embed=embed)
    
    @admin_group.command(name="remove", description="Remove a specific user from the queue")
    @app_commands.describe(user="The user to remove from the queue")
    async def admin_remove(
        self,
        interaction: discord.Interaction,
        user: discord.User
    ):
        """Remove a specific user from the queue."""
        discord_id = str(user.id)
        
        removed = await database.remove_from_queue(discord_id)
        
        if removed:
            embed = create_admin_remove_embed(user)
            logger.info(f"Admin {interaction.user} removed {user} from queue")
        else:
            embed = create_not_in_queue_embed()
            embed.description = f"{user.mention} is not currently in the queue."
        
        await interaction.response.send_message(embed=embed)
    
    @admin_group.command(name="refresh", description="Force refresh ranks for all queued players")
    async def admin_refresh(self, interaction: discord.Interaction):
        """Force refresh all queued player ranks immediately."""
        await interaction.response.defer(thinking=True)
        
        # Get all queued players
        queue_data = await database.get_queue_with_players()
        
        if not queue_data:
            embed = create_error_embed(
                "No Players in Queue",
                "There are no players in the queue to refresh."
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Fetch updated ranks
        client = get_client()
        updated_count = 0
        
        for player in queue_data:
            battletag = player["battletag"]
            discord_id = player["discord_id"]
            
            try:
                new_rank = await client.fetch_player_rank(battletag)
                await database.update_player_rank(discord_id, new_rank)
                updated_count += 1
                logger.debug(f"Refreshed rank for {battletag}: {new_rank}")
            except Exception as e:
                logger.error(f"Error refreshing rank for {battletag}: {e}")
        
        embed = create_admin_refresh_embed(updated_count)
        logger.info(f"Admin {interaction.user} force-refreshed {updated_count} player ranks")
        
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function for loading the cog."""
    await bot.add_cog(Admin(bot))
