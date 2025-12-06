"""Formats leaderboard data for Slack display."""
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional


def format_slack_timestamp(ts: int, token_string: str) -> str:
    """
    Format Unix timestamp using Slack's dynamic date syntax.

    Args:
        ts: Unix timestamp
        token_string: Slack token string (e.g., "{date_short} at {time} ({ago})")

    Returns:
        Slack-formatted date string with fallback

    Example:
        >>> format_slack_timestamp(1733419200, "{date_short} at {time} ({ago})")
        "<!date^1733419200^{date_short} at {time} ({ago})|Dec 5 at 14:30 UTC (2 hours ago)>"
    """
    # Generate fallback matching current format
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = now - dt

    # Calculate relative time for fallback
    if delta.total_seconds() < 60:
        relative = "just now"
    elif delta.total_seconds() < 3600:
        minutes = int(delta.total_seconds() / 60)
        relative = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif delta.total_seconds() < 86400:
        hours = int(delta.total_seconds() / 3600)
        relative = f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(delta.total_seconds() / 86400)
        relative = f"{days} day{'s' if days != 1 else ''} ago"

    # Build fallback based on token_string
    if "{date_short} at {time} ({ago})" in token_string:
        absolute = dt.strftime("%b %d at %H:%M UTC")
        fallback = f"{absolute} ({relative})"
    elif token_string == "{ago}":
        fallback = relative
    elif token_string == "{date_short}":
        fallback = dt.strftime("%b %d, %Y")
    else:
        # Generic fallback
        fallback = dt.strftime("%b %d, %Y at %I:%M %p UTC")

    # Return Slack formatted string
    return f"<!date^{ts}^{token_string}|{fallback}>"


def format_timestamp(ts: int) -> str:
    """
    DEPRECATED: Use format_slack_timestamp() instead.

    Legacy function for backward compatibility.
    Format a Unix timestamp as 'Dec 5 at 14:30 UTC (2 hours ago)'.

    Args:
        ts: Unix timestamp

    Returns:
        Formatted timestamp string
    """
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = now - dt

    # Format absolute time
    absolute = dt.strftime("%b %d at %H:%M UTC")

    # Format relative time
    if delta.total_seconds() < 60:
        relative = "just now"
    elif delta.total_seconds() < 3600:
        minutes = int(delta.total_seconds() / 60)
        relative = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif delta.total_seconds() < 86400:
        hours = int(delta.total_seconds() / 3600)
        relative = f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(delta.total_seconds() / 86400)
        relative = f"{days} day{'s' if days != 1 else ''} ago"

    return f"{absolute} ({relative})"


def get_medal_emoji(position: int) -> str:
    """Get medal emoji for top 3 positions."""
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    return medals.get(position, "  ")


def sort_members(members: Dict[str, Any], sort_by: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Sort members by stars or score.

    Args:
        members: Dictionary of member data from AoC API
        sort_by: 'stars' or 'score'

    Returns:
        List of (member_id, member_data) tuples, sorted
    """
    member_list = list(members.items())

    if sort_by == "stars":
        # Sort by stars (desc), then by last_star_ts (asc for tie-breaking)
        member_list.sort(
            key=lambda x: (-x[1].get('stars', 0), x[1].get('last_star_ts', 0))
        )
    else:  # score
        # Sort by local_score (desc), then by last_star_ts (asc)
        member_list.sort(
            key=lambda x: (-x[1].get('local_score', 0), x[1].get('last_star_ts', 0))
        )

    return member_list


def build_leaderboard_blocks(
    data: Dict[str, Any],
    fetched_at_ts: int,
    sort_by: str = "stars",
    page: int = 0,
    per_page: int = 10,
    is_cached: bool = False,
    admin_user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Build Slack Block Kit blocks for the leaderboard.

    Args:
        data: Leaderboard data from AoC API
        fetched_at_ts: Unix timestamp when data was fetched
        sort_by: 'stars' or 'score'
        page: Current page number (0-indexed)
        per_page: Members per page
        is_cached: Whether showing cached data
        admin_user_id: Admin user ID for cached data warnings

    Returns:
        List of Slack blocks
    """
    members = data.get('members', {})

    if not members:
        return [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🎄 Advent of Code 2025 - Private Leaderboard"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "_No data available yet. Waiting for first API fetch..._"}
            }
        ]

    # Sort members
    sorted_members = sort_members(members, sort_by)
    total_members = len(sorted_members)

    # Paginate
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, total_members)
    page_members = sorted_members[start_idx:end_idx]

    # Build blocks
    blocks = []

    # Header
    if is_cached:
        header_text = "🎄 Advent of Code 2025 - Private Leaderboard (Cached)"
    else:
        header_text = "🎄 Advent of Code 2025 - Private Leaderboard"

    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": header_text}
    })

    # Add warning banner if using cached data
    if is_cached:
        admin_mention = f"<@{admin_user_id}>" if admin_user_id else "the bot admin"
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"⚠️ *Session cookie expired - showing cached data*\n"
                        f"Contact {admin_mention} to renew the cookie."
            }
        })

    # Sort indicator
    sort_label = "⭐ Total Stars" if sort_by == "stars" else "🏆 Local Score"
    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"*Sorted by: {sort_label}*"}
    })

    # Score explanation (only for score view)
    if sort_by == "score":
        num_members = len(members)
        blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"ℹ️ *Local Score:* Points per star based on completion order. "
                        f"1st: {num_members} pts, 2nd: {num_members-1} pts, 3rd: {num_members-2} pts, etc."
            }]
        })

    blocks.append({"type": "divider"})

    # Member list
    for idx, (member_id, member_data) in enumerate(page_members, start=start_idx + 1):
        name = member_data.get('name') or f"(anonymous user #{member_id})"
        stars = member_data.get('stars', 0)
        score = member_data.get('local_score', 0)
        last_star_ts = member_data.get('last_star_ts', 0)

        medal = get_medal_emoji(idx)

        if sort_by == "stars":
            primary = f"{stars}⭐"
            secondary = f"({score} pts)"
        else:
            primary = f"{score} pts"
            secondary = f"({stars}⭐)"

        # Format last star timestamp using Slack dynamic format
        if last_star_ts > 0:
            timestamp_str = format_slack_timestamp(last_star_ts, "{date_short} at {time} ({ago})")
            last_star_info = f"\n    └─ Last star: {timestamp_str}"
        else:
            last_star_info = ""

        member_text = f"{medal} *{idx}.* *{name}* - {primary} {secondary}{last_star_info}"

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": member_text}
        })

    blocks.append({"type": "divider"})

    # Footer with pagination info and last updated
    last_updated_str = format_slack_timestamp(fetched_at_ts, "{date_short} at {time} ({ago})")
    blocks.append({
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": f"Showing {start_idx + 1}-{end_idx} of {total_members} members  •  Last updated: {last_updated_str}"
        }]
    })

    # Action buttons
    is_first_page = page == 0
    is_last_page = end_idx >= total_members

    buttons = []

    # Sort toggle button
    new_sort = "stars" if sort_by == "score" else "score"
    sort_button_text = "Sort by ⭐ Stars" if sort_by == "score" else "Sort by 🏆 Score"
    buttons.append({
        "type": "button",
        "text": {"type": "plain_text", "text": sort_button_text},
        "action_id": "switch_sort",
        "value": json.dumps({"sort": new_sort, "page": 0})
    })

    # Previous button
    if not is_first_page:
        buttons.append({
            "type": "button",
            "text": {"type": "plain_text", "text": "← Prev"},
            "action_id": "prev_page",
            "value": json.dumps({"sort": sort_by, "page": page - 1})
        })

    # Next button
    if not is_last_page:
        buttons.append({
            "type": "button",
            "text": {"type": "plain_text", "text": "Next →"},
            "action_id": "next_page",
            "value": json.dumps({"sort": sort_by, "page": page + 1})
        })

    if buttons:
        blocks.append({
            "type": "actions",
            "elements": buttons
        })

    return blocks
