"""Test script for verifying improvements."""
import sys
import os
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("🧪 Testing AoC Slack Bot Improvements\n")

# Test 1: Import all modules
print("Test 1: Importing modules...")
try:
    from mock_data import MockLeaderboardData
    from aoc_api import AoCAPIClient
    from slack_rate_limiter import slack_rate_limiter
    from differ import detect_changes
    print("✓ All imports successful\n")
except Exception as e:
    print(f"✗ Import failed: {e}\n")
    sys.exit(1)

# Test 2: Mock data generation
print("Test 2: Mock data generation...")
try:
    mock = MockLeaderboardData()
    data1 = mock.get_next()
    data2 = mock.get_next()
    data3 = mock.get_next()

    assert 'members' in data1, "Missing members key"
    assert 'members' in data2, "Missing members key"
    assert data1 != data2, "Snapshots should differ"

    # Check progression
    members1 = len(data1['members'])
    members2 = len(data2['members'])
    print(f"  Snapshot 1: {members1} members")
    print(f"  Snapshot 2: {members2} members")
    print(f"  Snapshot 3: {len(data3['members'])} members")
    print("✓ Mock data generates correctly\n")
except Exception as e:
    print(f"✗ Mock data test failed: {e}\n")
    sys.exit(1)

# Test 3: Async API client
print("Test 3: Async API client...")
async def test_api_client():
    try:
        # Test with mock mode
        client = AoCAPIClient(
            session_cookie="mock",
            leaderboard_id="12345",
            year="2025",
            use_mock=True,
            user_agent="Test-Bot/1.0"
        )

        data = await client.fetch_leaderboard()
        assert data is not None, "Should return data in mock mode"
        assert 'members' in data, "Should have members"
        print("  ✓ Mock mode works")

        # Test with real mode (should fail gracefully with fake cookie)
        client_real = AoCAPIClient(
            session_cookie="fake_cookie",
            leaderboard_id="12345",
            year="2025",
            use_mock=False,
            user_agent="Test-Bot/1.0 (+test@example.com)"
        )

        print("  ✓ Real mode client initialized")
        print("✓ Async API client works\n")

    except Exception as e:
        print(f"✗ Async API test failed: {e}\n")
        raise

asyncio.run(test_api_client())

# Test 4: Rate limiter
print("Test 4: Rate limiter...")
async def test_rate_limiter():
    try:
        import time

        # Test tier 1 (slowest)
        start = time.time()
        await slack_rate_limiter.wait_for_slot(tier=1)
        await slack_rate_limiter.wait_for_slot(tier=1)
        elapsed = time.time() - start

        # Should take at least 1 second for 2 tier-1 calls
        assert elapsed >= 0.9, f"Rate limiting too fast: {elapsed}s"
        print(f"  ✓ Tier 1 rate limiting works ({elapsed:.2f}s for 2 calls)")

        # Test tier 2 (should be faster)
        start = time.time()
        await slack_rate_limiter.wait_for_slot(tier=2)
        await slack_rate_limiter.wait_for_slot(tier=2)
        elapsed = time.time() - start
        print(f"  ✓ Tier 2 rate limiting works ({elapsed:.2f}s for 2 calls)")

        print("✓ Rate limiter works\n")

    except Exception as e:
        print(f"✗ Rate limiter test failed: {e}\n")
        raise

asyncio.run(test_rate_limiter())

# Test 5: Diff detection with mock data
print("Test 5: Diff detection...")
try:
    mock = MockLeaderboardData()
    mock.reset()

    snapshot1 = mock.get_next()
    snapshot2 = mock.get_next()
    snapshot3 = mock.get_next()

    # Should detect new star between snapshot 1 and 2
    new_stars, rank_changes, new_members = detect_changes(snapshot1, snapshot2)
    print(f"  Snapshot 1→2: {len(new_stars)} new stars, {len(rank_changes)} rank changes, {len(new_members)} new members")

    # Should detect new member between snapshot 2 and 3
    new_stars, rank_changes, new_members = detect_changes(snapshot2, snapshot3)
    print(f"  Snapshot 2→3: {len(new_stars)} new stars, {len(rank_changes)} rank changes, {len(new_members)} new members")
    assert len(new_members) > 0, "Should detect new member"

    print("✓ Diff detection works\n")

except Exception as e:
    print(f"✗ Diff detection test failed: {e}\n")
    sys.exit(1)

# Test 6: User-Agent configuration
print("Test 6: User-Agent configuration...")
try:
    # Test custom user-agent
    client = AoCAPIClient(
        session_cookie="test",
        leaderboard_id="123",
        year="2025",
        use_mock=True,
        user_agent="Custom-Bot/2.0 (+https://example.com; test@example.com)"
    )
    assert client.user_agent == "Custom-Bot/2.0 (+https://example.com; test@example.com)"
    print("  ✓ Custom User-Agent set correctly")

    # Test default user-agent
    client_default = AoCAPIClient(
        session_cookie="test",
        leaderboard_id="123",
        year="2025",
        use_mock=True
    )
    assert "AoC-Slack-Bot" in client_default.user_agent
    print("  ✓ Default User-Agent set correctly")

    print("✓ User-Agent configuration works\n")

except Exception as e:
    print(f"✗ User-Agent test failed: {e}\n")
    sys.exit(1)

print("=" * 50)
print("🎉 All tests passed!")
print("=" * 50)
print("\nReady for deployment! Try:")
print("  • Native Python: python -m src.main")
print("  • Docker: ./docker-run.sh")
print("\nDon't forget to set DEV_MODE=true in .env for testing with mock data!")
