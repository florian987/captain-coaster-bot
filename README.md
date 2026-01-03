# 🎢 Captain Coaster Discord Bot

A Discord bot for roller coaster enthusiasts featuring image guessing games, scoring, and leaderboards using the Captain Coaster API.

## ✨ Features

- **🎮 Image Guessing Game**: Guess roller coasters and parks from images
- **🏆 Difficulty Levels**: Easy, Medium, Hard with different point values
- **📊 Scoring System**: Track your performance with persistent scores
- **📈 Personal Statistics**: Detailed stats including response times, win rates, and favorite parks
- **🥇 Leaderboards**: Monthly rolling leaderboard with automatic cleanup
- **💡 Progressive Hints**: Letter hints for coaster (60s) and park (90s)
- **⚡ Speed Recognition**: Bonus messages for quick answers
- **🏆 Achievement Badges**: Unlock badges for various milestones
- **🔍 Fuzzy Matching**: Smart answer recognition with hints

## 🚀 Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd captain-coaster-bot
   cp .env.example .env
   ```

2. **Configure environment** (edit `.env`):
   ```env
   BOT_TOKEN=your_discord_bot_token
   CAPTAIN_API_KEY=your_captain_coaster_api_key
   ```

3. **Run with UV**:
   ```bash
   uv run --script bot.py
   ```

### Docker Deployment

1. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Deploy**:
   ```bash
   docker-compose up -d
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f bot
   ```

## 🎯 Commands

- `!game [difficulty]` - Start a guessing game (easy/medium/hard)
- `!score [@user]` - Check player score and detailed statistics
- `!leaderboard [limit]` - View top players (default: 10)

## 🏗️ Architecture

### Simplified Structure
```
├── bot.py              # Main bot with inline dependencies
├── config.py           # Simple environment configuration
├── .env                # Environment variables
├── Dockerfile          # Container configuration
├── docker-compose.yml  # Deployment configuration
└── data/               # SQLite database storage
```

### Technology Stack
- **Python 3.11+** with modern async/await
- **discord.py 2.3+** for Discord integration
- **aiohttp** for Captain Coaster API calls
- **aiosqlite** for lightweight database
- **fuzzywuzzy** for smart answer matching
- **UV** for fast dependency management

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | ✅ | - | Discord bot token |
| `CAPTAIN_API_KEY` | ✅ | - | Captain Coaster API key |
| `CAPTAIN_URL` | ❌ | `https://captaincoaster.com` | API base URL |
| `CAPTAIN_CDN` | ❌ | `https://pictures.captaincoaster.com` | Image CDN URL |
| `DB_PATH` | ❌ | `./data/coasterbot.db` | SQLite database path |
| `DEBUG` | ❌ | `false` | Enable debug logging |

### Game Settings

- **Timeout**: 120 seconds per game
- **Min Match Score**: 80% similarity for correct answers
- **Hint Score**: 60% similarity triggers "Ça chauffe!" hint
- **Leaderboard**: 30-day rolling window
- **Cleanup**: Automatic removal of games older than 35 days

## 🐳 Docker

### Build Locally
```bash
docker build -t captain-coaster-bot .
```

### Multi-platform Build
```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t captain-coaster-bot:latest .
```

### GitHub Container Registry
Images are automatically built and published to `ghcr.io/username/captain-coaster-bot` on:
- Push to `main` branch
- Version tags (`v1.0.0`)

## 📊 Database

### SQLite Schema
```sql
CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER,
    channel_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    difficulty INTEGER,
    park_name TEXT,
    coaster_name TEXT,
    park_solver_id INTEGER,
    coaster_solver_id INTEGER,
    park_solved_at TIMESTAMP,
    coaster_solved_at TIMESTAMP
);
```

### Automatic Maintenance
- **Startup cleanup**: Removes old records on bot start
- **Periodic cleanup**: Every 24 hours automatically
- **Rolling window**: Keeps 35 days of data (30-day leaderboard + 5-day buffer)

## 🎮 Game Mechanics

### Difficulty Levels
- **Easy**: `totalRatings > 100` (1 point)
- **Medium**: `totalRatings 30-100` (2 points)
- **Hard**: `totalRatings < 30` (3 points)

### Scoring
- Points awarded for both park and coaster identification
- Separate solvers can find park and coaster
- Monthly leaderboard with automatic reset

### Answer Recognition
- **Fuzzy matching** with 80% similarity threshold
- **Text normalization** removes accents, punctuation
- **Hints** at 60% similarity ("Ça chauffe!")
