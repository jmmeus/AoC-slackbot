# Advent of Code Slack Bot

A Slack bot that monitors your private Advent of Code leaderboard and posts updates to a channel.

## Features

- **Automatic updates**: Polls AoC API every 20 minutes and posts changes
- **Leaderboard command**: `/leaderboard [stars|score]` - View current standings (ephemeral)
- **Join command**: `/join-info` - Get instructions to join the private leaderboard
- **Interactive UI**: Switch between star and score views, paginate through members
- **Smart notifications**: Detects new stars, rank changes, and new members
- **Persistent storage**: SQLite database survives restarts
- **Rate limiting**: Respects both AoC (15-min minimum) and Slack API limits
- **Development mode**: Test with mock data without hitting real API
- **Docker support**: One-command deployment with Docker Compose

## Quick Start

### Docker (Recommended)
```bash
# Configure
cp .env.example .env
# Edit .env with your tokens

# Run
./docker-run.sh
```

See **[DOCKER.md](DOCKER.md)** for full Docker documentation.

### Native Python

See **[SETUP.md](SETUP.md)** for detailed setup instructions.

**Requirements:**
- Python 3.8+
- Slack workspace admin access
- Advent of Code account with private leaderboard access

**Installation:**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your tokens and IDs

# Run the bot
python -m src.main
```

## Commands

- `/leaderboard` or `/leaderboard stars` - View leaderboard sorted by stars
- `/leaderboard score` - View leaderboard sorted by local score
- `/join-info` - Get the private leaderboard join code

## Local Score Explanation

The local score is calculated by AoC based on completion order:
- First person to complete a star: N points (N = number of members)
- Second person: N-1 points
- Third person: N-2 points
- And so on...

Each star (part 1 and part 2 of each day) is scored independently.
