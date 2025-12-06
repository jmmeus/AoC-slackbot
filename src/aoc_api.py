"""Client for fetching Advent of Code leaderboard data."""
import httpx
import asyncio
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AoCAPIClient:
    """Handles requests to the Advent of Code API."""

    def __init__(
        self,
        session_cookie: str,
        leaderboard_id: str,
        year: str = "2025",
        use_mock: bool = False,
        user_agent: Optional[str] = None
    ):
        """
        Initialize the AoC API client.

        Args:
            session_cookie: Your AoC session cookie
            leaderboard_id: Private leaderboard ID
            year: AoC year (default: 2025)
            use_mock: Use mock data instead of real API (for development)
            user_agent: Custom User-Agent string (should include contact info)
        """
        self.session_cookie = session_cookie
        self.leaderboard_id = leaderboard_id
        self.year = year
        self.use_mock = use_mock
        self.user_agent = user_agent or "AoC-Slack-Bot/1.0"
        self.base_url = f"https://adventofcode.com/{year}/leaderboard/private/view/{leaderboard_id}.json"

        if use_mock:
            try:
                from .mock_data import MockLeaderboardData
            except ImportError:
                from mock_data import MockLeaderboardData
            self.mock_data = MockLeaderboardData()
            logger.info("🔧 Mock mode enabled - using simulated data")

    async def fetch_leaderboard(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the current leaderboard data.

        Returns:
            Leaderboard data as dictionary, or None if request fails
        """
        if self.use_mock:
            return await self._fetch_mock_data()

        return await self._fetch_real_data()

    async def _fetch_mock_data(self) -> Dict[str, Any]:
        """Fetch mock data for development."""
        logger.info("Fetching mock leaderboard data...")
        # Simulate network delay
        await asyncio.sleep(0.1)
        return self.mock_data.get_next()

    async def _fetch_real_data(self) -> Optional[Dict[str, Any]]:
        """Fetch real data from AoC API."""
        headers = {
            'Cookie': f'session={self.session_cookie}',
            'User-Agent': self.user_agent
        }

        try:
            logger.info(f"Fetching leaderboard from AoC API...")

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    timeout=10.0,
                    follow_redirects=True
                )
                response.raise_for_status()

                data = response.json()
                logger.info(f"Successfully fetched leaderboard with {len(data.get('members', {}))} members")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching leaderboard: {e.response.status_code} - {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching leaderboard: {e}")
            return None
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching leaderboard: {e}")
            return None
