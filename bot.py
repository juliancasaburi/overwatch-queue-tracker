"""
Overwatch 2 South America Queue Tracker Discord Bot

Main entry point for the bot. Handles:
- Bot initialization and cog loading
- Background task for automatic queue updates every 10 minutes
- Rank refresh for queued players
- 24-hour queue timeout cleanup
"""

import asyncio
import os
import logging
from pathlib import Path

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from services import database
from services.overfast_api import get_client, close_client
from utils.embeds import create_queue_status_embed

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("bot")

# Bot configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
QUEUE_CHANNEL_ID = os.getenv("QUEUE_CHANNEL_ID")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set")

if not QUEUE_CHANNEL_ID:
    logger.warning("QUEUE_CHANNEL_ID not set - automatic updates will be disabled")
    QUEUE_CHANNEL_ID = None
else:
    QUEUE_CHANNEL_ID = int(QUEUE_CHANNEL_ID)

# Bot intents
intents = discord.Intents.default()
intents.message_content = True  # Required for DM handling


class QueueTrackerBot(commands.Bot):
    """Main bot class with background tasks."""
    
    def __init__(self):
        super().__init__(
            command_prefix="!",  # Fallback prefix (we use slash commands)
            intents=intents,
            help_command=None  # We have our own help command
        )
    
    async def setup_hook(self):
        """Called when the bot is starting up."""
        # Initialize database
        await database.init_db()
        logger.info("Database initialized")
        
        # Load cogs
        cogs = [
            "cogs.registration",
            "cogs.queue",
            "cogs.admin",
            "cogs.help",
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")
        
        # Sync slash commands
        await self.tree.sync()
        logger.info("Slash commands synced")
        
        # Start background task
        if QUEUE_CHANNEL_ID:
            self.queue_update_task.start()
            logger.info("Started queue update background task")
    
    async def on_ready(self):
        """Called when the bot is fully connected."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="SA Queue | /help"
        )
        await self.change_presence(activity=activity)
        
        # Set bot avatar if not already set
        await self._set_avatar_if_needed()
    
    async def _set_avatar_if_needed(self):
        """Set the bot's avatar from the assets folder if available."""
        avatar_path = Path(__file__).parent / "assets" / "queue_icon.png"
        
        if not avatar_path.exists():
            logger.info("No avatar file found at assets/queue_icon.png")
            return
        
        try:
            with open(avatar_path, "rb") as f:
                avatar_data = f.read()
            
            await self.user.edit(avatar=avatar_data)
            logger.info("Bot avatar updated successfully")
        except discord.HTTPException as e:
            # Avatar might already be set or rate limited
            logger.debug(f"Could not update avatar: {e}")
        except Exception as e:
            logger.error(f"Error setting avatar: {e}")
    
    async def close(self):
        """Cleanup when bot is shutting down."""
        # Stop background task
        if self.queue_update_task.is_running():
            self.queue_update_task.cancel()
        
        # Close API client
        await close_client()
        
        await super().close()
        logger.info("Bot shut down cleanly")
    
    @tasks.loop(minutes=10)
    async def queue_update_task(self):
        """
        Background task that runs every 10 minutes.
        
        1. Removes players who have been in queue > 24 hours
        2. Refreshes ranks for all queued players
        3. Posts queue status to the configured channel
        """
        logger.info("Running queue update task...")
        
        try:
            # 1. Remove expired queue entries (24 hour timeout)
            expired_count = await database.remove_expired_from_queue(hours=24)
            if expired_count > 0:
                logger.info(f"Removed {expired_count} expired player(s) from queue")
            
            # 2. Refresh ranks for queued players
            queue_data = await database.get_queue_with_players()
            
            if queue_data:
                client = get_client()
                
                for player in queue_data:
                    battletag = player["battletag"]
                    discord_id = player["discord_id"]
                    
                    try:
                        new_rank = await client.fetch_player_rank(battletag)
                        await database.update_player_rank(discord_id, new_rank)
                    except Exception as e:
                        logger.error(f"Error refreshing rank for {battletag}: {e}")
                
                # Re-fetch queue data with updated ranks
                queue_data = await database.get_queue_with_players()
                logger.info(f"Refreshed ranks for {len(queue_data)} player(s)")
            
            # 3. Post status to channel
            if QUEUE_CHANNEL_ID:
                channel = self.get_channel(QUEUE_CHANNEL_ID)
                
                if channel is None:
                    # Try fetching if not in cache
                    try:
                        channel = await self.fetch_channel(QUEUE_CHANNEL_ID)
                    except discord.NotFound:
                        logger.error(f"Queue channel {QUEUE_CHANNEL_ID} not found")
                        return
                    except discord.Forbidden:
                        logger.error(f"No access to queue channel {QUEUE_CHANNEL_ID}")
                        return
                
                embed = create_queue_status_embed(queue_data, self.user)
                await channel.send(embed=embed)
                logger.info(f"Posted queue status to channel {channel.name}")
        
        except Exception as e:
            logger.error(f"Error in queue update task: {e}", exc_info=True)
    
    @queue_update_task.before_loop
    async def before_queue_update(self):
        """Wait until the bot is ready before starting the task."""
        await self.wait_until_ready()


def main():
    """Main entry point."""
    bot = QueueTrackerBot()
    
    try:
        bot.run(DISCORD_TOKEN, log_handler=None)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
