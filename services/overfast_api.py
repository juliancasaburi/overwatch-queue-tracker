"""
OverFast API client for fetching Overwatch 2 player data.
API Documentation: https://overfast-api.tekrop.fr/docs
"""

import asyncio
import aiohttp
from typing import Optional
import logging

from utils.ranks import get_highest_rank, normalize_battletag

logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "https://overfast-api.tekrop.fr"
REQUEST_DELAY = 0.1  # 100ms between requests to avoid rate limiting


class OverFastAPIError(Exception):
    """Base exception for API errors."""
    pass


class PlayerNotFoundError(OverFastAPIError):
    """Player not found on Blizzard servers."""
    pass


class PrivateProfileError(OverFastAPIError):
    """Player profile is private."""
    pass


class RateLimitError(OverFastAPIError):
    """API rate limit exceeded."""
    def __init__(self, retry_after: int = 1):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after} seconds.")


class OverFastClient:
    """Async client for the OverFast API."""
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(
                base_url=BASE_URL,
                timeout=timeout,
                headers={"Accept": "application/json"}
            )
        return self._session
    
    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get_player_summary(self, battletag: str) -> dict:
        """
        Fetch a player's summary data including competitive ranks.
        
        Args:
            battletag: BattleTag in API format (Name-1234)
            
        Returns:
            Player summary dict from API
            
        Raises:
            PlayerNotFoundError: If player doesn't exist
            PrivateProfileError: If profile is private
            RateLimitError: If rate limited
            OverFastAPIError: For other API errors
        """
        session = await self._get_session()
        
        try:
            async with session.get(f"/players/{battletag}/summary") as response:
                if response.status == 200:
                    return await response.json()
                
                elif response.status == 404:
                    raise PlayerNotFoundError(f"Player '{battletag}' not found")
                
                elif response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 1))
                    raise RateLimitError(retry_after)
                
                elif response.status == 500:
                    # API returns 500 for private profiles sometimes
                    data = await response.json()
                    if "private" in str(data).lower():
                        raise PrivateProfileError(f"Profile '{battletag}' is private")
                    raise OverFastAPIError(f"API error: {data}")
                
                else:
                    text = await response.text()
                    raise OverFastAPIError(f"HTTP {response.status}: {text}")
                    
        except aiohttp.ClientError as e:
            raise OverFastAPIError(f"Network error: {e}")
    
    async def fetch_player_rank(self, battletag: str) -> str:
        """
        Fetch a player's highest competitive rank.
        
        Args:
            battletag: BattleTag in user format (Name#1234) or API format (Name-1234)
            
        Returns:
            Rank string (e.g., 'diamond', 'master', 'unknown')
        """
        # Normalize battletag to API format
        api_battletag = normalize_battletag(battletag)
        if not api_battletag:
            logger.warning(f"Invalid battletag format: {battletag}")
            return "unknown"
        
        try:
            summary = await self.get_player_summary(api_battletag)
            competitive_data = summary.get("competitive")
            return get_highest_rank(competitive_data)
            
        except PlayerNotFoundError:
            logger.info(f"Player not found: {battletag}")
            return "unknown"
            
        except PrivateProfileError:
            logger.info(f"Private profile: {battletag}")
            return "unknown"
            
        except RateLimitError as e:
            logger.warning(f"Rate limited, waiting {e.retry_after}s")
            await asyncio.sleep(e.retry_after)
            # Retry once after waiting
            try:
                summary = await self.get_player_summary(api_battletag)
                competitive_data = summary.get("competitive")
                return get_highest_rank(competitive_data)
            except Exception:
                return "unknown"
                
        except OverFastAPIError as e:
            logger.error(f"API error for {battletag}: {e}")
            return "unknown"
    
    async def fetch_multiple_ranks(
        self, 
        battletags: list[str],
        delay: float = REQUEST_DELAY
    ) -> dict[str, str]:
        """
        Fetch ranks for multiple players with rate limiting.
        
        Args:
            battletags: List of BattleTags
            delay: Delay between requests in seconds
            
        Returns:
            Dict mapping battletag -> rank
        """
        results = {}
        
        for i, battletag in enumerate(battletags):
            if i > 0:
                await asyncio.sleep(delay)
            
            rank = await self.fetch_player_rank(battletag)
            results[battletag] = rank
            logger.debug(f"Fetched rank for {battletag}: {rank}")
        
        return results


# Global client instance
_client: Optional[OverFastClient] = None


def get_client() -> OverFastClient:
    """Get the global OverFast API client."""
    global _client
    if _client is None:
        _client = OverFastClient()
    return _client


async def close_client() -> None:
    """Close the global API client."""
    global _client
    if _client:
        await _client.close()
        _client = None
