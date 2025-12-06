"""Main entry point for the AoC Slack bot."""
import os
import logging
import asyncio
from dotenv import load_dotenv
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from .storage import Storage
from .aoc_api import AoCAPIClient
from .poller import LeaderboardPoller
from .cookie_monitor import CookieMonitor
from .commands.join import register_join_command
from .commands.leaderboard import register_leaderboard_command

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_env_vars():
    """Validate that all required environment variables are set."""
    required_vars = [
        'SLACK_BOT_TOKEN',
        'SLACK_APP_TOKEN',
        'SLACK_CHANNEL_ID',
        'AOC_SESSION_COOKIE',
        'AOC_LEADERBOARD_ID'
    ]

    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please check your .env file."
        )


async def main():
    """Main application entry point."""
    # Validate environment
    validate_env_vars()

    # Get configuration
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    app_token = os.getenv("SLACK_APP_TOKEN")
    channel_id = os.getenv("SLACK_CHANNEL_ID")
    admin_user_id = os.getenv("ADMIN_USER_ID")
    session_cookie = os.getenv("AOC_SESSION_COOKIE")
    leaderboard_id = os.getenv("AOC_LEADERBOARD_ID")
    year = os.getenv("AOC_YEAR", "2025")

    # Cookie age reminders configuration
    cookie_reminders_enabled = os.getenv("AOC_COOKIE_AGE_REMINDERS", "true").lower() == "true"

    # User-Agent configuration
    user_agent = os.getenv(
        'AOC_USER_AGENT',
        'AoC-Slack-Bot/1.0 (Please configure AOC_USER_AGENT in .env with contact info)'
    )

    # Warn if using default User-Agent
    if 'Please configure' in user_agent:
        logger.warning("⚠️  Using default User-Agent. Please set AOC_USER_AGENT in .env with your contact info!")
        logger.warning("⚠️  Example: AOC_USER_AGENT=AoC-Slack-Bot/1.0 (+https://github.com/user/repo; email@example.com)")

    # Development mode settings
    dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"

    if dev_mode:
        logger.warning("🔧 DEVELOPMENT MODE: Using MOCK data (60s polling interval)")
        logger.warning("🔧 This mode does NOT hit the real AoC API")
        poll_interval = int(os.getenv("DEV_POLL_INTERVAL_SECONDS", "60"))
        use_mock = True
    else:
        # Enforce minimum 15-minute (900s) interval to respect AoC rate limits
        requested_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "1200"))
        poll_interval = max(900, requested_interval)

        if requested_interval < 900:
            logger.warning(
                f"⚠️  Requested poll interval ({requested_interval}s) is below 15-minute minimum. "
                f"Using 900s to respect AoC rate limits."
            )

        use_mock = False
        logger.info(f"Production mode: Polling every {poll_interval}s (min 900s enforced)")

    # Initialize components
    logger.info("Initializing bot components...")

    app = AsyncApp(token=bot_token)

    # Use separate databases for dev/prod to avoid mixing mock and real data
    db_path = "data/aoc_bot_dev.db" if dev_mode else "data/aoc_bot.db"
    storage = Storage(db_path=db_path)
    logger.info(f"Using database: {db_path}")

    api_client = AoCAPIClient(
        session_cookie=session_cookie,
        leaderboard_id=leaderboard_id,
        year=year,
        use_mock=use_mock,
        user_agent=user_agent
    )

    # Register command handlers
    register_join_command(app)
    register_leaderboard_command(app, storage)

    # Initialize cookie monitor (skip in dev mode with mock data)
    cookie_monitor = None
    if not use_mock and admin_user_id:
        cookie_monitor = CookieMonitor(
            session_cookie=session_cookie,
            storage=storage,
            slack_client=app.client,
            admin_user_id=admin_user_id,
            channel_id=channel_id,
            year=year,
            user_agent=user_agent,
            reminders_enabled=cookie_reminders_enabled
        )
        logger.info("Cookie monitoring enabled")
    elif not use_mock and not admin_user_id:
        logger.warning("⚠️  ADMIN_USER_ID not configured - cookie monitoring disabled")

    # Initialize poller
    poller = LeaderboardPoller(
        app=app,
        api_client=api_client,
        storage=storage,
        channel_id=channel_id,
        cookie_monitor=cookie_monitor,
        use_cron=not dev_mode  # Use cron in production, interval in dev
    )

    # Start poller
    poller.start()

    # Start bot in Socket Mode
    handler = AsyncSocketModeHandler(app, app_token)

    logger.info("🎄 AoC Slack Bot is starting...")
    logger.info(f"📊 Monitoring leaderboard: {leaderboard_id} (year {year})")
    logger.info(f"📢 Posting to channel: {channel_id}")
    if dev_mode:
        logger.info(f"⏱️  Poll interval: 60 seconds (DEV_MODE)")
    else:
        logger.info(f"⏱️  Cron schedule: Every 20 minutes (:00, :20, :40)")
    if cookie_monitor:
        logger.info(f"👤 Admin notifications: <@{admin_user_id}>")
        if cookie_reminders_enabled:
            logger.info("📅 Cookie age reminders: Enabled (21+ days)")
        else:
            logger.info("📅 Cookie age reminders: Disabled")

    try:
        await handler.start_async()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        poller.stop()
        storage.close()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        poller.stop()
        storage.close()
        raise


if __name__ == "__main__":
    asyncio.run(main())
