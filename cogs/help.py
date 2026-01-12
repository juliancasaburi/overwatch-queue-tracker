"""
Help cog for displaying bot usage information.
"""

import discord
from discord import app_commands
from discord.ext import commands

from utils.embeds import create_help_embed


class Help(commands.Cog):
    """Cog for the help command."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="help", description="Show help information and available commands")
    async def help(self, interaction: discord.Interaction):
        """Display help information about the bot."""
        embed = create_help_embed()
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function for loading the cog."""
    await bot.add_cog(Help(bot))
