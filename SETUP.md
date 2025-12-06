# Advent of Code Slack Bot - Setup Guide

This guide will walk you through setting up the AoC Slack bot from scratch.

## Prerequisites

- Python 3.8 or higher
- A Slack workspace where you have permission to install apps
- An Advent of Code account with access to a private leaderboard

## Step 1: Create a Slack App

1. Go to https://api.slack.com/apps and click **"Create New App"**
2. Choose **"From scratch"**
3. Enter app name (e.g., "AoC Leaderboard Bot") and select your workspace
4. Click **"Create App"**

## Step 2: Configure Slack App Permissions

### Enable Socket Mode
1. In your app settings, go to **"Socket Mode"** in the left sidebar
2. Toggle **"Enable Socket Mode"** to ON
3. Give your token a name (e.g., "socket-token")
4. Click **"Generate"**
5. **Copy the app-level token** (starts with `xapp-`) - you'll need this later

### Add Bot Token Scopes
1. Go to **"OAuth & Permissions"** in the left sidebar
2. Scroll down to **"Scopes"** → **"Bot Token Scopes"**
3. Add these scopes:
   - `chat:write` - Post messages to channels
   - `commands` - Use slash commands

### Install App to Workspace
1. Scroll to the top of the **"OAuth & Permissions"** page
2. Click **"Install to Workspace"** (or **"Reinstall to Workspace"**)
3. Review permissions and click **"Allow"**
4. **Copy the Bot User OAuth Token** (starts with `xoxb-`) - you'll need this later

## Step 3: Create Slash Commands

1. Go to **"Slash Commands"** in the left sidebar
2. Click **"Create New Command"**

### Create `/leaderboard` command
- **Command**: `/leaderboard`
- **Short Description**: `View the current AoC leaderboard`
- **Usage Hint**: `[stars|score]`
- Click **"Save"**

### Create `/join-info` command
- **Command**: `/join-info`
- **Short Description**: `Get the private leaderboard join code`
- **Usage Hint**: (leave empty)
- Click **"Save"**

## Step 4: Get Your Slack Channel ID

1. Open Slack in your browser or desktop app
2. Navigate to the channel where you want the bot to post updates
3. Click the channel name at the top
4. In the "About" section, scroll down to find the **Channel ID**
5. Copy it (format: `C1234567890`)

## Step 5: Get Your Advent of Code Session Cookie

1. Log in to https://adventofcode.com in your browser
2. Open your browser's Developer Tools (F12 or right-click → Inspect)
3. Go to the **Application** tab (Chrome/Edge) or **Storage** tab (Firefox)
4. Under **Cookies**, select `https://adventofcode.com`
5. Find the cookie named `session`
6. **Copy the value** (a long hexadecimal string)

**Note**: Your session cookie is like a password - keep it secure! Don't commit it to version control.

## Step 6: Set Up the Bot

### Clone or Navigate to the Bot Directory
```bash
cd /path/to/AoC_bot
```

### Create Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Create Environment File
```bash
cp .env.example .env
```

### Edit `.env` File
Open `.env` in a text editor and fill in your values:

```env
# Slack tokens (from Step 2)
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here

# Channel ID (from Step 4)
SLACK_CHANNEL_ID=C1234567890

# AoC credentials (from Step 5)
AOC_SESSION_COOKIE=your_long_session_cookie_here
AOC_LEADERBOARD_ID=5123211
AOC_YEAR=2025

# User-Agent for AoC API (REQUIRED - include your contact info!)
# AoC requires this so they can reach you if your bot misbehaves
AOC_USER_AGENT=AoC-Slack-Bot/1.0 (+https://github.com/youruser/repo; your.email@example.com)

# Polling settings (optional - minimum 900s = 15 min enforced)
POLL_INTERVAL_SECONDS=1200

# Development mode (optional - uses MOCK data, does NOT hit real API)
DEV_MODE=false
DEV_POLL_INTERVAL_SECONDS=60
```

**Important**: Replace all placeholder values with your actual tokens and IDs!

## Step 7: Run the Bot

### Start the Bot
```bash
python -m src.main
```

You should see output like:
```
🎄 AoC Slack Bot is starting...
📊 Monitoring leaderboard: 5123211 (year 2025)
📢 Posting to channel: C1234567890
⏱️  Poll interval: 1200 seconds
Polling AoC leaderboard...
Saved snapshot 1
First snapshot saved, no notifications to send
```

### Test the Commands

In your Slack workspace:
1. Type `/join-info` - You should get an ephemeral message with join instructions
2. Type `/leaderboard` - You should see the current leaderboard (ephemeral)
3. Try `/leaderboard stars` and `/leaderboard score`
4. Test the pagination buttons if you have more than 10 members

## Step 8: Verify Notifications

The bot will:
- Fetch the leaderboard immediately on startup (saves as baseline)
- Poll every 20 minutes for changes
- Post to your channel when changes are detected

To test notifications quickly:
1. Stop the bot (Ctrl+C)
2. Edit `.env` and set `DEV_MODE=true`
3. Restart the bot (it will now poll every 60 seconds)
4. Wait 1-2 minutes for the next poll
5. You should see a notification in your channel!

## Required Slack Scopes

Your app needs these OAuth scopes:
- `chat:write` - To post messages to channels
- `commands` - To register and handle slash commands

**That's it!** No additional scopes needed. Socket Mode handles all incoming events.

## Troubleshooting

### "Missing required environment variables"
- Check that your `.env` file exists and all values are filled in
- Make sure you're in the correct directory
- Verify the `.env` file has no syntax errors

### "Failed to fetch leaderboard"
- Verify your `AOC_SESSION_COOKIE` is correct and not expired
- Check your `AOC_LEADERBOARD_ID` matches your private leaderboard
- Ensure your AoC account has access to the leaderboard

### Slash commands not working
- Make sure you created the commands in Slack (Step 3)
- Verify Socket Mode is enabled (Step 2)
- Check that `SLACK_APP_TOKEN` is correct (starts with `xapp-`)

### Bot not posting to channel
- Verify the bot is invited to the channel (`/invite @BotName`)
- Check that `SLACK_CHANNEL_ID` is correct
- Ensure the bot has `chat:write` scope

### "Token looks invalid"
- Make sure you're using the **Bot Token** (starts with `xoxb-`), not the User Token
- Verify the **App-Level Token** (starts with `xapp-`) is for Socket Mode

## Development Tips

### Testing with Faster Polling
Set `DEV_MODE=true` in `.env` to poll every 60 seconds instead of 20 minutes.

### Viewing Logs
All logs are printed to the console. For production, consider redirecting to a file:
```bash
python -m src.main >> logs/bot.log 2>&1
```

### Database Location
The bot stores data in `data/aoc_bot.db`. To reset:
```bash
rm data/aoc_bot.db
```

The bot will create a fresh database on next startup.

## Running in Production

For production deployment (VPS, server, etc.), consider:
- Using `systemd` or `supervisor` to run the bot as a service
- Setting up log rotation
- Monitoring the process for crashes
- Keeping your session cookie updated (they expire after ~1 month)

See the main README for deployment examples.

## Need Help?

- Check the logs for error messages
- Verify all environment variables are set correctly
- Ensure your session cookie hasn't expired
- Test each slash command individually
- Join the #help channel in your workspace if you have one!
