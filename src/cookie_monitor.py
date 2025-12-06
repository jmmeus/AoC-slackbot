"""Cookie monitoring and validation for AoC session cookies."""
import hashlib
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional

try:
    from .storage import Storage
except ImportError:
    from storage import Storage

logger = logging.getLogger(__name__)


class CookieMonitor:
    """
    Monitors AoC session cookie health and sends alerts.

    Features:
    - Validates cookie on demand
    - Tracks cookie age
    - Sends reminders when cookie is old (>21 days)
    - Notifies admin when cookie expires
    """

    def __init__(
        self,
        session_cookie: str,
        storage: Storage,
        slack_client,
        admin_user_id: str,
        channel_id: str,
        year: str = "2025",
        user_agent: str = "AoC-Slack-Bot/1.0",
        reminders_enabled: bool = True
    ):
        """
        Initialize cookie monitor.

        Args:
            session_cookie: AoC session cookie value
            storage: Storage instance
            slack_client: Slack Bolt client
            admin_user_id: Slack user ID of admin
            channel_id: Channel to post public messages
            year: AoC year
            user_agent: User-Agent for API requests
            reminders_enabled: Whether to send age reminders
        """
        self.session_cookie = session_cookie
        self.storage = storage
        self.slack_client = slack_client
        self.admin_user_id = admin_user_id
        self.channel_id = channel_id
        self.year = year
        self.user_agent = user_agent
        self.reminders_enabled = reminders_enabled
        self.admin_notified_expired = False

        # Ensure cookie is being tracked
        self._ensure_cookie_tracked()

    def _hash_cookie(self, cookie: str) -> str:
        """Create SHA256 hash of cookie value."""
        return hashlib.sha256(cookie.encode()).hexdigest()

    def _ensure_cookie_tracked(self):
        """Track cookie in database if new or changed."""
        current_hash = self._hash_cookie(self.session_cookie)
        metadata = self.storage.get_cookie_metadata()

        if not metadata or metadata['cookie_hash'] != current_hash:
            # New or changed cookie - track it
            self.storage.upsert_cookie_metadata(
                cookie_hash=current_hash,
                first_seen=datetime.now()
            )
            logger.info("Cookie changed or first run - tracking new cookie")

    async def check_cookie_validity(self) -> bool:
        """
        Test if session cookie is still valid.

        Returns:
            True if cookie works, False if expired
        """
        try:
            async with httpx.AsyncClient() as client:
                # Access an authenticated endpoint
                response = await client.get(
                    f'https://adventofcode.com/{self.year}/settings',
                    cookies={'session': self.session_cookie},
                    headers={'User-Agent': self.user_agent},
                    follow_redirects=False,
                    timeout=10.0
                )

                # Valid cookie: 200 OK
                # Expired cookie: 302 redirect to login, or 400 error
                if response.status_code == 200:
                    logger.debug("Cookie validation: OK")
                    self.storage.update_cookie_last_verified()
                    return True
                else:
                    logger.warning(f"Cookie validation failed: HTTP {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Cookie validation error: {e}")
            # On error, assume cookie might be invalid
            return False

    def get_cookie_age_days(self) -> int:
        """
        Get age of current cookie in days.

        Returns:
            Age in days, or 0 if unknown
        """
        metadata = self.storage.get_cookie_metadata()
        if not metadata or not metadata['first_seen']:
            return 0

        age = datetime.now() - metadata['first_seen']
        return age.days

    def should_send_age_reminder(self) -> bool:
        """
        Check if we should send age reminder.

        Returns:
            True if reminder should be sent
        """
        if not self.reminders_enabled:
            return False

        age_days = self.get_cookie_age_days()

        # Only remind if >21 days old
        REMINDER_START_DAYS = 21
        if age_days < REMINDER_START_DAYS:
            return False

        metadata = self.storage.get_cookie_metadata()
        last_reminder = metadata.get('last_reminder_sent') if metadata else None

        if not last_reminder:
            # Never sent reminder, send now
            return True

        # Send if last reminder was >24 hours ago
        time_since_reminder = datetime.now() - last_reminder
        return time_since_reminder.total_seconds() >= 86400  # 24 hours

    async def notify_admin_cookie_expired(self):
        """Send DM to admin about expired cookie."""
        if not self.admin_user_id:
            logger.warning("No ADMIN_USER_ID configured - cannot send DM")
            return

        try:
            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "🚨 AoC Bot: Session Cookie Expired"}
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Your Advent of Code session cookie has expired. "
                                "The bot will continue to show the last known leaderboard, but won't fetch new updates."
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Impact:*\n"
                                "• New puzzles won't appear\n"
                                "• Score changes won't be detected\n"
                                "• Users will see stale data"
                    }
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*To fix:*\n"
                                "1. Log in to https://adventofcode.com\n"
                                "2. Open DevTools (F12) → Application → Cookies\n"
                                "3. Copy the `session` cookie value\n"
                                "4. Update `.env`: `AOC_SESSION_COOKIE=<new value>`\n"
                                "5. Restart the bot"
                    }
                },
                {
                    "type": "context",
                    "elements": [{
                        "type": "mrkdwn",
                        "text": "_Session cookies last ~30 days. Consider setting a calendar reminder!_"
                    }]
                }
            ]

            await self.slack_client.chat_postMessage(
                channel=self.admin_user_id,
                text="🚨 AoC Bot: Session Cookie Expired - Please renew your cookie",
                blocks=blocks
            )

            logger.info("Sent cookie expiry notification to admin")
            self.admin_notified_expired = True

        except Exception as e:
            logger.error(f"Failed to send admin DM: {e}")

    async def notify_admin_cookie_aging(self, age_days: int):
        """
        Send DM to admin about aging cookie.

        Args:
            age_days: Current age of cookie in days
        """
        if not self.admin_user_id:
            logger.warning("No ADMIN_USER_ID configured - cannot send DM")
            return

        try:
            # Get cookie metadata for timestamps
            metadata = self.storage.get_cookie_metadata()
            first_seen_ts = int(datetime.fromisoformat(metadata['first_seen']).timestamp())
            expiry_ts = first_seen_ts + (30 * 86400)  # 30 days later

            # Calculate days until expiry (AoC cookies last ~30 days)
            days_until_expiry = 30 - age_days

            # Emoji and urgency based on time remaining
            if days_until_expiry <= 2:
                emoji = "🚨"
                urgency = "URGENT"
            elif days_until_expiry <= 7:
                emoji = "⚠️"
                urgency = "Warning"
            else:
                emoji = "ℹ️"
                urgency = "Reminder"

            # Generate fallback text for timestamps
            dt_expiry = datetime.fromtimestamp(expiry_ts, tz=timezone.utc)
            fallback_created = f"{age_days} days ago"
            fallback_expiry_date = dt_expiry.strftime("%b %d, %Y")
            fallback_expiry_relative = f"in {days_until_expiry} days" if days_until_expiry > 0 else "expired"

            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"{emoji} AoC Bot: Session Cookie Age {urgency}"}
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Your AoC session cookie was created <!date^{first_seen_ts}^{{ago}}|{fallback_created}>.\n"
                                f"AoC cookies typically expire after ~30 days.\n\n"
                                f"*Expiry date:* <!date^{expiry_ts}^{{date_short}}|{fallback_expiry_date}> (<!date^{expiry_ts}^{{ago}}|{fallback_expiry_relative}>)"
                    }
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*To renew before it expires:*\n"
                                "1. Log in to https://adventofcode.com\n"
                                "2. Open DevTools (F12) → Application → Cookies\n"
                                "3. Copy the `session` cookie value\n"
                                "4. Update `.env`: `AOC_SESSION_COOKIE=<new value>`\n"
                                "5. Restart the bot"
                    }
                },
                {
                    "type": "context",
                    "elements": [{
                        "type": "mrkdwn",
                        "text": "_This reminder will be sent daily until the cookie is renewed._\n"
                                "_To disable: Set `AOC_COOKIE_AGE_REMINDERS=false` in .env_"
                    }]
                }
            ]

            await self.slack_client.chat_postMessage(
                channel=self.admin_user_id,
                text=f"{emoji} AoC Bot: Cookie age reminder - created {age_days} days ago (expires {fallback_expiry_date})",
                blocks=blocks
            )

            # Update reminder timestamp
            self.storage.update_cookie_reminder_sent()

            logger.info(f"Sent cookie age reminder to admin (age: {age_days} days)")

        except Exception as e:
            logger.error(f"Failed to send age reminder DM: {e}")

    async def notify_channel_using_cache(self, last_fetch_ts: int):
        """
        Post to channel that we're using cached data.

        Args:
            last_fetch_ts: Unix timestamp of last successful fetch
        """
        try:
            admin_mention = f"<@{self.admin_user_id}>" if self.admin_user_id else "the bot admin"

            # Generate fallback text
            age_hours = int((datetime.now().timestamp() - last_fetch_ts) / 3600)
            if age_hours < 1:
                fallback = "less than an hour ago"
            elif age_hours == 1:
                fallback = "1 hour ago"
            else:
                fallback = f"{age_hours} hours ago"

            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "⚠️ Using Cached Leaderboard Data"}
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"The session cookie has expired. Showing last known standings.\n"
                                f"Last updated: <!date^{last_fetch_ts}^{{ago}}|{fallback}>"
                    }
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"New puzzles and scores won't appear until the session cookie is renewed.\n"
                                f"Contact {admin_mention} to update the cookie."
                    }
                }
            ]

            await self.slack_client.chat_postMessage(
                channel=self.channel_id,
                text=f"⚠️ Using cached leaderboard data (last updated {fallback}) - Cookie expired",
                blocks=blocks
            )

            logger.info("Posted cached data warning to channel")

        except Exception as e:
            logger.error(f"Failed to post cache warning to channel: {e}")

    async def notify_admin_cookie_renewed(self):
        """Send DM to admin that cookie has been renewed."""
        if not self.admin_user_id:
            return

        try:
            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "✅ AoC Bot: Session Cookie Renewed"}
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Your AoC session cookie has been renewed. The bot is back online and fetching fresh data!"
                    }
                },
                {
                    "type": "context",
                    "elements": [{
                        "type": "mrkdwn",
                        "text": "Thank you for keeping the bot healthy. 🎄"
                    }]
                }
            ]

            await self.slack_client.chat_postMessage(
                channel=self.admin_user_id,
                text="✅ AoC Bot: Session Cookie Renewed - Bot is back online",
                blocks=blocks
            )

            logger.info("Sent cookie renewal notification to admin")
            self.admin_notified_expired = False

        except Exception as e:
            logger.error(f"Failed to send renewal notification: {e}")

    async def daily_health_check(self):
        """
        Daily health check (runs at 9 AM).

        Checks:
        1. Is cookie valid?
        2. How old is the cookie?
        3. Should we send reminder?
        """
        logger.info("Running daily cookie health check...")

        # Check validity
        is_valid = await self.check_cookie_validity()

        if not is_valid:
            logger.warning("Daily health check: Cookie invalid")
            await self.notify_admin_cookie_expired()
            return

        # Cookie is valid - check age
        age_days = self.get_cookie_age_days()
        logger.info(f"Daily health check: Cookie age = {age_days} days")

        # Send reminder if needed
        if self.should_send_age_reminder():
            await self.notify_admin_cookie_aging(age_days)
