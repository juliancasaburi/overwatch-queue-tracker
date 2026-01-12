"""
Rank utilities and constants for Overwatch 2 skill tiers.
"""

# Rank order from highest to lowest
RANK_ORDER = [
    "ultimate",      # Champion (top 500)
    "grandmaster",
    "master",
    "diamond",
    "platinum",
    "gold",
    "silver",
    "bronze",
    "unranked",      # No ranked roles this season
    "unknown",       # Private profile / API error / invalid battletag
]

# Display names for each rank
RANK_DISPLAY_NAMES = {
    "ultimate": "Champion",
    "grandmaster": "Grandmaster",
    "master": "Master",
    "diamond": "Diamond",
    "platinum": "Platinum",
    "gold": "Gold",
    "silver": "Silver",
    "bronze": "Bronze",
    "unranked": "Unranked",
    "unknown": "Unknown",
}

# Emojis for each rank
RANK_EMOJIS = {
    "ultimate": "👑",
    "grandmaster": "🏆",
    "master": "💜",
    "diamond": "💎",
    "platinum": "🥈",
    "gold": "🥇",
    "silver": "⚪",
    "bronze": "🥉",
    "unranked": "📊",
    "unknown": "❓",
}

# Colors for embeds (Discord color format)
RANK_COLORS = {
    "ultimate": 0xFFD700,      # Gold
    "grandmaster": 0xFFAA00,   # Orange-gold
    "master": 0x9B59B6,        # Purple
    "diamond": 0x3498DB,       # Blue
    "platinum": 0x95A5A6,      # Silver-gray
    "gold": 0xF1C40F,          # Yellow
    "silver": 0xBDC3C7,        # Light gray
    "bronze": 0xCD7F32,        # Bronze
    "unranked": 0x7F8C8D,      # Gray
    "unknown": 0x95A5A6,       # Gray
}


def get_rank_priority(rank: str) -> int:
    """
    Get the priority of a rank (lower = higher rank).
    Used for sorting players by rank.
    """
    try:
        return RANK_ORDER.index(rank.lower())
    except ValueError:
        return len(RANK_ORDER)  # Unknown ranks go to the end


def get_highest_rank(competitive_data: dict | None) -> str:
    """
    Determine the highest role rank from competitive data.
    
    Args:
        competitive_data: The 'competitive' field from player summary API response
        
    Returns:
        The highest rank division as a string (e.g., 'diamond', 'master')
        Returns 'unranked' if no roles are ranked this season
        Returns 'unknown' if data is missing/private
    """
    if not competitive_data:
        return "unknown"
    
    pc_data = competitive_data.get("pc")
    if not pc_data:
        return "unknown"
    
    roles = ["tank", "damage", "support"]
    found_ranks = []
    
    for role in roles:
        role_data = pc_data.get(role)
        if role_data and role_data.get("division"):
            found_ranks.append(role_data["division"].lower())
    
    if not found_ranks:
        # Player has PC data but no ranked roles this season
        return "unranked"
    
    # Return the highest rank based on tier order
    for rank in RANK_ORDER:
        if rank in found_ranks:
            return rank
    
    return "unknown"


def format_rank_display(rank: str) -> str:
    """
    Format a rank for display with emoji and name.
    
    Args:
        rank: The rank key (e.g., 'diamond')
        
    Returns:
        Formatted string like '💎 Diamond'
    """
    rank_lower = rank.lower()
    emoji = RANK_EMOJIS.get(rank_lower, "❓")
    name = RANK_DISPLAY_NAMES.get(rank_lower, "Unknown")
    return f"{emoji} {name}"


def normalize_battletag(battletag: str) -> str | None:
    """
    Normalize a BattleTag to API format.
    
    Converts 'Player#1234' to 'Player-1234' for API calls.
    Returns None if the format is invalid.
    
    Args:
        battletag: User-provided BattleTag
        
    Returns:
        API-formatted BattleTag or None if invalid
    """
    battletag = battletag.strip()
    
    # Check for valid format: Name#Numbers
    if "#" in battletag:
        parts = battletag.split("#")
        if len(parts) == 2 and parts[0] and parts[1].isdigit():
            return f"{parts[0]}-{parts[1]}"
    
    # Already in API format (Name-Numbers)
    if "-" in battletag:
        parts = battletag.rsplit("-", 1)
        if len(parts) == 2 and parts[0] and parts[1].isdigit():
            return battletag
    
    return None


def format_battletag_display(battletag: str) -> str:
    """
    Format a BattleTag for display (ensure # format).
    
    Args:
        battletag: BattleTag in any format
        
    Returns:
        Display-formatted BattleTag with #
    """
    if "-" in battletag and "#" not in battletag:
        parts = battletag.rsplit("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return f"{parts[0]}#{parts[1]}"
    return battletag
