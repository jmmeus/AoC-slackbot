"""Detects changes between leaderboard snapshots."""
from typing import Dict, Any, List, Tuple


def calculate_rankings(members: Dict[str, Any]) -> Dict[str, int]:
    """
    Calculate member rankings based on local_score.

    Args:
        members: Dictionary of member data

    Returns:
        Dictionary mapping member_id to rank (1-indexed)
    """
    # Sort by local_score (desc), then by last_star_ts (asc for tie-breaking)
    sorted_members = sorted(
        members.items(),
        key=lambda x: (-x[1].get('local_score', 0), x[1].get('last_star_ts', 0))
    )

    rankings = {}
    for rank, (member_id, _) in enumerate(sorted_members, start=1):
        rankings[member_id] = rank

    return rankings


def detect_changes(
    old_data: Dict[str, Any],
    new_data: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Detect changes between two leaderboard snapshots.

    Args:
        old_data: Previous leaderboard data
        new_data: Current leaderboard data

    Returns:
        Tuple of (new_stars, rank_changes, new_members)
        - new_stars: List of dicts with member_name, day, part, stars_total
        - rank_changes: List of dicts with member_name, old_rank, new_rank, score
        - new_members: List of dicts with member_name, stars
    """
    old_members = old_data.get('members', {})
    new_members = new_data.get('members', {})

    new_stars = []
    rank_changes = []
    new_members_list = []

    # Detect new members
    for member_id, member_data in new_members.items():
        if member_id not in old_members:
            new_members_list.append({
                'member_name': member_data.get('name') or f"(anonymous user #{member_id})",
                'stars': member_data.get('stars', 0)
            })

    # Detect new stars
    for member_id, new_member_data in new_members.items():
        if member_id not in old_members:
            # Skip new members - we already reported them
            continue

        old_member_data = old_members[member_id]
        new_completion = new_member_data.get('completion_day_level', {})
        old_completion = old_member_data.get('completion_day_level', {})

        member_name = new_member_data.get('name') or f"(anonymous user #{member_id})"
        stars_total = new_member_data.get('stars', 0)

        # Check each day and part
        for day, parts in new_completion.items():
            for part, part_data in parts.items():
                # Check if this star is new
                if day not in old_completion or part not in old_completion[day]:
                    new_stars.append({
                        'member_name': member_name,
                        'day': int(day),
                        'part': int(part),
                        'stars_total': stars_total,
                        'star_index': part_data.get('star_index', 0)
                    })

    # Sort new stars by star_index (chronological order)
    new_stars.sort(key=lambda x: x['star_index'])

    # Detect ranking changes
    old_rankings = calculate_rankings(old_members)
    new_rankings = calculate_rankings(new_members)

    for member_id, new_rank in new_rankings.items():
        if member_id in old_rankings:
            old_rank = old_rankings[member_id]
            if old_rank != new_rank:
                member_name = new_members[member_id].get('name') or f"(anonymous user #{member_id})"
                score = new_members[member_id].get('local_score', 0)

                rank_changes.append({
                    'member_name': member_name,
                    'old_rank': old_rank,
                    'new_rank': new_rank,
                    'score': score
                })

    return new_stars, rank_changes, new_members_list
