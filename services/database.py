"""
Database service for SQLite operations.
Handles player registration and queue management.
"""

import aiosqlite
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "bot.db"


async def init_db() -> None:
    """Initialize the database and create tables if they don't exist."""
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Create players table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id TEXT UNIQUE NOT NULL,
                battletag TEXT NOT NULL,
                current_rank TEXT DEFAULT 'unknown',
                last_rank_update TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create queue table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id TEXT UNIQUE NOT NULL,
                queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (discord_id) REFERENCES players(discord_id)
            )
        """)
        
        await db.commit()


# ============================================================================
# Player Operations
# ============================================================================

async def register_player(discord_id: str, battletag: str, rank: str = "unknown") -> bool:
    """
    Register a new player or update existing registration.
    
    Args:
        discord_id: Discord user ID
        battletag: Player's BattleTag (API format: Name-1234)
        rank: Initial rank (default: unknown)
        
    Returns:
        True if new registration, False if updated existing
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if player exists
        cursor = await db.execute(
            "SELECT id FROM players WHERE discord_id = ?",
            (discord_id,)
        )
        existing = await cursor.fetchone()
        
        now = datetime.now(timezone.utc).isoformat()
        
        if existing:
            # Update existing player
            await db.execute(
                """UPDATE players 
                   SET battletag = ?, current_rank = ?, last_rank_update = ?
                   WHERE discord_id = ?""",
                (battletag, rank, now, discord_id)
            )
            await db.commit()
            return False
        else:
            # Insert new player
            await db.execute(
                """INSERT INTO players (discord_id, battletag, current_rank, last_rank_update)
                   VALUES (?, ?, ?, ?)""",
                (discord_id, battletag, rank, now)
            )
            await db.commit()
            return True


async def get_player(discord_id: str) -> Optional[dict]:
    """
    Get a player's registration info.
    
    Args:
        discord_id: Discord user ID
        
    Returns:
        Player dict or None if not registered
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM players WHERE discord_id = ?",
            (discord_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_player_rank(discord_id: str, rank: str) -> None:
    """
    Update a player's rank.
    
    Args:
        discord_id: Discord user ID
        rank: New rank value
    """
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE players SET current_rank = ?, last_rank_update = ?
               WHERE discord_id = ?""",
            (rank, now, discord_id)
        )
        await db.commit()


async def get_all_players() -> list[dict]:
    """Get all registered players."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM players")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# ============================================================================
# Queue Operations
# ============================================================================

async def add_to_queue(discord_id: str) -> bool:
    """
    Add a player to the queue or refresh their queue time.
    
    Args:
        discord_id: Discord user ID
        
    Returns:
        True if newly added, False if refreshed existing entry
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if already in queue
        cursor = await db.execute(
            "SELECT id FROM queue WHERE discord_id = ?",
            (discord_id,)
        )
        existing = await cursor.fetchone()
        
        now = datetime.now(timezone.utc).isoformat()
        
        if existing:
            # Refresh queue time
            await db.execute(
                "UPDATE queue SET queued_at = ? WHERE discord_id = ?",
                (now, discord_id)
            )
            await db.commit()
            return False
        else:
            # Add to queue
            await db.execute(
                "INSERT INTO queue (discord_id, queued_at) VALUES (?, ?)",
                (discord_id, now)
            )
            await db.commit()
            return True


async def remove_from_queue(discord_id: str) -> bool:
    """
    Remove a player from the queue.
    
    Args:
        discord_id: Discord user ID
        
    Returns:
        True if removed, False if wasn't in queue
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM queue WHERE discord_id = ? RETURNING id",
            (discord_id,)
        )
        result = await cursor.fetchone()
        await db.commit()
        return result is not None


async def is_in_queue(discord_id: str) -> bool:
    """Check if a player is currently in the queue."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM queue WHERE discord_id = ?",
            (discord_id,)
        )
        result = await cursor.fetchone()
        return result is not None


async def get_queue_with_players() -> list[dict]:
    """
    Get all players currently in queue with their player info.
    
    Returns:
        List of dicts with queue and player info combined
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT q.discord_id, q.queued_at, p.battletag, p.current_rank
            FROM queue q
            JOIN players p ON q.discord_id = p.discord_id
            ORDER BY q.queued_at ASC
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_queued_player_ids() -> list[str]:
    """Get list of discord IDs for all players in queue."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT discord_id FROM queue")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def clear_queue() -> int:
    """
    Clear all players from the queue.
    
    Returns:
        Number of players removed
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM queue")
        count = (await cursor.fetchone())[0]
        
        await db.execute("DELETE FROM queue")
        await db.commit()
        return count


async def remove_expired_from_queue(hours: int = 24) -> int:
    """
    Remove players who have been in queue longer than specified hours.
    
    Args:
        hours: Maximum hours in queue before removal
        
    Returns:
        Number of players removed
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    cutoff_str = cutoff.isoformat()
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Count expired entries
        cursor = await db.execute(
            "SELECT COUNT(*) FROM queue WHERE queued_at < ?",
            (cutoff_str,)
        )
        count = (await cursor.fetchone())[0]
        
        # Remove expired entries
        await db.execute(
            "DELETE FROM queue WHERE queued_at < ?",
            (cutoff_str,)
        )
        await db.commit()
        return count


async def get_queue_count() -> int:
    """Get the number of players currently in queue."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM queue")
        result = await cursor.fetchone()
        return result[0] if result else 0
