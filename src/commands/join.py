"""Handler for /join-info slash command."""
from slack_bolt import App
import os


def register_join_command(app: App):
    """Register the /join-info command handler."""

    @app.command("/join-info")
    async def handle_join_command(ack, command, respond):
        """Handle the /join-info slash command."""
        await ack()

        leaderboard_id = os.getenv("AOC_LEADERBOARD_ID", "unknown")
        year = os.getenv("AOC_YEAR", "2025")

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🎄 Join Our Advent of Code {year} Leaderboard!"}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Join our private leaderboard and compete with the team!\n\n"
                            f"*Steps to join:*\n"
                            f"1. Go to <https://adventofcode.com/{year}/leaderboard/private|Advent of Code Private Leaderboards>\n"
                            f"2. Enter this code: `{leaderboard_id}`\n"
                            f"3. Start solving puzzles! 🎅"
                }
            },
            {
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": "💡 Use `/leaderboard` to check current standings"
                }]
            }
        ]

        await respond({
            "response_type": "ephemeral",
            "text": f"Join our Advent of Code {year} leaderboard! Code: {leaderboard_id}",
            "blocks": blocks
        })
