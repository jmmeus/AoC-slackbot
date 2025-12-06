"""Test script for new features: cron scheduling and cookie monitoring."""
import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🧪 Testing New Features\n")

# Test 1: Cookie tracking in storage
print("Test 1: Cookie tracking in storage...")
try:
    from storage import Storage
    import tempfile

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    storage = Storage(db_path)

    # Test cookie metadata insertion
    cookie_hash = "test_hash_123"
    first_seen = datetime.now()
    storage.upsert_cookie_metadata(cookie_hash, first_seen)

    # Retrieve and verify
    metadata = storage.get_cookie_metadata()
    assert metadata is not None, "Cookie metadata should exist"
    assert metadata['cookie_hash'] == cookie_hash, "Cookie hash should match"
    print(f"  ✓ Cookie tracking works (hash: {cookie_hash[:8]}...)")

    # Test update
    storage.update_cookie_reminder_sent()
    metadata = storage.get_cookie_metadata()
    assert metadata['last_reminder_sent'] is not None, "Reminder timestamp should be set"
    print("  ✓ Reminder timestamp update works")

    # Cleanup
    storage.close()
    os.unlink(db_path)

    print("✓ Cookie tracking in storage works\n")
except Exception as e:
    print(f"✗ Cookie tracking test failed: {e}\n")
    sys.exit(1)

# Test 2: CookieMonitor initialization and age calculation
print("Test 2: Cookie monitor age calculation...")
try:
    from cookie_monitor import CookieMonitor
    from storage import Storage
    from unittest.mock import MagicMock
    import hashlib

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    storage = Storage(db_path)

    # Mock Slack client
    mock_slack = MagicMock()

    # Create cookie monitor
    monitor = CookieMonitor(
        session_cookie="test_cookie",
        storage=storage,
        slack_client=mock_slack,
        admin_user_id="U123456",
        channel_id="C123456",
        year="2025",
        user_agent="Test/1.0",
        reminders_enabled=True
    )

    # Test hash creation
    test_hash = monitor._hash_cookie("test_cookie")
    assert len(test_hash) == 64, "SHA256 hash should be 64 chars"
    print(f"  ✓ Cookie hashing works (hash: {test_hash[:8]}...)")

    # Test age calculation (should be 0 days for new cookie)
    age = monitor.get_cookie_age_days()
    assert age == 0, f"New cookie should be 0 days old, got {age}"
    print(f"  ✓ Cookie age calculation works (age: {age} days)")

    # Test should_send_reminder logic
    should_remind = monitor.should_send_age_reminder()
    assert not should_remind, "Should not remind for new cookie"
    print("  ✓ Reminder logic works (no reminder for new cookie)")

    # Manually set cookie to 22 days old
    old_date = datetime.now() - timedelta(days=22)
    storage.upsert_cookie_metadata(test_hash, old_date)

    # Re-create monitor to pick up old date
    monitor2 = CookieMonitor(
        session_cookie="test_cookie",
        storage=storage,
        slack_client=mock_slack,
        admin_user_id="U123456",
        channel_id="C123456",
        reminders_enabled=True
    )

    age2 = monitor2.get_cookie_age_days()
    assert age2 >= 21, f"Old cookie should be 21+ days, got {age2}"
    print(f"  ✓ Old cookie detection works (age: {age2} days)")

    should_remind2 = monitor2.should_send_age_reminder()
    assert should_remind2, "Should remind for old cookie"
    print("  ✓ Reminder logic works (reminder for old cookie)")

    # Cleanup
    storage.close()
    os.unlink(db_path)

    print("✓ Cookie monitor works\n")
except Exception as e:
    print(f"✗ Cookie monitor test failed: {e}\n")
    sys.exit(1)

# Test 3: Cron trigger import and structure
print("Test 3: Cron scheduling support...")
try:
    from apscheduler.triggers.cron import CronTrigger

    # Create cron trigger
    trigger = CronTrigger(minute='0,20,40')
    print("  ✓ CronTrigger imported successfully")

    # Verify trigger would fire at correct times
    now = datetime.now()
    # Get next fire time
    next_fire = trigger.get_next_fire_time(None, now)
    assert next_fire is not None, "Trigger should have next fire time"

    # Verify it's at :00, :20, or :40
    minute = next_fire.minute
    assert minute in [0, 20, 40], f"Should fire at :00, :20, or :40, got :{minute}"
    print(f"  ✓ Cron trigger configured correctly (next: :{minute:02d})")

    print("✓ Cron scheduling support works\n")
except Exception as e:
    print(f"✗ Cron scheduling test failed: {e}\n")
    sys.exit(1)

# Test 4: Leaderboard cached warning
print("Test 4: Leaderboard cached warning...")
try:
    from formatters.leaderboard import build_leaderboard_blocks

    # Sample data
    test_data = {
        'members': {
            '123': {
                'name': 'Test User',
                'stars': 5,
                'local_score': 10,
                'last_star_ts': 1700000000,
                'completion_day_level': {}
            }
        }
    }

    # Test normal mode
    blocks_normal = build_leaderboard_blocks(
        data=test_data,
        fetched_at="Dec 5 at 14:00 UTC (just now)",
        sort_by="stars",
        is_cached=False
    )

    # Header should not say "Cached"
    header_text = blocks_normal[0]['text']['text']
    assert "(Cached)" not in header_text, "Normal mode should not show cached"
    print("  ✓ Normal leaderboard doesn't show cached warning")

    # Test cached mode
    blocks_cached = build_leaderboard_blocks(
        data=test_data,
        fetched_at="Dec 5 at 14:00 UTC (2 hours ago)",
        sort_by="stars",
        is_cached=True,
        admin_user_id="U123456"
    )

    # Header should say "Cached"
    header_cached = blocks_cached[0]['text']['text']
    assert "(Cached)" in header_cached, "Cached mode should show cached in header"
    print("  ✓ Cached leaderboard shows warning in header")

    # Should have warning block
    assert len(blocks_cached) > len(blocks_normal), "Cached should have extra warning block"

    # Find warning block
    warning_found = False
    for block in blocks_cached:
        if block.get('type') == 'section':
            text = block.get('text', {}).get('text', '')
            if '⚠️' in text and 'cookie expired' in text.lower():
                warning_found = True
                break

    assert warning_found, "Should have cookie expiry warning"
    print("  ✓ Cached leaderboard shows cookie warning")

    print("✓ Leaderboard cached warning works\n")
except Exception as e:
    print(f"✗ Leaderboard cached warning test failed: {e}\n")
    sys.exit(1)

# Test 5: Async cookie validation (mock test)
print("Test 5: Async cookie validation...")
async def test_cookie_validation():
    try:
        from cookie_monitor import CookieMonitor
        from storage import Storage
        from unittest.mock import MagicMock, AsyncMock

        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        storage = Storage(db_path)

        # Mock Slack client
        mock_slack = MagicMock()

        # Create cookie monitor
        monitor = CookieMonitor(
            session_cookie="invalid_cookie",
            storage=storage,
            slack_client=mock_slack,
            admin_user_id="U123456",
            channel_id="C123456",
            reminders_enabled=False
        )

        # Test validation (will fail with invalid cookie, but should not crash)
        is_valid = await monitor.check_cookie_validity()
        assert isinstance(is_valid, bool), "Validation should return boolean"
        print(f"  ✓ Cookie validation runs (result: {is_valid})")

        # Cleanup
        storage.close()
        os.unlink(db_path)

        print("✓ Async cookie validation works\n")
    except Exception as e:
        print(f"✗ Async validation test failed: {e}\n")
        raise

asyncio.run(test_cookie_validation())

print("=" * 50)
print("🎉 All new feature tests passed!")
print("=" * 50)
print("\nNew features verified:")
print("  ✓ Cookie metadata storage")
print("  ✓ Cookie age tracking")
print("  ✓ Cookie monitor initialization")
print("  ✓ Cron scheduling support")
print("  ✓ Leaderboard cached warnings")
print("  ✓ Async cookie validation")
print("\n📝 Next steps:")
print("  1. Configure ADMIN_USER_ID in .env")
print("  2. Test with real Slack workspace")
print("  3. Verify cron schedule (:00, :20, :40)")
print("  4. Monitor cookie age warnings")
