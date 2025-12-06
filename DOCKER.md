# Docker Deployment Guide

Deploy the AoC Slack Bot using Docker for consistent, isolated execution.

## Quick Start

### 1. Configure Environment
```bash
cp .env.example .env
# Edit .env with your actual tokens and credentials
```

### 2. Run with Helper Script
```bash
./docker-run.sh
```

That's it! The bot is now running in the background.

---

## Manual Docker Commands

### Build and Start
```bash
docker-compose build
docker-compose up -d
```

### View Logs
```bash
# Follow logs in real-time
docker-compose logs -f

# View last 50 lines
docker-compose logs --tail=50

# View logs for last hour
docker-compose logs --since=1h
```

### Stop Bot
```bash
docker-compose down
```

### Restart Bot
```bash
docker-compose restart
```

### Check Status
```bash
docker-compose ps
```

### Rebuild After Code Changes
```bash
docker-compose up -d --build
```

### Shell Access (Debugging)
```bash
docker-compose exec aoc-bot bash
```

---

## Data Persistence

The SQLite database is stored in the `./data/` directory, which is mounted as a Docker volume.

### Reset Database
```bash
docker-compose down
rm -rf data/
docker-compose up -d
```

The bot will create a fresh database on startup.

### Backup Database
```bash
cp data/aoc_bot.db data/aoc_bot.db.backup
```

### Restore Database
```bash
docker-compose down
cp data/aoc_bot.db.backup data/aoc_bot.db
docker-compose up -d
```

---

## VPS Deployment

### Requirements
- Docker and Docker Compose installed
- SSH access to VPS
- Open ports: None (Socket Mode doesn't require inbound ports!)

### Step-by-Step Deployment

#### 1. Install Docker on VPS
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

#### 2. Clone Repository
```bash
ssh user@your-vps-ip
git clone https://github.com/youruser/aoc-slack-bot.git
cd aoc-slack-bot
```

#### 3. Configure
```bash
cp .env.example .env
nano .env  # or vim, emacs, etc.
```

Fill in your actual values:
- `SLACK_BOT_TOKEN`
- `SLACK_APP_TOKEN`
- `SLACK_CHANNEL_ID`
- `AOC_SESSION_COOKIE`
- `AOC_LEADERBOARD_CODE`
- `AOC_USER_AGENT` (important - include contact info!)

#### 4. Start Bot
```bash
./docker-run.sh
```

#### 5. Enable Auto-Start on Reboot
```bash
# Docker Compose will auto-restart containers with restart: unless-stopped
# But also ensure Docker starts on boot:
sudo systemctl enable docker
```

#### 6. Verify It's Running
```bash
docker-compose ps
docker-compose logs --tail=20
```

---

## Cloud Platform Deployment

### Railway.app

1. **Connect Repository**
   - Go to [railway.app](https://railway.app)
   - "New Project" → "Deploy from GitHub"
   - Select your repository

2. **Add Environment Variables**
   - Go to "Variables" tab
   - Add all variables from `.env.example`
   - Click "Deploy"

3. **Done!**
   - Railway auto-detects the Dockerfile
   - Bot deploys automatically

### Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch app
fly launch

# Set environment variables
fly secrets set SLACK_BOT_TOKEN=xoxb-...
fly secrets set SLACK_APP_TOKEN=xapp-...
fly secrets set SLACK_CHANNEL_ID=C...
fly secrets set AOC_SESSION_COOKIE=...
fly secrets set AOC_LEADERBOARD_CODE=5123211-abc123fg
fly secrets set AOC_USER_AGENT="AoC-Slack-Bot/1.0 (+https://your-contact)"

# Deploy
fly deploy
```

### Render.com

1. **Create Web Service**
   - Go to [render.com](https://render.com)
   - "New" → "Web Service"
   - Connect repository

2. **Configure**
   - Environment: Docker
   - Add environment variables
   - Deploy

---

## Development with Docker

### Development Mode
```bash
# In .env
DEV_MODE=true

# Rebuild and restart
docker-compose up -d --build
docker-compose logs -f
```

This uses mock data and polls every 60 seconds.

### Mount Local Code (Live Reload)
Edit `docker-compose.yml`:
```yaml
volumes:
  - ./data:/app/data
  - ./src:/app/src  # Add this line
```

Then:
```bash
docker-compose up -d --build
# Now code changes are reflected immediately
```

---

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs

# Common issues:
# 1. Missing .env file → Create it from .env.example
# 2. Invalid tokens → Check Slack app settings
# 3. Port conflicts → Stop other containers
```

### Database Locked Error
```bash
# SQLite doesn't handle multiple connections well
# Ensure only one container is running:
docker-compose down
docker-compose up -d
```

### Out of Disk Space
```bash
# Clean up old Docker images/containers
docker system prune -a

# Check disk usage
docker system df
```

### Can't Connect to Docker Daemon
```bash
# Ensure Docker is running
sudo systemctl start docker

# Check if you're in docker group
groups

# If not, add yourself:
sudo usermod -aG docker $USER
# Then log out and back in
```

### Health Check Failing
```bash
# View health status
docker inspect aoc-slack-bot | grep -A 10 Health

# Check if Python is working
docker-compose exec aoc-bot python --version
```

---

## Resource Usage

### Expected Resource Consumption
- **Memory**: 50-100 MB
- **CPU**: <1% (idle), 5-10% (during polls)
- **Disk**: ~50 MB image + <1 MB database
- **Network**: Minimal (a few KB every 20 minutes)

### Monitor Resources
```bash
# Real-time stats
docker stats aoc-slack-bot

# Check container resource limits
docker inspect aoc-slack-bot | grep -A 10 Resources
```

### Set Resource Limits (Optional)
Edit `docker-compose.yml`:
```yaml
services:
  aoc-bot:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          memory: 64M
```

---

## Security Best Practices

### 1. Never Commit .env
Already in `.gitignore`, but double-check:
```bash
git status
# Should NOT show .env
```

### 2. Use Secrets Management (Production)
Instead of `.env` file on server:
```bash
# Use environment variables
docker run -e SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN ...

# Or Docker secrets (Swarm mode)
echo "$SLACK_BOT_TOKEN" | docker secret create slack_bot_token -
```

### 3. Keep Docker Updated
```bash
# Update Docker
sudo apt-get update && sudo apt-get upgrade docker-ce

# Rebuild bot image
docker-compose build --pull
docker-compose up -d
```

### 4. Rotate Session Cookie
AoC session cookies expire after ~1 month. Update when needed:
```bash
# Edit .env with new cookie
nano .env

# Restart bot
docker-compose restart
```

---

## Updating the Bot

### Pull Latest Code
```bash
cd aoc-slack-bot
git pull origin main
docker-compose up -d --build
```

### Rolling Back
```bash
# Find previous image
docker images

# Or revert git commit
git log --oneline
git checkout <previous-commit>
docker-compose up -d --build
```

---

## Logs and Monitoring

### Log Rotation
Configured in `docker-compose.yml`:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"  # Max 10 MB per file
    max-file: "3"     # Keep 3 files (30 MB total)
```

### External Log Management
```bash
# Ship logs to external service (e.g., Papertrail)
docker-compose logs -f | nc logs.papertrailapp.com 12345
```

### Health Monitoring
```bash
# Check if container is healthy
docker inspect aoc-slack-bot --format='{{.State.Health.Status}}'

# Set up alerts (example with curl)
if [ "$(docker inspect aoc-slack-bot --format='{{.State.Health.Status}}')" != "healthy" ]; then
    curl -X POST https://your-webhook-url -d "Bot is unhealthy!"
fi
```

---

## Advanced Configuration

### Custom Network
```yaml
networks:
  aoc-network:
    driver: bridge

services:
  aoc-bot:
    networks:
      - aoc-network
```

### Multiple Bots (Different Leaderboards)
```bash
# Create separate directories
cp -r aoc-slack-bot aoc-slack-bot-team2
cd aoc-slack-bot-team2

# Edit .env with different leaderboard
nano .env

# Use different container name
# Edit docker-compose.yml: container_name: aoc-slack-bot-team2

# Start
docker-compose up -d
```

---

## FAQ

**Q: Do I need to expose any ports?**
A: No! Socket Mode doesn't require inbound ports. Perfect for restrictive networks.

**Q: Can I run multiple instances?**
A: Yes, use different directories and container names for each leaderboard.

**Q: How do I update dependencies?**
A: Edit `requirements.txt`, then `docker-compose up -d --build`.

**Q: Can I use podman instead of Docker?**
A: Yes! Replace `docker` with `podman` and `docker-compose` with `podman-compose`.

**Q: Where are logs stored?**
A: In Docker's log driver. View with `docker-compose logs`.

---

## Support

- **Issues**: https://github.com/youruser/aoc-slack-bot/issues
- **Docs**: See README.md and SETUP.md
- **Slack**: Check logs with `docker-compose logs -f`

Happy Advent of Code! 🎄🎅
