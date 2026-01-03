"""
Simple configuration using environment variables.
"""
import os
from pathlib import Path

# Load .env file if it exists
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key, value)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Captain Coaster API
CAPTAIN_API_KEY = os.getenv('CAPTAIN_API_KEY')
if not CAPTAIN_API_KEY:
    raise ValueError("CAPTAIN_API_KEY environment variable is required")

CAPTAIN_URL = os.getenv('CAPTAIN_URL', 'https://captaincoaster.com')
CAPTAIN_CDN = os.getenv('CAPTAIN_CDN', 'https://pictures.captaincoaster.com')

# Database
DB_PATH = os.getenv('DB_PATH', './data/coasterbot.db')

# Game settings
GAME_TIMEOUT = 120.0
MIN_MATCH_SCORE = 80
HINT_MATCH_SCORE = 60

# Difficulty levels mapping
DIFFICULTY_LEVELS = {
    'easy': {'filter': '[gt]=500', 'points': 1},
    'medium': {'filter': '[between]=50..500', 'points': 2},
    'hard': {'filter': '[lt]=50', 'points': 5}
}

# French taunts for timeouts
CC_TAUNTS = [
    "On est chez les disney fans ici ?",
    "J'en ai marre des lambdas...",
    "Vous voulez pas visiter autre chose que le parc Spirou ?",
    "Faut sortir un peu les nerds...",
    "Vous avez laissé quelque neurones sur Goudurix ?",
    "La culture ici c'est un peu comme Mirapolis... une légende.",
    "Si c'est bleu c'est Mack ?' Bah voyons...",
    "Eh ben, c'est plus calme qu'un 15 Août au Parc Spirou, par ici...",
    "Ça se dit coasterfan, et ça reconnait pas un coaster chinois pourri ? Non mais allô, quoi...",
    "Personne ? Vous êtes moins fiables que Lightning Rod, en fait...",
    "Oui, c'est pas un coaster facile à reconnaître. Tu t'es cru sur Ameworld, là, ou quoi ?",
    "Aussi efficaces que les opérateurs de Port Aventura... Non mais sérieux...",
    "En même temps, avec ton CC de 41 coasters, avoue que t'étais mal barré...",
    "Comme CanCanCoaster, vous faites les beaux de l'extérieur, mais quand il s'agit de passer aux choses sérieuses, il n'y a plus grand-chose...",
    "Bon, si vous continuez sur cette lignée, on va finir plus rouillés que le lift de The Monster... ON SE REVEILLE !",
    "Le bon parc était Quanching... Xuixing... Quiching... Oh, et puis merde.",
    "Toujours pas trouvé ? Votre cerveau est plus mou que le launch de Blue Fire"
]