"""Mock data for development and testing."""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MockLeaderboardData:
    """
    Generates realistic mock leaderboard data with incremental changes.

    Cycles through 5 snapshots to simulate real-world changes:
    1. Initial state with 2 members
    2. Alice completes a new star
    3. Bob joins the leaderboard
    4. Alice gets another star (rank change)
    5. Multiple members complete stars
    """

    def __init__(self):
        self.state = 0
        self.snapshots = self._generate_snapshots()
        logger.info(f"Mock data initialized with {len(self.snapshots)} snapshots")

    def get_next(self) -> Dict[str, Any]:
        """Get next snapshot in the cycle."""
        data = self.snapshots[self.state % len(self.snapshots)]
        logger.info(f"Mock data: Returning snapshot {self.state % len(self.snapshots) + 1}/{len(self.snapshots)}")
        self.state += 1
        return data

    def reset(self):
        """Reset to first snapshot."""
        self.state = 0

    def _generate_snapshots(self):
        """Generate 5 snapshots showing progression."""

        # Snapshot 0: Initial state - Alice and Charlie with some progress
        snapshot_0 = {
            "event": "2025",
            "owner_id": 5123211,
            "day1_ts": 1764565200,
            "num_days": 12,
            "members": {
                "100001": {
                    "id": 100001,
                    "name": "Alice",
                    "stars": 6,
                    "local_score": 12,
                    "last_star_ts": 1764720000,
                    "completion_day_level": {
                        "1": {
                            "1": {"star_index": 0, "get_star_ts": 1764670000},
                            "2": {"star_index": 1, "get_star_ts": 1764675000}
                        },
                        "2": {
                            "1": {"star_index": 2, "get_star_ts": 1764690000},
                            "2": {"star_index": 3, "get_star_ts": 1764695000}
                        },
                        "3": {
                            "1": {"star_index": 4, "get_star_ts": 1764710000},
                            "2": {"star_index": 5, "get_star_ts": 1764720000}
                        }
                    }
                },
                "100002": {
                    "id": 100002,
                    "name": "Charlie",
                    "stars": 4,
                    "local_score": 7,
                    "last_star_ts": 1764700000,
                    "completion_day_level": {
                        "1": {
                            "1": {"star_index": 6, "get_star_ts": 1764680000},
                            "2": {"star_index": 7, "get_star_ts": 1764685000}
                        },
                        "2": {
                            "1": {"star_index": 8, "get_star_ts": 1764695000},
                            "2": {"star_index": 9, "get_star_ts": 1764700000}
                        }
                    }
                }
            }
        }

        # Snapshot 1: Alice completes Day 4 Part 1
        snapshot_1 = {
            "event": "2025",
            "owner_id": 5123211,
            "day1_ts": 1764565200,
            "num_days": 12,
            "members": {
                "100001": {
                    "id": 100001,
                    "name": "Alice",
                    "stars": 7,
                    "local_score": 14,
                    "last_star_ts": 1764730000,
                    "completion_day_level": {
                        "1": {
                            "1": {"star_index": 0, "get_star_ts": 1764670000},
                            "2": {"star_index": 1, "get_star_ts": 1764675000}
                        },
                        "2": {
                            "1": {"star_index": 2, "get_star_ts": 1764690000},
                            "2": {"star_index": 3, "get_star_ts": 1764695000}
                        },
                        "3": {
                            "1": {"star_index": 4, "get_star_ts": 1764710000},
                            "2": {"star_index": 5, "get_star_ts": 1764720000}
                        },
                        "4": {
                            "1": {"star_index": 10, "get_star_ts": 1764730000}
                        }
                    }
                },
                "100002": {
                    "id": 100002,
                    "name": "Charlie",
                    "stars": 4,
                    "local_score": 7,
                    "last_star_ts": 1764700000,
                    "completion_day_level": {
                        "1": {
                            "1": {"star_index": 6, "get_star_ts": 1764680000},
                            "2": {"star_index": 7, "get_star_ts": 1764685000}
                        },
                        "2": {
                            "1": {"star_index": 8, "get_star_ts": 1764695000},
                            "2": {"star_index": 9, "get_star_ts": 1764700000}
                        }
                    }
                }
            }
        }

        # Snapshot 2: Bob joins the leaderboard with Day 1 Part 1
        snapshot_2 = {
            "event": "2025",
            "owner_id": 5123211,
            "day1_ts": 1764565200,
            "num_days": 12,
            "members": {
                "100001": {
                    "id": 100001,
                    "name": "Alice",
                    "stars": 7,
                    "local_score": 17,  # Score adjusted with 3 members
                    "last_star_ts": 1764730000,
                    "completion_day_level": {
                        "1": {
                            "1": {"star_index": 0, "get_star_ts": 1764670000},
                            "2": {"star_index": 1, "get_star_ts": 1764675000}
                        },
                        "2": {
                            "1": {"star_index": 2, "get_star_ts": 1764690000},
                            "2": {"star_index": 3, "get_star_ts": 1764695000}
                        },
                        "3": {
                            "1": {"star_index": 4, "get_star_ts": 1764710000},
                            "2": {"star_index": 5, "get_star_ts": 1764720000}
                        },
                        "4": {
                            "1": {"star_index": 10, "get_star_ts": 1764730000}
                        }
                    }
                },
                "100002": {
                    "id": 100002,
                    "name": "Charlie",
                    "stars": 4,
                    "local_score": 9,
                    "last_star_ts": 1764700000,
                    "completion_day_level": {
                        "1": {
                            "1": {"star_index": 6, "get_star_ts": 1764680000},
                            "2": {"star_index": 7, "get_star_ts": 1764685000}
                        },
                        "2": {
                            "1": {"star_index": 8, "get_star_ts": 1764695000},
                            "2": {"star_index": 9, "get_star_ts": 1764700000}
                        }
                    }
                },
                "100003": {
                    "id": 100003,
                    "name": "Bob",
                    "stars": 1,
                    "local_score": 3,
                    "last_star_ts": 1764740000,
                    "completion_day_level": {
                        "1": {
                            "1": {"star_index": 11, "get_star_ts": 1764740000}
                        }
                    }
                }
            }
        }

        # Snapshot 3: Alice completes Day 4 Part 2 (increases lead)
        snapshot_3 = {
            "event": "2025",
            "owner_id": 5123211,
            "day1_ts": 1764565200,
            "num_days": 12,
            "members": {
                "100001": {
                    "id": 100001,
                    "name": "Alice",
                    "stars": 8,
                    "local_score": 20,
                    "last_star_ts": 1764750000,
                    "completion_day_level": {
                        "1": {
                            "1": {"star_index": 0, "get_star_ts": 1764670000},
                            "2": {"star_index": 1, "get_star_ts": 1764675000}
                        },
                        "2": {
                            "1": {"star_index": 2, "get_star_ts": 1764690000},
                            "2": {"star_index": 3, "get_star_ts": 1764695000}
                        },
                        "3": {
                            "1": {"star_index": 4, "get_star_ts": 1764710000},
                            "2": {"star_index": 5, "get_star_ts": 1764720000}
                        },
                        "4": {
                            "1": {"star_index": 10, "get_star_ts": 1764730000},
                            "2": {"star_index": 12, "get_star_ts": 1764750000}
                        }
                    }
                },
                "100002": {
                    "id": 100002,
                    "name": "Charlie",
                    "stars": 4,
                    "local_score": 9,
                    "last_star_ts": 1764700000,
                    "completion_day_level": {
                        "1": {
                            "1": {"star_index": 6, "get_star_ts": 1764680000},
                            "2": {"star_index": 7, "get_star_ts": 1764685000}
                        },
                        "2": {
                            "1": {"star_index": 8, "get_star_ts": 1764695000},
                            "2": {"star_index": 9, "get_star_ts": 1764700000}
                        }
                    }
                },
                "100003": {
                    "id": 100003,
                    "name": "Bob",
                    "stars": 1,
                    "local_score": 3,
                    "last_star_ts": 1764740000,
                    "completion_day_level": {
                        "1": {
                            "1": {"star_index": 11, "get_star_ts": 1764740000}
                        }
                    }
                }
            }
        }

        # Snapshot 4: Multiple changes - Bob completes Day 1 Part 2, Charlie starts Day 3
        snapshot_4 = {
            "event": "2025",
            "owner_id": 5123211,
            "day1_ts": 1764565200,
            "num_days": 12,
            "members": {
                "100001": {
                    "id": 100001,
                    "name": "Alice",
                    "stars": 8,
                    "local_score": 20,
                    "last_star_ts": 1764750000,
                    "completion_day_level": {
                        "1": {
                            "1": {"star_index": 0, "get_star_ts": 1764670000},
                            "2": {"star_index": 1, "get_star_ts": 1764675000}
                        },
                        "2": {
                            "1": {"star_index": 2, "get_star_ts": 1764690000},
                            "2": {"star_index": 3, "get_star_ts": 1764695000}
                        },
                        "3": {
                            "1": {"star_index": 4, "get_star_ts": 1764710000},
                            "2": {"star_index": 5, "get_star_ts": 1764720000}
                        },
                        "4": {
                            "1": {"star_index": 10, "get_star_ts": 1764730000},
                            "2": {"star_index": 12, "get_star_ts": 1764750000}
                        }
                    }
                },
                "100002": {
                    "id": 100002,
                    "name": "Charlie",
                    "stars": 5,
                    "local_score": 11,
                    "last_star_ts": 1764760000,
                    "completion_day_level": {
                        "1": {
                            "1": {"star_index": 6, "get_star_ts": 1764680000},
                            "2": {"star_index": 7, "get_star_ts": 1764685000}
                        },
                        "2": {
                            "1": {"star_index": 8, "get_star_ts": 1764695000},
                            "2": {"star_index": 9, "get_star_ts": 1764700000}
                        },
                        "3": {
                            "1": {"star_index": 13, "get_star_ts": 1764760000}
                        }
                    }
                },
                "100003": {
                    "id": 100003,
                    "name": "Bob",
                    "stars": 2,
                    "local_score": 5,
                    "last_star_ts": 1764755000,
                    "completion_day_level": {
                        "1": {
                            "1": {"star_index": 11, "get_star_ts": 1764740000},
                            "2": {"star_index": 14, "get_star_ts": 1764755000}
                        }
                    }
                }
            }
        }

        return [snapshot_0, snapshot_1, snapshot_2, snapshot_3, snapshot_4]
