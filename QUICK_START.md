# Quick Start Checklist

## What You Need to Do

### 1. Create Slack App (5 minutes)
Go to https://api.slack.com/apps
- Create new app "From scratch"
- Enable **Socket Mode** → Copy `xapp-` token
- Add scopes: `chat:write`, `commands`
- Install to workspace → Copy `xoxb-` token
- Create slash commands: `/leaderboard` and `/join-info`

### 2. Get Tokens & IDs (5 minutes)
- **Channel ID**: Right-click channel → View channel details → Copy ID
- **Session Cookie**: Login to adventofcode.com → F12 → Application/Storage → Cookies → Copy `session` value
- **Leaderboard ID**: Your private leaderboard ID

### 3. Install & Configure (2 minutes)
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your tokens
```

### 4. Run It!
```bash
python -m src.main
```

## Your .env File Should Look Like:
```env
SLACK_BOT_TOKEN=xoxb-123456...
SLACK_APP_TOKEN=xapp-123456...
SLACK_CHANNEL_ID=C1234567890
AOC_SESSION_COOKIE=53616c7465645f5f...
AOC_LEADERBOARD_ID=5123213
AOC_YEAR=2025
POLL_INTERVAL_SECONDS=1200
```

## Test It Works
1. In Slack: Type `/join-info` → Should show join instructions
2. In Slack: Type `/leaderboard` → Should show current standings
3. Watch console logs → Should see "Polling AoC leaderboard..."

## Need More Details?
See **SETUP.md** for the complete step-by-step guide with screenshots and troubleshooting.
