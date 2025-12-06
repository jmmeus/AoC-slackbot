#!/bin/bash
# Quick start script for Docker deployment

set -e

echo "🎄 AoC Slack Bot - Docker Quick Start"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Copying .env.example to .env..."
    cp .env.example .env
    echo ""
    echo "✏️  Please edit .env with your tokens and credentials:"
    echo "   - SLACK_BOT_TOKEN"
    echo "   - SLACK_APP_TOKEN"
    echo "   - SLACK_CHANNEL_ID"
    echo "   - AOC_SESSION_COOKIE"
    echo "   - AOC_LEADERBOARD_CODE"
    echo "   - AOC_USER_AGENT (include your contact info!)"
    echo ""
    echo "Then run this script again: ./docker-run.sh"
    exit 1
fi

# Build Docker image
echo "🐳 Building Docker image..."
docker-compose build

echo ""
echo "🚀 Starting AoC Slack Bot..."
docker-compose up -d

echo ""
echo "✅ Bot started successfully!"
echo ""
echo "📊 Status:"
docker-compose ps

echo ""
echo "💡 Useful commands:"
echo "   View logs:    docker-compose logs -f"
echo "   Stop bot:     docker-compose down"
echo "   Restart bot:  docker-compose restart"
echo "   Check status: docker-compose ps"
echo ""
echo "🎄 Happy Advent of Code! 🎅"
