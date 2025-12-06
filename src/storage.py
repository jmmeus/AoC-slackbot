"""Storage layer for leaderboard data using SQLite."""
import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any
import os


class Storage:
    """Handles all database operations for the AoC bot."""

    def __init__(self, db_path: str = "data/aoc_bot.db"):
        """Initialize storage and create tables if needed."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Store snapshots of the leaderboard
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data TEXT NOT NULL
            )
        """)

        # Store individual member star completions for easier querying
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS member_stars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                member_id TEXT NOT NULL,
                member_name TEXT,
                day INTEGER NOT NULL,
                part INTEGER NOT NULL,
                star_index INTEGER NOT NULL,
                completed_at TIMESTAMP NOT NULL,
                FOREIGN KEY (snapshot_id) REFERENCES leaderboard_snapshots(id)
            )
        """)

        # Index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_member_stars_snapshot
            ON member_stars(snapshot_id)
        """)

        # Store cookie metadata for age tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cookie_metadata (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                cookie_hash TEXT NOT NULL,
                first_seen TIMESTAMP NOT NULL,
                last_verified TIMESTAMP,
                last_reminder_sent TIMESTAMP
            )
        """)

        self.conn.commit()

    def save_snapshot(self, data: Dict[str, Any]) -> int:
        """
        Save a leaderboard snapshot.

        Args:
            data: Raw leaderboard data from AoC API

        Returns:
            The snapshot ID
        """
        cursor = self.conn.cursor()

        # Save snapshot
        cursor.execute(
            "INSERT INTO leaderboard_snapshots (raw_data) VALUES (?)",
            (json.dumps(data),)
        )
        snapshot_id = cursor.lastrowid

        # Extract and save individual star completions
        members = data.get('members', {})
        for member_id, member_data in members.items():
            member_name = member_data.get('name', 'Unknown')
            completion_days = member_data.get('completion_day_level', {})

            for day, parts in completion_days.items():
                for part, part_data in parts.items():
                    star_index = part_data.get('star_index')
                    completed_ts = part_data.get('get_star_ts')

                    if star_index is not None and completed_ts is not None:
                        cursor.execute("""
                            INSERT INTO member_stars
                            (snapshot_id, member_id, member_name, day, part, star_index, completed_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            snapshot_id,
                            member_id,
                            member_name,
                            int(day),
                            int(part),
                            star_index,
                            datetime.fromtimestamp(completed_ts)
                        ))

        self.conn.commit()
        return snapshot_id

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent leaderboard snapshot.

        Returns:
            Dictionary with 'id', 'fetched_at', and 'data' keys, or None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, fetched_at, raw_data
            FROM leaderboard_snapshots
            ORDER BY id DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        if row:
            return {
                'id': row['id'],
                'fetched_at': row['fetched_at'],
                'data': json.loads(row['raw_data'])
            }
        return None

    def get_previous_snapshot(self, current_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the snapshot before the given ID.

        Args:
            current_id: The current snapshot ID

        Returns:
            Dictionary with 'id', 'fetched_at', and 'data' keys, or None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, fetched_at, raw_data
            FROM leaderboard_snapshots
            WHERE id < ?
            ORDER BY id DESC
            LIMIT 1
        """, (current_id,))

        row = cursor.fetchone()
        if row:
            return {
                'id': row['id'],
                'fetched_at': row['fetched_at'],
                'data': json.loads(row['raw_data'])
            }
        return None

    def get_cookie_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Get current cookie metadata.

        Returns:
            Dictionary with cookie_hash, first_seen, last_verified, last_reminder_sent
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT cookie_hash, first_seen, last_verified, last_reminder_sent
            FROM cookie_metadata
            WHERE id = 1
        """)

        row = cursor.fetchone()
        if row:
            return {
                'cookie_hash': row['cookie_hash'],
                'first_seen': datetime.fromisoformat(row['first_seen']) if row['first_seen'] else None,
                'last_verified': datetime.fromisoformat(row['last_verified']) if row['last_verified'] else None,
                'last_reminder_sent': datetime.fromisoformat(row['last_reminder_sent']) if row['last_reminder_sent'] else None
            }
        return None

    def upsert_cookie_metadata(self, cookie_hash: str, first_seen: datetime):
        """
        Insert or update cookie metadata.

        Args:
            cookie_hash: SHA256 hash of session cookie
            first_seen: When this cookie was first seen
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO cookie_metadata (id, cookie_hash, first_seen, last_verified)
            VALUES (1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                cookie_hash = excluded.cookie_hash,
                first_seen = excluded.first_seen,
                last_verified = excluded.last_verified
        """, (cookie_hash, first_seen.isoformat(), datetime.now().isoformat()))
        self.conn.commit()

    def update_cookie_last_verified(self):
        """Update last verified timestamp for current cookie."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE cookie_metadata
            SET last_verified = ?
            WHERE id = 1
        """, (datetime.now().isoformat(),))
        self.conn.commit()

    def update_cookie_reminder_sent(self):
        """Update last reminder sent timestamp."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE cookie_metadata
            SET last_reminder_sent = ?
            WHERE id = 1
        """, (datetime.now().isoformat(),))
        self.conn.commit()

    def close(self):
        """Close database connection."""
        self.conn.close()
