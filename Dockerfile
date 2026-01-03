FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Copy the Python files
COPY bot.py config.py ./

# Create data directory for SQLite database
RUN mkdir -p data

# UV will read inline dependencies from bot.py and install them automatically
CMD ["uv", "run", "--script", "bot.py"]