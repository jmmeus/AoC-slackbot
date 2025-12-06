"""Rate limiting for Slack API calls."""
from aiolimiter import AsyncLimiter
import logging

logger = logging.getLogger(__name__)


class SlackRateLimiter:
    """
    Rate limiter for Slack API methods.

    Implements per-method rate limiting based on Slack's tier structure.
    This is preventive - Slack Bolt has built-in retry logic, but we avoid
    hitting rate limits in the first place.

    Slack Rate Limit Tiers:
    - Tier 1 (chat.postMessage): ~1/sec (we use conservative 1/sec)
    - Tier 2 (most methods): ~20/min
    - Tier 3 (bulk ops): ~50/min
    """

    def __init__(self):
        # Tier 1: chat.postMessage (1 per second, conservative)
        self.tier1_limiter = AsyncLimiter(1, 1)  # 1 request per 1 second

        # Tier 2: Most other methods (20 per minute, conservative)
        self.tier2_limiter = AsyncLimiter(15, 60)  # 15 requests per 60 seconds

        # Tier 3: Bulk operations (50 per minute)
        self.tier3_limiter = AsyncLimiter(40, 60)  # 40 requests per 60 seconds

        logger.info("Slack rate limiter initialized")

    async def wait_for_slot(self, tier: int = 2):
        """
        Wait for a rate limit slot to become available.

        Args:
            tier: Rate limit tier (1, 2, or 3)
                  1 = chat.postMessage (slowest)
                  2 = most other methods (default)
                  3 = bulk operations (fastest)
        """
        if tier == 1:
            async with self.tier1_limiter:
                logger.debug("Acquired Tier 1 rate limit slot (chat.postMessage)")
        elif tier == 2:
            async with self.tier2_limiter:
                logger.debug("Acquired Tier 2 rate limit slot")
        elif tier == 3:
            async with self.tier3_limiter:
                logger.debug("Acquired Tier 3 rate limit slot")
        else:
            logger.warning(f"Unknown tier {tier}, defaulting to Tier 2")
            async with self.tier2_limiter:
                pass


# Global rate limiter instance
slack_rate_limiter = SlackRateLimiter()
