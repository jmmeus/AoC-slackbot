"""Handler for /leaderboard slash command."""
from slack_bolt import App
import json
import logging
from datetime import datetime
from ..storage import Storage
from ..formatters.leaderboard import build_leaderboard_blocks
from ..slack_rate_limiter import slack_rate_limiter

logger = logging.getLogger(__name__)


def parse_timestamp(fetched_at_raw) -> int:
    """
    Parse timestamp from various formats (string, datetime, int).

    Args:
        fetched_at_raw: Timestamp in various formats from storage

    Returns:
        Unix timestamp as integer
    """
    if isinstance(fetched_at_raw, str):
        # Parse ISO format string from SQLite
        dt = datetime.fromisoformat(fetched_at_raw.replace('Z', '+00:00'))
        return int(dt.timestamp())
    elif hasattr(fetched_at_raw, 'timestamp'):
        # datetime object
        return int(fetched_at_raw.timestamp())
    else:
        # Already an integer timestamp
        return int(fetched_at_raw)


def register_leaderboard_command(app: App, storage: Storage):
    """Register the /leaderboard command and button handlers."""

    @app.command("/leaderboard")
    async def handle_leaderboard_command(ack, command, respond):
        """Handle the /leaderboard slash command."""
        await ack()

        # Parse argument
        arg = command['text'].strip().lower()

        if arg and arg not in ['stars', 'score']:
            await respond({
                "response_type": "ephemeral",
                "text": "❌ Invalid argument. Use `/leaderboard stars` or `/leaderboard score`"
            })
            return

        sort_by = arg if arg else 'stars'  # Default to stars

        # Get latest snapshot
        snapshot = storage.get_latest_snapshot()

        if not snapshot:
            await respond({
                "response_type": "ephemeral",
                "text": "⏳ No leaderboard data available yet. Waiting for first API fetch..."
            })
            return

        # Parse timestamp
        fetched_at_ts = parse_timestamp(snapshot['fetched_at'])

        # Build blocks
        blocks = build_leaderboard_blocks(
            data=snapshot['data'],
            fetched_at_ts=fetched_at_ts,
            sort_by=sort_by,
            page=0
        )

        # Rate limit before responding
        await slack_rate_limiter.wait_for_slot(tier=2)

        await respond({
            "response_type": "ephemeral",
            "text": "Advent of Code Leaderboard",
            "blocks": blocks
        })

    @app.action("switch_sort")
    async def handle_switch_sort(ack, body, respond):
        """Handle sort toggle button click."""
        await ack()

        try:
            # Parse button value
            state = json.loads(body['actions'][0]['value'])
            sort_by = state['sort']
            page = state['page']

            # Get latest snapshot
            snapshot = storage.get_latest_snapshot()

            if not snapshot:
                await respond({
                    "response_type": "ephemeral",
                    "text": "⏳ No leaderboard data available yet."
                })
                return

            # Parse timestamp
            fetched_at_ts = parse_timestamp(snapshot['fetched_at'])

            # Build blocks
            blocks = build_leaderboard_blocks(
                data=snapshot['data'],
                fetched_at_ts=fetched_at_ts,
                sort_by=sort_by,
                page=page
            )

            # Rate limit before responding
            await slack_rate_limiter.wait_for_slot(tier=2)

            # Update message
            await respond({
                "replace_original": True,
                "text": "Advent of Code Leaderboard",
                "blocks": blocks
            })

        except Exception as e:
            logger.error(f"Error handling switch_sort: {e}")
            await respond({
                "response_type": "ephemeral",
                "text": "❌ An error occurred while updating the leaderboard."
            })

    @app.action("next_page")
    async def handle_next_page(ack, body, respond):
        """Handle next page button click."""
        await ack()

        try:
            # Parse button value
            state = json.loads(body['actions'][0]['value'])
            sort_by = state['sort']
            page = state['page']

            # Get latest snapshot
            snapshot = storage.get_latest_snapshot()

            if not snapshot:
                await respond({
                    "response_type": "ephemeral",
                    "text": "⏳ No leaderboard data available yet."
                })
                return

            # Parse timestamp
            fetched_at_ts = parse_timestamp(snapshot['fetched_at'])

            # Build blocks
            blocks = build_leaderboard_blocks(
                data=snapshot['data'],
                fetched_at_ts=fetched_at_ts,
                sort_by=sort_by,
                page=page
            )

            # Rate limit before responding
            await slack_rate_limiter.wait_for_slot(tier=2)

            # Update message
            await respond({
                "replace_original": True,
                "text": "Advent of Code Leaderboard",
                "blocks": blocks
            })

        except Exception as e:
            logger.error(f"Error handling next_page: {e}")
            await respond({
                "response_type": "ephemeral",
                "text": "❌ An error occurred while updating the leaderboard."
            })

    @app.action("prev_page")
    async def handle_prev_page(ack, body, respond):
        """Handle previous page button click."""
        await ack()

        try:
            # Parse button value
            state = json.loads(body['actions'][0]['value'])
            sort_by = state['sort']
            page = state['page']

            # Get latest snapshot
            snapshot = storage.get_latest_snapshot()

            if not snapshot:
                await respond({
                    "response_type": "ephemeral",
                    "text": "⏳ No leaderboard data available yet."
                })
                return

            # Parse timestamp
            fetched_at_ts = parse_timestamp(snapshot['fetched_at'])

            # Build blocks
            blocks = build_leaderboard_blocks(
                data=snapshot['data'],
                fetched_at_ts=fetched_at_ts,
                sort_by=sort_by,
                page=page
            )

            # Rate limit before responding
            await slack_rate_limiter.wait_for_slot(tier=2)

            # Update message
            await respond({
                "replace_original": True,
                "text": "Advent of Code Leaderboard",
                "blocks": blocks
            })

        except Exception as e:
            logger.error(f"Error handling prev_page: {e}")
            await respond({
                "response_type": "ephemeral",
                "text": "❌ An error occurred while updating the leaderboard."
            })
