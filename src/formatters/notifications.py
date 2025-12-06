"""Formats change notifications for Slack channel posts."""
from typing import List, Dict, Any


def format_star_notification(star: Dict[str, Any]) -> str:
    """
    Format a single star completion.

    Args:
        star: Dictionary with 'member_name', 'day', 'part', 'stars_total'

    Returns:
        Formatted string
    """
    name = star['member_name']
    day = star['day']
    part = star['part']
    stars_total = star['stars_total']

    part_text = "⭐" if part == 1 else "⭐⭐"
    return f"• *{name}* completed Day {day} Part {part} {part_text} (now has {stars_total}⭐ total)"


def format_rank_change(change: Dict[str, Any]) -> str:
    """
    Format a ranking change.

    Args:
        change: Dictionary with 'member_name', 'old_rank', 'new_rank', 'score'

    Returns:
        Formatted string
    """
    name = change['member_name']
    old_rank = change['old_rank']
    new_rank = change['new_rank']
    score = change['score']

    if new_rank < old_rank:
        emoji = "📈"
        direction = f"moved up from #{old_rank} to #{new_rank}"
    else:
        emoji = "📉"
        direction = f"moved down from #{old_rank} to #{new_rank}"

    return f"• {emoji} *{name}* {direction} ({score} pts)"


def format_new_member(member: Dict[str, Any]) -> str:
    """
    Format a new member joining.

    Args:
        member: Dictionary with 'member_name', 'stars'

    Returns:
        Formatted string
    """
    name = member['member_name']
    stars = member.get('stars', 0)
    return f"• 👋 *{name}* joined the leaderboard ({stars}⭐)"


def build_notification_blocks(
    new_stars: List[Dict[str, Any]],
    rank_changes: List[Dict[str, Any]],
    new_members: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Build Slack blocks for a combined notification message.

    Args:
        new_stars: List of new star completions
        rank_changes: List of ranking changes
        new_members: List of new members

    Returns:
        List of Slack blocks
    """
    blocks = []

    # Header
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": "🎄 Advent of Code Leaderboard Update"}
    })

    # New stars section
    if new_stars:
        stars_text = "*New Stars Earned:* ⭐\n" + "\n".join(
            format_star_notification(star) for star in new_stars
        )
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": stars_text}
        })

    # Rank changes section
    if rank_changes:
        if new_stars:
            blocks.append({"type": "divider"})

        ranks_text = "*Ranking Changes:*\n" + "\n".join(
            format_rank_change(change) for change in rank_changes
        )
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": ranks_text}
        })

    # New members section
    if new_members:
        if new_stars or rank_changes:
            blocks.append({"type": "divider"})

        members_text = "*New Members:*\n" + "\n".join(
            format_new_member(member) for member in new_members
        )
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": members_text}
        })

    # Footer
    blocks.append({
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": "Use `/leaderboard` to view current standings"
        }]
    })

    return blocks
