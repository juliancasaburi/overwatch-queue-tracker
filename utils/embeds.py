"""
Discord embed builders for queue status and messages.
"""

import discord
from datetime import datetime, timezone
from collections import defaultdict

from utils.ranks import (
    RANK_ORDER,
    RANK_DISPLAY_NAMES,
    RANK_EMOJIS,
    RANK_COLORS,
    get_rank_priority,
    format_battletag_display,
)


def create_queue_status_embed(
    queue_data: list[dict],
    bot_user: discord.User | None = None
) -> discord.Embed:
    """
    Create an embed showing the current queue status grouped by rank.
    
    Args:
        queue_data: List of dicts with discord_id, battletag, current_rank
        bot_user: Bot user for footer icon
        
    Returns:
        Discord embed with queue status
    """
    total_players = len(queue_data)
    
    # Group players by rank
    rank_groups: dict[str, list[str]] = defaultdict(list)
    for player in queue_data:
        rank = player.get("current_rank", "unknown").lower()
        discord_id = player.get("discord_id")
        rank_groups[rank].append(f"<@{discord_id}>")
    
    # Determine embed color based on highest rank in queue
    embed_color = 0x5865F2  # Discord blurple default
    for rank in RANK_ORDER:
        if rank in rank_groups:
            embed_color = RANK_COLORS.get(rank, embed_color)
            break
    
    # Create embed
    embed = discord.Embed(
        title="SA Queue Status",
        color=embed_color,
    )
    
    # Add player count
    if total_players == 0:
        embed.description = "No players currently in queue.\nUse `/queue` to join!"
    else:
        player_word = "player" if total_players == 1 else "players"
        embed.description = f"**{total_players}** {player_word} looking for a match"
    
    # Add rank groups (in order from highest to lowest)
    for rank in RANK_ORDER:
        if rank in rank_groups:
            players = rank_groups[rank]
            emoji = RANK_EMOJIS.get(rank, "")
            name = RANK_DISPLAY_NAMES.get(rank, rank.title())
            
            # Format field
            field_name = f"{emoji} {name} ({len(players)})"
            field_value = ", ".join(players)
            
            # Discord field value limit is 1024 chars
            if len(field_value) > 1024:
                field_value = field_value[:1020] + "..."
            
            embed.add_field(
                name=field_name,
                value=field_value,
                inline=False
            )
    
    # Add footer with timestamp
    now = datetime.now(timezone.utc)
    embed.set_footer(text="Ranks refresh every 10 minutes")
    embed.timestamp = now
    
    return embed


def create_registration_success_embed(
    battletag: str,
    rank: str,
    is_update: bool = False
) -> discord.Embed:
    """
    Create an embed for successful registration.
    
    Args:
        battletag: Player's BattleTag
        rank: Fetched rank
        is_update: True if updating existing registration
        
    Returns:
        Discord embed
    """
    display_tag = format_battletag_display(battletag)
    emoji = RANK_EMOJIS.get(rank, "")
    rank_name = RANK_DISPLAY_NAMES.get(rank, rank.title())
    
    action = "updated" if is_update else "registered"
    
    embed = discord.Embed(
        title="Registration Successful",
        description=f"Your BattleTag has been {action}!",
        color=0x2ECC71  # Green
    )
    
    embed.add_field(name="BattleTag", value=display_tag, inline=True)
    embed.add_field(name="Rank", value=f"{emoji} {rank_name}", inline=True)
    
    if rank == "unknown":
        embed.add_field(
            name="Note",
            value="Could not fetch your rank. This may be because your profile is private or the BattleTag was not found.",
            inline=False
        )
    
    return embed


def create_registration_error_embed(error_message: str) -> discord.Embed:
    """Create an embed for registration errors."""
    return discord.Embed(
        title="Registration Failed",
        description=error_message,
        color=0xE74C3C  # Red
    )


def create_queue_join_embed(position: int | None = None) -> discord.Embed:
    """Create an embed for successfully joining the queue."""
    embed = discord.Embed(
        title="Joined Queue",
        description="You are now in the queue! Use `/status` to see who else is looking for a match.",
        color=0x3498DB  # Blue
    )
    embed.add_field(
        name="Auto-Timeout",
        value="You will be automatically removed after 24 hours. Re-queue to reset the timer.",
        inline=False
    )
    return embed


def create_queue_refresh_embed() -> discord.Embed:
    """Create an embed for queue time refresh."""
    return discord.Embed(
        title="Queue Refreshed",
        description="Your queue timer has been reset. You will remain in queue for another 24 hours.",
        color=0x3498DB  # Blue
    )


def create_queue_leave_embed() -> discord.Embed:
    """Create an embed for leaving the queue."""
    return discord.Embed(
        title="Left Queue",
        description="You have been removed from the queue.",
        color=0xF39C12  # Orange
    )


def create_not_in_queue_embed() -> discord.Embed:
    """Create an embed when user tries to unqueue but isn't in queue."""
    return discord.Embed(
        title="Not in Queue",
        description="You are not currently in the queue.",
        color=0x95A5A6  # Gray
    )


def create_not_registered_embed() -> discord.Embed:
    """Create an embed when user needs to register first."""
    return discord.Embed(
        title="Not Registered",
        description="You need to register your BattleTag first!\nUse `/register <battletag>` (e.g., `/register Player#1234`)",
        color=0xE74C3C  # Red
    )


def create_admin_clear_embed(count: int) -> discord.Embed:
    """Create an embed for admin queue clear."""
    return discord.Embed(
        title="Queue Cleared",
        description=f"Removed **{count}** player(s) from the queue.",
        color=0x9B59B6  # Purple
    )


def create_admin_remove_embed(user: discord.User | discord.Member) -> discord.Embed:
    """Create an embed for admin removing a user from queue."""
    return discord.Embed(
        title="Player Removed",
        description=f"Removed {user.mention} from the queue.",
        color=0x9B59B6  # Purple
    )


def create_admin_refresh_embed(count: int) -> discord.Embed:
    """Create an embed for admin rank refresh."""
    return discord.Embed(
        title="Ranks Refreshed",
        description=f"Updated ranks for **{count}** queued player(s).",
        color=0x9B59B6  # Purple
    )


def create_help_embed() -> discord.Embed:
    """Create the help embed with all commands."""
    embed = discord.Embed(
        title="SA Queue Tracker - Help",
        description="Track Overwatch 2 queue times for South American servers.",
        color=0x5865F2  # Discord blurple
    )
    
    # User commands
    embed.add_field(
        name="User Commands",
        value=(
            "`/register <battletag>` - Register your BattleTag (e.g., Player#1234)\n"
            "`/queue` - Join the queue (24h timeout, re-queue to refresh)\n"
            "`/unqueue` - Leave the queue\n"
            "`/status` - Show current queue status by rank\n"
            "`/help` - Show this help message"
        ),
        inline=False
    )
    
    # Admin commands
    embed.add_field(
        name="Admin Commands",
        value=(
            "`/admin clear` - Clear the entire queue\n"
            "`/admin remove <user>` - Remove a user from the queue\n"
            "`/admin refresh` - Force refresh all queued player ranks"
        ),
        inline=False
    )
    
    # How it works
    embed.add_field(
        name="How It Works",
        value=(
            "1. Register your BattleTag to link your Overwatch 2 account\n"
            "2. Use `/queue` when you start looking for a match\n"
            "3. Use `/unqueue` when you're done playing\n"
            "4. Check `/status` to see who else is queuing\n\n"
            "Ranks are fetched from your public profile and refresh every 10 minutes. "
            "Queue status is automatically posted every 10 minutes."
        ),
        inline=False
    )
    
    embed.set_footer(text="All commands work in server channels and DMs")
    
    return embed


def create_error_embed(title: str, description: str) -> discord.Embed:
    """Create a generic error embed."""
    return discord.Embed(
        title=title,
        description=description,
        color=0xE74C3C  # Red
    )


def create_success_embed(title: str, description: str) -> discord.Embed:
    """Create a generic success embed."""
    return discord.Embed(
        title=title,
        description=description,
        color=0x2ECC71  # Green
    )
