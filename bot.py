#!/usr/bin/env python3
# /// script
# dependencies = [
#     "discord.py>=2.3.0",
#     "aiohttp>=3.9.0",
#     "aiosqlite>=0.19.0",
#     "fuzzywuzzy>=0.18.0",
#     "unidecode>=1.3.0",
# ]
# ///
"""
Captain Coaster Discord Bot - Simplified Version
Image guessing game with scoring and leaderboards.
"""

import asyncio
import aiosqlite
import aiohttp
import discord
import logging
import os
import random
import re
import time
from datetime import datetime
from discord.ext import commands
from fuzzywuzzy import fuzz
from pathlib import Path
from unidecode import unidecode

import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

# Enable debug logging for development
if os.getenv('DEBUG', '').lower() in ('true', '1', 'yes'):
    logging.getLogger().setLevel(logging.DEBUG)
    log.setLevel(logging.DEBUG)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global variables
games_in_progress = set()

class CoasterBot:
    def __init__(self):
        self.db_path = config.DB_PATH
        self.headers = {'Authorization': config.CAPTAIN_API_KEY}
        
    async def init_database(self):
        """Initialize SQLite database with game tables"""
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Create table with all columns
            await db.execute('''
                CREATE TABLE IF NOT EXISTS games (
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
                    coaster_solved_at TIMESTAMP,
                    park_response_time REAL,
                    coaster_response_time REAL
                )
            ''')
            
            # Create index for faster cleanup queries
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_games_created_at ON games(created_at)
            ''')
            
            await db.commit()
            
            # Clean up old records (older than 35 days to keep some buffer)
            await self.cleanup_old_games(db)
            
            log.info("Database initialized")

    async def cleanup_old_games(self, db=None):
        """Remove game records older than 35 days to keep database lean"""
        should_close = db is None
        if db is None:
            db = await aiosqlite.connect(self.db_path)
        
        try:
            # Delete games older than 35 days (5 days buffer beyond leaderboard period)
            cursor = await db.execute('''
                DELETE FROM games 
                WHERE created_at < datetime('now', '-35 days')
            ''')
            
            deleted_count = cursor.rowcount
            await db.commit()
            
            if deleted_count > 0:
                log.info(f"Cleaned up {deleted_count} old game records")
            else:
                log.debug("No old game records to clean up")
                
        finally:
            if should_close:
                await db.close()

    async def get_coaster_data(self, difficulty='easy'):
        """Fetch random coaster data from Captain Coaster API"""
        difficulty_filter = config.DIFFICULTY_LEVELS[difficulty]['filter']
        url = f"{config.CAPTAIN_URL}/api/coasters?totalRatings{difficulty_filter}&mainImage[exists]=true"
        
        log.info(f"Fetching coasters from: {url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    response_text = await response.text()
                    log.error(f"API request failed: {response.status} - {response_text}")
                    raise Exception(f"API request failed: {response.status}")
                
                data = await response.json()
                log.debug(f"API Response keys: {list(data.keys())}")
                
                # Check if this is a Hydra API response
                if "hydra:member" in data:
                    coasters = data["hydra:member"]
                    view_key = "hydra:view"
                    last_key = "hydra:last"
                elif "member" in data:
                    # Captain Coaster API format
                    coasters = data["member"]
                    view_key = "view"
                    last_key = "last"
                # Handle different API response formats
                elif isinstance(data, list):
                    # Direct array response
                    coasters = data
                elif "data" in data:
                    # Wrapped in data key
                    coasters = data["data"]
                else:
                    log.error(f"Unexpected API response format. Keys: {list(data.keys())}")
                    log.error(f"Response sample: {str(data)[:500]}...")
                    raise Exception(f"Unexpected API response format. Available keys: {list(data.keys())}")
                
                # Get random page if multiple pages exist
                if view_key in data and last_key in data[view_key]:
                    last_page = int(data[view_key][last_key].split('=')[-1])
                    page = random.randint(1, last_page)
                    
                    # Fetch random page
                    page_url = f"{url}&page={page}"
                    log.info(f"Fetching random page: {page_url}")
                    async with session.get(page_url, headers=self.headers) as page_response:
                        if page_response.status != 200:
                            log.error(f"Page request failed: {page_response.status}")
                            # Fall back to first page
                        else:
                            page_data = await page_response.json()
                            if "member" in page_data:
                                coasters = page_data["member"]
                            elif "hydra:member" in page_data:
                                coasters = page_data["hydra:member"]
                
                if not coasters:
                    raise Exception("No coasters found for this difficulty")
                
                log.info(f"Found {len(coasters)} coasters")
                
                # Select random coaster
                coaster = random.choice(coasters)
                log.info(f"Selected coaster: {coaster.get('name', 'Unknown')} at {coaster.get('park', {}).get('name', 'Unknown park')}")
                
                # Debug: Log the park data structure to see what fields are available
                if 'park' in coaster:
                    log.debug(f"Park data structure: {coaster['park']}")
                
                # Get coaster images
                images_url = f"{config.CAPTAIN_URL}/api/images?coaster={coaster['id']}"
                log.info(f"Fetching images from: {images_url}")
                
                async with session.get(images_url, headers=self.headers) as img_response:
                    if img_response.status != 200:
                        log.error(f"Images request failed: {img_response.status}")
                        raise Exception(f"Failed to fetch images: {img_response.status}")
                    
                    img_data = await img_response.json()
                    log.debug(f"Images API Response keys: {list(img_data.keys())}")
                    
                    # Handle different image response formats
                    if "hydra:member" in img_data:
                        images = img_data["hydra:member"]
                    elif "member" in img_data:
                        images = img_data["member"]
                    elif isinstance(img_data, list):
                        images = img_data
                    elif "data" in img_data:
                        images = img_data["data"]
                    else:
                        log.error(f"Unexpected images response format: {list(img_data.keys())}")
                        raise Exception("Unexpected images response format")
                    
                    if not images:
                        raise Exception("No images found for this coaster")
                    
                    log.debug(f"First image object keys: {list(images[0].keys()) if images else 'No images'}")
                    
                    # Handle different image object formats
                    random_image_obj = random.choice(images)
                    if "path" in random_image_obj:
                        random_image = random_image_obj["path"]
                    elif "url" in random_image_obj:
                        random_image = random_image_obj["url"]
                    elif "filename" in random_image_obj:
                        random_image = random_image_obj["filename"]
                    elif "src" in random_image_obj:
                        random_image = random_image_obj["src"]
                    else:
                        log.error(f"Image object keys: {list(random_image_obj.keys())}")
                        log.error(f"Image object sample: {random_image_obj}")
                        raise Exception(f"Unknown image object format. Keys: {list(random_image_obj.keys())}")
                    
                    log.info(f"Selected image: {random_image}")
                    
                return {
                        'coaster': coaster,
                        'image_path': random_image
                    }

    def normalize_text(self, text):
        """Normalize text for fuzzy matching"""
        return re.sub(r"\(.*?\)", "", unidecode(text.lower().strip().replace("'", "").replace("-", "").replace(":", "")))

    def create_letter_hint(self, text):
        """Create a letter hint like 'F____ R____' with correct letter count"""
        words = text.split()
        hint_words = []
        
        for word in words:
            if len(word) == 1:
                # Single letters get one underscore
                hint_words.append("_")
            elif len(word) == 2:
                # Two letter words get first letter + underscore
                hint_words.append(word[0] + "_")
            else:
                # Show first letter + correct number of underscores
                hint_words.append(word[0] + "_" * (len(word) - 1))
        
        return " ".join(hint_words)

    def create_embed(self, title, description=None, color=discord.Color.blue(), image_url=None, author=None):
        """Create a Discord embed"""
        embed = discord.Embed(title=title, description=description, color=color)
        
        if image_url:
            embed.set_image(url=image_url)
            
        if author:
            embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)
            
        return embed

    async def send_hint(self, ctx, coaster, hint_type, game_time):
        """Send different types of hints based on game progress"""
        if hint_type == "letters_coaster":
            coaster_hint = self.create_letter_hint(coaster['name'])
            embed = self.create_embed(
                title="🎢 Indice Coaster", 
                description=f"Le coaster: **{coaster_hint}**",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            
        elif hint_type == "letters_park":
            park_hint = self.create_letter_hint(coaster['park']['name'])
            embed = self.create_embed(
                title="🏰 Indice Parc",
                description=f"Le parc: **{park_hint}**",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    async def save_game_result(self, game_data, solver_type, solver_id, response_time=None):
        """Save game result to database with response time"""
        async with aiosqlite.connect(self.db_path) as db:
            if solver_type == 'park':
                await db.execute('''
                    UPDATE games 
                    SET park_solver_id = ?, park_solved_at = CURRENT_TIMESTAMP, park_response_time = ?
                    WHERE id = ?
                ''', (solver_id, response_time, game_data['game_id']))
            else:  # coaster
                await db.execute('''
                    UPDATE games 
                    SET coaster_solver_id = ?, coaster_solved_at = CURRENT_TIMESTAMP, coaster_response_time = ?
                    WHERE id = ?
                ''', (solver_id, response_time, game_data['game_id']))
            await db.commit()

    async def get_player_stats(self, user_id):
        """Get comprehensive stats for a player"""
        async with aiosqlite.connect(self.db_path) as db:
            # Basic game stats
            cursor = await db.execute('''
                SELECT 
                    COUNT(*) as total_games,
                    COUNT(CASE WHEN park_solver_id = ? OR coaster_solver_id = ? THEN 1 END) as games_won,
                    COUNT(CASE WHEN park_solver_id = ? THEN 1 END) as parks_found,
                    COUNT(CASE WHEN coaster_solver_id = ? THEN 1 END) as coasters_found,
                    SUM(CASE WHEN park_solver_id = ? THEN difficulty ELSE 0 END) + 
                    SUM(CASE WHEN coaster_solver_id = ? THEN difficulty ELSE 0 END) as total_points,
                    AVG(CASE WHEN park_solver_id = ? THEN park_response_time END) as avg_park_time,
                    AVG(CASE WHEN coaster_solver_id = ? THEN coaster_response_time END) as avg_coaster_time,
                    MIN(CASE WHEN park_solver_id = ? THEN park_response_time END) as fastest_park,
                    MIN(CASE WHEN coaster_solver_id = ? THEN coaster_response_time END) as fastest_coaster
                FROM games 
                WHERE created_at > datetime('now', '-30 days')
                AND (park_solver_id = ? OR coaster_solver_id = ? OR 
                     (park_solver_id IS NULL AND coaster_solver_id IS NULL))
            ''', (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))
            
            basic_stats = await cursor.fetchone()
            
            # Difficulty breakdown - only show user's actual participation
            cursor = await db.execute('''
                SELECT 
                    difficulty,
                    COUNT(*) as wins
                FROM games 
                WHERE created_at > datetime('now', '-30 days')
                AND (park_solver_id = ? OR coaster_solver_id = ?)
                GROUP BY difficulty
            ''', (user_id, user_id))
            
            difficulty_stats = await cursor.fetchall()
            
            # Most successful parks/countries
            cursor = await db.execute('''
                SELECT park_name, COUNT(*) as wins
                FROM games 
                WHERE (park_solver_id = ? OR coaster_solver_id = ?)
                AND created_at > datetime('now', '-30 days')
                GROUP BY park_name
                ORDER BY wins DESC
                LIMIT 3
            ''', (user_id, user_id))
            
            favorite_parks = await cursor.fetchall()
            
            return {
                'basic': basic_stats,
                'difficulty': difficulty_stats,
                'parks': favorite_parks
            }

    async def get_player_score(self, user_id):
        """Get total score for a player"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get points from park solutions
            park_cursor = await db.execute('''
                SELECT SUM(difficulty) FROM games 
                WHERE park_solver_id = ? AND park_solved_at IS NOT NULL
            ''', (user_id,))
            park_points = (await park_cursor.fetchone())[0] or 0
            
            # Get points from coaster solutions
            coaster_cursor = await db.execute('''
                SELECT SUM(difficulty) FROM games 
                WHERE coaster_solver_id = ? AND coaster_solved_at IS NOT NULL
            ''', (user_id,))
            coaster_points = (await coaster_cursor.fetchone())[0] or 0
            
            return park_points + coaster_points

    async def get_leaderboard(self, limit=10):
        """Get leaderboard data"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT 
                    COALESCE(park_solver_id, coaster_solver_id) as user_id,
                    SUM(difficulty) as total_score
                FROM (
                    SELECT park_solver_id, NULL as coaster_solver_id, difficulty 
                    FROM games 
                    WHERE park_solver_id IS NOT NULL 
                      AND park_solved_at > datetime('now', '-30 days')
                    
                    UNION ALL
                    
                    SELECT NULL as park_solver_id, coaster_solver_id, difficulty 
                    FROM games 
                    WHERE coaster_solver_id IS NOT NULL 
                      AND coaster_solved_at > datetime('now', '-30 days')
                ) combined
                WHERE COALESCE(park_solver_id, coaster_solver_id) IS NOT NULL
                GROUP BY COALESCE(park_solver_id, coaster_solver_id)
                ORDER BY total_score DESC
                LIMIT ?
            ''', (limit,))
            
            return await cursor.fetchall()

# Initialize bot instance
coaster_bot = CoasterBot()

@bot.event
async def on_ready():
    """Bot startup event"""
    await coaster_bot.init_database()
    
    # Start periodic cleanup task
    bot.loop.create_task(periodic_cleanup())
    
    log.info(f'{bot.user} has connected to Discord!')
    log.info(f'Bot is in {len(bot.guilds)} guilds')

async def periodic_cleanup():
    """Run database cleanup every 24 hours"""
    import asyncio
    
    while True:
        try:
            # Wait 24 hours
            await asyncio.sleep(24 * 60 * 60)  # 24 hours in seconds
            
            log.info("Running periodic database cleanup...")
            await coaster_bot.cleanup_old_games()
            
        except Exception as e:
            log.error(f"Error in periodic cleanup: {e}")
            # Continue the loop even if cleanup fails
            await asyncio.sleep(60 * 60)  # Wait 1 hour before retrying

@bot.command(name='game', aliases=['play', 'jeu'])
async def play_game(ctx, difficulty=None):
    """Start a coaster guessing game"""
    # If no difficulty specified, choose random
    if difficulty is None:
        difficulty = random.choice(list(config.DIFFICULTY_LEVELS.keys()))
        log.info(f"No difficulty specified, randomly selected: {difficulty}")
    
    # Validate difficulty
    if difficulty not in config.DIFFICULTY_LEVELS:
        await ctx.send(f"Difficulté invalide. Utilisez: {', '.join(config.DIFFICULTY_LEVELS.keys())}")
        return
    
    # Check if game already in progress in this channel
    if ctx.channel.id in games_in_progress:
        await ctx.send("Une partie est déjà en cours dans ce canal!")
        return
    
    try:
        # Add channel to games in progress
        games_in_progress.add(ctx.channel.id)
        
        # Get coaster data
        game_data = await coaster_bot.get_coaster_data(difficulty)
        coaster = game_data['coaster']
        image_url = f"{config.CAPTAIN_CDN}/1440x1440/{game_data['image_path']}"
        
        # Create game record in database
        async with aiosqlite.connect(coaster_bot.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO games (guild_id, channel_id, difficulty, park_name, coaster_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                ctx.guild.id if ctx.guild else None,
                ctx.channel.id,
                config.DIFFICULTY_LEVELS[difficulty]['points'],
                coaster['park']['name'],
                coaster['name']
            ))
            game_id = cursor.lastrowid
            await db.commit()
        
        # Create game embed
        embed = coaster_bot.create_embed(
            title=f"De quel coaster et quel parc s'agit-il ? ({difficulty})",
            color=discord.Color.gold(),
            image_url=image_url,
            author=ctx.author
        )
        
        log.info(f"Game embed image URL: {image_url}")
        
        question_msg = await ctx.send(embed=embed)
        
        # Game state
        park_found = False
        coaster_found = False
        game_start_time = time.time()
        hints_given = set()  # Track which hints have been given
        
        log.info(f"Game started by {ctx.author} in {ctx.channel}. Coaster: {coaster['name']}, Park: {coaster['park']['name']}")
        
        # Game loop
        while not (park_found and coaster_found):
            try:
                def check(m):
                    return m.channel == ctx.channel
                
                # Check if it's time for hints
                current_time = time.time()
                elapsed_time = current_time - game_start_time
                
                log.debug(f"Game elapsed time: {elapsed_time:.1f}s")
                
                # Progressive hints system - coaster first, then park
                if elapsed_time >= 60 and not coaster_found and "letters_coaster" not in hints_given:
                    log.info(f"Sending coaster hint at {elapsed_time:.1f}s")
                    hints_given.add("letters_coaster")
                    await coaster_bot.send_hint(ctx, coaster, "letters_coaster", elapsed_time)
                
                if elapsed_time >= 90 and not park_found and "letters_park" not in hints_given:
                    log.info(f"Sending park hint at {elapsed_time:.1f}s")
                    hints_given.add("letters_park")
                    await coaster_bot.send_hint(ctx, coaster, "letters_park", elapsed_time)
                
                log.debug(f"Waiting for messages in channel {ctx.channel.id}")
                
                # Calculate remaining timeout
                remaining_timeout = max(1, config.GAME_TIMEOUT - elapsed_time)
                
                # Use a shorter timeout to check hints more frequently
                message_timeout = min(10, remaining_timeout)  # Check every 10 seconds or less
                
                try:
                    msg = await bot.wait_for('message', timeout=message_timeout, check=check)
                    log.debug(f"Received message: '{msg.content}' from {msg.author}")
                    
                    # Skip bot's own messages
                    if msg.author == bot.user:
                        continue
                    
                    # Calculate response time
                    response_time = time.time() - game_start_time
                    
                    # Normalize the message content
                    normalized_msg = coaster_bot.normalize_text(msg.content)
                    normalized_park = coaster_bot.normalize_text(coaster['park']['name'])
                    normalized_coaster = coaster_bot.normalize_text(coaster['name'])
                    
                    log.debug(f"Normalized message: '{normalized_msg}'")
                    log.debug(f"Normalized park: '{normalized_park}'")
                    log.debug(f"Normalized coaster: '{normalized_coaster}'")
                    
                    # Check for correct answers
                    park_match = fuzz.ratio(normalized_msg, normalized_park)
                    coaster_match = fuzz.ratio(normalized_msg, normalized_coaster)
                    
                    log.debug(f"Park match score: {park_match}, Coaster match score: {coaster_match}")
                    
                    # Park answer
                    if park_match >= config.MIN_MATCH_SCORE and not park_found:
                        park_found = True
                        await coaster_bot.save_game_result({'game_id': game_id}, 'park', msg.author.id, response_time)
                        
                        # Speed bonus message
                        speed_msg = ""
                        if response_time < 10:
                            speed_msg = " ⚡ Lightning fast!"
                        elif response_time < 30:
                            speed_msg = " 🚀 Quick thinking!"
                        
                        title = f"Bravo {msg.author.display_name}, tu as trouvé le parc!{speed_msg}"
                        if not coaster_found:
                            title += "\nSaurez-vous trouver le coaster ?"
                        
                        embed = coaster_bot.create_embed(title, coaster['park']['name'], discord.Color.green())
                        await ctx.send(embed=embed)
                        
                        # Update question embed
                        embed = question_msg.embeds[0]
                        embed.add_field(name="Parc", value=f"{coaster['park']['name']} ({msg.author.display_name})", inline=True)
                        if park_found and coaster_found:
                            embed.color = discord.Color.green()
                        await question_msg.edit(embed=embed)
                    
                    # Coaster answer
                    elif coaster_match >= config.MIN_MATCH_SCORE and not coaster_found:
                        coaster_found = True
                        await coaster_bot.save_game_result({'game_id': game_id}, 'coaster', msg.author.id, response_time)
                        
                        # Speed bonus message
                        speed_msg = ""
                        if response_time < 10:
                            speed_msg = " ⚡ Lightning fast!"
                        elif response_time < 30:
                            speed_msg = " 🚀 Quick thinking!"
                        
                        title = f"Bravo {msg.author.display_name}, tu as trouvé le coaster!{speed_msg}"
                        if not park_found:
                            title += "\nSaurez-vous trouver le parc ?"
                        
                        embed = coaster_bot.create_embed(title, coaster['name'], discord.Color.green())
                        await ctx.send(embed=embed)
                        
                        # Update question embed
                        embed = question_msg.embeds[0]
                        embed.add_field(name="Coaster", value=f"{coaster['name']} ({msg.author.display_name})", inline=True)
                        if park_found and coaster_found:
                            embed.color = discord.Color.green()
                        await question_msg.edit(embed=embed)
                    
                    # Hints for close answers
                    elif (config.HINT_MATCH_SCORE <= park_match < config.MIN_MATCH_SCORE and not park_found) or \
                         (config.HINT_MATCH_SCORE <= coaster_match < config.MIN_MATCH_SCORE and not coaster_found):
                        await ctx.send("Ça chauffe! 🔥")
                
                except asyncio.TimeoutError:
                    # Check if game has timed out completely
                    if elapsed_time >= config.GAME_TIMEOUT:
                        # Game timeout - show final message and break
                        taunt = random.choice(config.CC_TAUNTS)
                        embed = coaster_bot.create_embed(
                            title=taunt,
                            description=f"Il s'agissait de **{coaster['name']}** se trouvant à **{coaster['park']['name']}**",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                        
                        # Update question embed to show timeout
                        embed = question_msg.embeds[0]
                        embed.color = discord.Color.red()
                        await question_msg.edit(embed=embed)
                        break
                    else:
                        # Just a short timeout to check hints - continue loop
                        continue
                
            except asyncio.TimeoutError:
                # Game timeout
                taunt = random.choice(config.CC_TAUNTS)
                embed = coaster_bot.create_embed(
                    title=taunt,
                    description=f"Il s'agissait de **{coaster['name']}** se trouvant à **{coaster['park']['name']}**",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                
                # Update question embed to show timeout
                embed = question_msg.embeds[0]
                embed.color = discord.Color.red()
                await question_msg.edit(embed=embed)
                break
        
        log.info(f"Game ended in {ctx.channel}")
        
    except Exception as e:
        log.error(f"Error in game: {e}")
        await ctx.send("Une erreur est survenue lors du jeu. Réessayez plus tard.")
    
    finally:
        # Remove channel from games in progress
        games_in_progress.discard(ctx.channel.id)

@bot.command(name='score', aliases=['points', 'stats', 'statistics', 'profile'])
async def show_score(ctx, user: discord.User = None):
    """Show player score and detailed statistics"""
    if user is None:
        user = ctx.author
    
    try:
        # Get basic score first
        score = await coaster_bot.get_player_score(user.id)
        
        # Get detailed stats
        stats = await coaster_bot.get_player_stats(user.id)
        basic = stats['basic']
        
        embed = coaster_bot.create_embed(
            title=f"🏆 {score} points",
            color=discord.Color.blue(),
            author=user
        )
        
        if basic[0] == 0:  # total_games
            embed.description = "No games played yet! Use `!game` to start playing."
            await ctx.send(embed=embed)
            return
        
        # Calculate derived stats
        total_games, games_won, parks_found, coasters_found, total_points = basic[:5]
        avg_park_time, avg_coaster_time, fastest_park, fastest_coaster = basic[5:]
        
        win_rate = (games_won / total_games * 100) if total_games > 0 else 0
        avg_response_time = ((avg_park_time or 0) + (avg_coaster_time or 0)) / 2 if avg_park_time or avg_coaster_time else 0
        
        # Games and accuracy stats
        embed.add_field(
            name="🎮 Games", 
            value=f"**{total_games}** played\n**{games_won}** won\n**{win_rate:.1f}%** win rate", 
            inline=True
        )
        
        embed.add_field(
            name="🎯 Accuracy", 
            value=f"**{parks_found}** parks\n**{coasters_found}** coasters", 
            inline=True
        )
        
        # Speed stats
        if avg_response_time > 0:
            speed_emoji = "⚡" if avg_response_time < 45 else "🚀" if avg_response_time < 90 else "🐌"
            fastest_time = min(fastest_park or 999, fastest_coaster or 999)
            embed.add_field(
                name=f"{speed_emoji} Speed", 
                value=f"**{avg_response_time:.1f}s** average\n**{fastest_time:.1f}s** fastest", 
                inline=True
            )
        
        # Difficulty breakdown
        difficulty_text = ""
        difficulty_names = {1: "Easy", 2: "Medium", 3: "Hard"}
        for diff_stat in stats['difficulty']:
            difficulty, wins = diff_stat
            if wins > 0:  # Only show difficulties where user has wins
                difficulty_text += f"**{difficulty_names.get(difficulty, 'Unknown')}**: {wins} wins\n"
        
        if difficulty_text:
            embed.add_field(name="🎲 Difficulty", value=difficulty_text, inline=True)
        
        # Performance badges
        badges = []
        if fastest_park and fastest_park < 10:
            badges.append("⚡ Speed Demon")
        if fastest_coaster and fastest_coaster < 10:
            badges.append("⚡ Speed Demon")
        if win_rate > 75:
            badges.append("🎯 Sharpshooter")
        if total_points > 100:
            badges.append("💯 Century Club")
        if parks_found > 50:
            badges.append("🗺️ Explorer")
        if coasters_found > 50:
            badges.append("🎢 Coaster Master")
        
        if badges:
            # Remove duplicates and join
            unique_badges = list(dict.fromkeys(badges))
            embed.add_field(name="🏆 Badges", value=" • ".join(unique_badges), inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        log.error(f"Error getting score/stats: {e}")
        await ctx.send("Erreur lors de la récupération du score.")

@bot.command(name='leaderboard', aliases=['classement', 'top'])
async def show_leaderboard(ctx, limit: int = 10):
    """Show leaderboard"""
    if limit > 25:
        limit = 25
    
    try:
        leaderboard = await coaster_bot.get_leaderboard(limit)
        
        embed = coaster_bot.create_embed(
            title="🏆 Classement (30 derniers jours)",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url="https://image.flaticon.com/icons/png/512/262/262831.png")
        
        if not leaderboard:
            embed.description = "Aucun score enregistré ce mois-ci."
        else:
            for i, (user_id, score) in enumerate(leaderboard, 1):
                try:
                    user = bot.get_user(user_id) or await bot.fetch_user(user_id)
                    name = user.display_name if user else "Utilisateur inconnu"
                except:
                    name = "Utilisateur inconnu"
                
                # Add medal emojis for top 3
                medal = ""
                if i == 1:
                    medal = "🥇 "
                elif i == 2:
                    medal = "🥈 "
                elif i == 3:
                    medal = "🥉 "
                
                embed.add_field(
                    name=f"{medal}{i}. {name}",
                    value=f"{score} points",
                    inline=False
                )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        log.error(f"Error getting leaderboard: {e}")
        await ctx.send("Erreur lors de la récupération du classement.")

if __name__ == "__main__":
    bot.run(config.BOT_TOKEN)