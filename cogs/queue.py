"""
Queue cog for queue management commands.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging

from services import database
from utils.embeds import (
    create_queue_status_embed,
    create_queue_join_embed,
    create_queue_refresh_embed,
    create_queue_leave_embed,
    create_not_in_queue_embed,
    create_not_registered_embed,
)

logger = logging.getLogger(__name__)


class Queue(commands.Cog):
    """Cog for queue management commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="queue", description="Join the queue to find other players")
    async def queue(self, interaction: discord.Interaction):
        """
        Add the player to the queue.
        
        Requirements:
        - Player must be registered first
        - If already in queue, refreshes the timeout
        """
        discord_id = str(interaction.user.id)
        
        # Check if player is registered
        player = await database.get_player(discord_id)
        if not player:
            embed = create_not_registered_embed()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Add to queue (or refresh if already in)
        is_new = await database.add_to_queue(discord_id)
        
        if is_new:
            embed = create_queue_join_embed()
            logger.info(f"Player joined queue: {interaction.user} ({discord_id})")
        else:
            embed = create_queue_refresh_embed()
            logger.info(f"Player refreshed queue: {interaction.user} ({discord_id})")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="unqueue", description="Leave the queue")
    async def unqueue(self, interaction: discord.Interaction):
        """Remove the player from the queue."""
        discord_id = str(interaction.user.id)
        
        removed = await database.remove_from_queue(discord_id)
        
        if removed:
            embed = create_queue_leave_embed()
            logger.info(f"Player left queue: {interaction.user} ({discord_id})")
        else:
            embed = create_not_in_queue_embed()
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="status", description="Show current queue status")
    async def status(self, interaction: discord.Interaction):
        """Display the current queue status grouped by rank."""
        await interaction.response.defer()
        
        # Get queue data with player info
        queue_data = await database.get_queue_with_players()
        
        # Create and send embed
        embed = create_queue_status_embed(queue_data, self.bot.user)
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function for loading the cog."""
    await bot.add_cog(Queue(bot))
