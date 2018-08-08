import discord
from discord.ext import commands

import sys
import traceback
import logging
import yaml

from secret import secret

import cogs.scrapper.settings

import cogs.custom_functions as tools 

logging.basicConfig(level=logging.DEBUG)


"""This is a multi file example showcasing many features of the command
extension and the use of cogs.
These examples make use of Python 3.5 and the rewrite version on the lib.
For examples on cogs for the async version:
https://gist.github.com/leovoel/46cd89ed6a8f41fd09c5
Rewrite Documentation:
http://discordpy.readthedocs.io/en/rewrite/api.html
Rewrite Commands Documentation:
http://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html
Familiarising yourself with the documentation will greatly help you.
"""

# YML config
# https://gitlab.nextcoders.eu/weStart/DisBot/blob/master/disbot.py
try:
    with open('config.yml', 'r') as config_file:
        config = yaml.load(config_file)
except FileNotFoundError:
    print('Config file not found!')
    exit(1)

try:
    token = config['token']
except:
    print('Token not set in config.')
    exit(1)


def get_prefix(bot, message):
    """A callable Prefix for our bot.
    This could be edited to allow per server prefixes.
    """

    # Notice how you can use spaces in prefixes.
    # Try to keep them simple though.
    #prefixes = ['/']
    prefixes = config['prefixes']

    # If we are in a guild, we allow for the user to mention
    # us or use any of the prefixes in our list.
    return commands.when_mentioned_or(*prefixes)(bot, message)


# Below cogs represents our folder our cogs are in.
# Following is the file name. So 'meme.py' in cogs, would be cogs.meme
# Think of it like a dot path import
#initial_extensions = ['cogs.owner',
#                      'cogs.default',
#                      'cogs.vrs',
#                      'cogs.embed',
#                      'cogs.dev',
#                      'cogs.error_handler',
#                      'cogs.config']

initial_extensions = config['extensions']

# Proxy settings
proxy='http://fw_in.bnf.fr:8080'

bot = commands.Bot(
    command_prefix=get_prefix,
    description=config['description'])


# Here we load our extensions(cogs) listed above in [initial_extensions].
if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}.', file=sys.stderr).format(
                extension)

            traceback.print_exc()


@bot.event
async def on_ready():
    """http://discordpy.readthedocs.io/en/rewrite/api.html#discord.on_ready"""

    print(
        ("""\n\n
        Logged in as: {} -{}\n
        Version: {}\n
        """).format(bot.user.name, bot.user.id, discord.__version__))

    # Changes our bots Playing Status. t
    # ype=1(streaming) for a standard game you could remove type and url.
    if config['activity']:
        await bot.change_presence(activity=discord.Game(name=config['activity']))

    

    print('Successfully logged in and booted...!')




bot.run(
    token,
    bot=True,
    reconnect=True
)