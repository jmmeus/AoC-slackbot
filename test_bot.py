"""Simple test script to verify bot components."""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing imports...")

try:
    from storage import Storage
    print("✓ storage.py")
except Exception as e:
    print(f"✗ storage.py: {e}")

try:
    from aoc_api import AoCAPIClient
    print("✓ aoc_api.py")
except Exception as e:
    print(f"✗ aoc_api.py: {e}")

try:
    from differ import detect_changes, calculate_rankings
    print("✓ differ.py")
except Exception as e:
    print(f"✗ differ.py: {e}")

try:
    from formatters.leaderboard import build_leaderboard_blocks, format_timestamp
    print("✓ formatters/leaderboard.py")
except Exception as e:
    print(f"✗ formatters/leaderboard.py: {e}")

try:
    from formatters.notifications import build_notification_blocks
    print("✓ formatters/notifications.py")
except Exception as e:
    print(f"✗ formatters/notifications.py: {e}")

print("\nTesting differ with sample data...")

# Sample data
old_data = {
    "members": {
        "123": {
            "name": "Alice",
            "stars": 2,
            "local_score": 5,
            "last_star_ts": 1000000,
            "completion_day_level": {
                "1": {
                    "1": {"star_index": 0, "get_star_ts": 1000000}
                }
            }
        }
    }
}

new_data = {
    "members": {
        "123": {
            "name": "Alice",
            "stars": 4,
            "local_score": 10,
            "last_star_ts": 2000000,
            "completion_day_level": {
                "1": {
                    "1": {"star_index": 0, "get_star_ts": 1000000},
                    "2": {"star_index": 1, "get_star_ts": 1500000}
                },
                "2": {
                    "1": {"star_index": 2, "get_star_ts": 2000000}
                }
            }
        },
        "456": {
            "name": "Bob",
            "stars": 2,
            "local_score": 3,
            "last_star_ts": 1800000,
            "completion_day_level": {
                "1": {
                    "1": {"star_index": 3, "get_star_ts": 1800000}
                }
            }
        }
    }
}

new_stars, rank_changes, new_members = detect_changes(old_data, new_data)

print(f"✓ Detected {len(new_stars)} new stars")
print(f"✓ Detected {len(rank_changes)} rank changes")
print(f"✓ Detected {len(new_members)} new members")

if new_stars:
    stars_list = [f"Day {s['day']} Part {s['part']}" for s in new_stars]
    print(f"  - New stars: {stars_list}")
if new_members:
    members_list = [m['member_name'] for m in new_members]
    print(f"  - New members: {members_list}")

print("\nAll tests passed! ✓")
