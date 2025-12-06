"""Polling service for fetching AoC leaderboard updates."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from slack_bolt.app.async_app import AsyncApp
import logging
from typing import Optional
from datetime import datetime
from .aoc_api import AoCAPIClient
from .storage import Storage
from .differ import detect_changes
from .formatters.notifications import build_notification_blocks
from .slack_rate_limiter import slack_rate_limiter
from .cookie_monitor import CookieMonitor

logger = logging.getLogger(__name__)


class LeaderboardPoller:
    """Handles periodic polling of the AoC leaderboard."""

    def __init__(
        self,
        app: AsyncApp,
        api_client: AoCAPIClient,
        storage: Storage,
        channel_id: str,
        cookie_monitor: Optional[CookieMonitor] = None,
        use_cron: bool = True
    ):
        """
        Initialize the poller.

        Args:
            app: Slack Bolt app instance
            api_client: AoC API client
            storage: Storage instance
            channel_id: Slack channel ID for notifications
            cookie_monitor: Cookie monitor instance (optional)
            use_cron: Use cron scheduling instead of interval (default: True)
        """
        self.app = app
        self.api_client = api_client
        self.storage = storage
        self.channel_id = channel_id
        self.cookie_monitor = cookie_monitor
        self.use_cron = use_cron
        self.scheduler = AsyncIOScheduler()

    async def poll_and_notify(self):
        """Fetch leaderboard, detect changes, and post notifications."""
        logger.info("Polling AoC leaderboard...")

        try:
            # Fetch new data
            new_data = await self.api_client.fetch_leaderboard()

            if not new_data:
                # Fetch failed - check if cookie expired
                if self.cookie_monitor:
                    cookie_valid = await self.cookie_monitor.check_cookie_validity()

                    if not cookie_valid:
                        logger.error("Cookie expired - using cached data")

                        # Notify admin (only once per expiry)
                        if not self.cookie_monitor.admin_notified_expired:
                            await self.cookie_monitor.notify_admin_cookie_expired()

                        # Get cached data and pass timestamp to notification
                        cached = self.storage.get_latest_snapshot()
                        if cached:
                            fetched_at_dt = datetime.fromisoformat(cached['fetched_at']) if isinstance(cached['fetched_at'], str) else cached['fetched_at']
                            last_fetch_ts = int(fetched_at_dt.timestamp())

                            # Calculate age for logging
                            age_hours = int((datetime.now() - fetched_at_dt).total_seconds() / 3600)
                            logger.info(f"Cached data available (age: {age_hours}h)")

                            # Note: Not posting cached leaderboard automatically to avoid spam
                            # Users can use /leaderboard command to see cached data
                        return
                    else:
                        # Cookie valid but API failed (network issue?)
                        logger.warning("API fetch failed but cookie valid - likely network issue")
                else:
                    logger.warning("Failed to fetch leaderboard data")
                return

            # Get previous snapshot
            previous = self.storage.get_latest_snapshot()

            # Save new snapshot
            snapshot_id = self.storage.save_snapshot(new_data)
            logger.info(f"Saved snapshot {snapshot_id}")

            # If this is the first snapshot, don't post notifications
            if not previous:
                logger.info("First snapshot saved, no notifications to send")
                return

            # Detect changes
            new_stars, rank_changes, new_members = detect_changes(
                previous['data'],
                new_data
            )

            # Check if there are any changes
            if not new_stars and not rank_changes and not new_members:
                logger.info("No changes detected")
                return

            # Build and send notification
            logger.info(
                f"Changes detected: {len(new_stars)} stars, "
                f"{len(rank_changes)} rank changes, {len(new_members)} new members"
            )

            blocks = build_notification_blocks(new_stars, rank_changes, new_members)

            # Build fallback text for notifications and screen readers
            fallback_parts = []
            if new_stars:
                fallback_parts.append(f"{len(new_stars)} new star{'s' if len(new_stars) != 1 else ''}")
            if rank_changes:
                fallback_parts.append(f"{len(rank_changes)} rank change{'s' if len(rank_changes) != 1 else ''}")
            if new_members:
                fallback_parts.append(f"{len(new_members)} new member{'s' if len(new_members) != 1 else ''}")

            fallback_text = f"AoC Leaderboard Update: {', '.join(fallback_parts)}"

            # Wait for rate limit slot before posting
            await slack_rate_limiter.wait_for_slot(tier=1)

            await self.app.client.chat_postMessage(
                channel=self.channel_id,
                text=fallback_text,
                blocks=blocks
            )

            logger.info("Notification posted successfully")

        except Exception as e:
            logger.error(f"Error during poll_and_notify: {e}", exc_info=True)

    def start(self):
        """Start the polling scheduler."""
        if self.use_cron:
            # Cron-style scheduling: Every hour at :00, :20, :40
            self.scheduler.add_job(
                self.poll_and_notify,
                CronTrigger(minute='0,20,40'),
                id='leaderboard_poll',
                replace_existing=True
            )
            logger.info("Poller started with cron schedule (every 20 min at :00, :20, :40)")
        else:
            # Interval-based scheduling (for DEV_MODE)
            self.scheduler.add_job(
                self.poll_and_notify,
                'interval',
                seconds=60,  # DEV_MODE uses 60s
                id='leaderboard_poll',
                replace_existing=True
            )
            logger.info("Poller started with 60s interval (DEV_MODE)")

        # Schedule daily cookie health check (9 AM)
        if self.cookie_monitor:
            self.scheduler.add_job(
                self.cookie_monitor.daily_health_check,
                CronTrigger(hour=9),
                id='daily_cookie_check',
                replace_existing=True
            )
            logger.info("Daily cookie health check scheduled for 9 AM")

        self.scheduler.start()

    def stop(self):
        """Stop the polling scheduler."""
        self.scheduler.shutdown()
        logger.info("Poller stopped")
