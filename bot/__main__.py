import logging
import sys
import traceback
import socket

import discord
from aiohttp import AsyncResolver, ClientSession, TCPConnector
from discord import Game
from discord.ext.commands import Bot, when_mentioned_or
from bot.constants import Bot as BotConfig, Prefixes


log = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

bot = Bot(
    command_prefix=when_mentioned_or(*Prefixes.guild),
    activity=Game(name=BotConfig.activity),
    case_insensitive=True,
    max_messages=10_000
)

# Global aiohttp session for all cogs
# - Uses asyncio for DNS resolution instead of threads, so we don't spam threads
# - Uses AF_INET as its socket family to prevent https related problems both locally and in prod.
bot.http_session = ClientSession(
    connector=TCPConnector(
        resolver=AsyncResolver(),
        family=socket.AF_INET,
    )
)

# """This is a multi file example showcasing many features of the command
# extension and the use of cogs.
# These examples make use of Python 3.5 and the rewrite version on the lib.
# For examples on cogs for the async version:
# https://gist.github.com/leovoel/46cd89ed6a8f41fd09c5
# Rewrite Documentation:
# http://discordpy.readthedocs.io/en/rewrite/api.html
# Rewrite Commands Documentation:
# http://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html
# Familiarising yourself with the documentation will greatly help you.
# """
# 
# # YML config
# # https://gitlab.nextcoders.eu/weStart/DisBot/blob/master/disbot.py
# try:
#     with open('config.yml', 'r') as config_file:
#         config = yaml.load(config_file)
# except FileNotFoundError:
#     print('Config file not found!')
#     exit(1)
# 
# try:
#     token = config['token']
# except Exception:
#     print('Token not set in config.')
#     exit(1)


# def get_prefix(bot, message):
#     """
#     A callable Prefix for our bot.
#     This could be edited to allow per server prefixes.
#     """
# 
#     # Notice how you can use spaces in prefixes.
#     # Try to keep them simple though.
#     # prefixes = ['/']
#     prefixes = config['prefixes']
# 
#     # If we are in a guild, we allow for the user to mention
#     # us or use any of the prefixes in our list.
#     return commands.when_mentioned_or(*prefixes)(bot, message)


# Import initial cogs
initial_extensions = BotConfig.cogs

# for extension in initial_extensions:
#     bot.load_extension(extension)

# bot = commands.Bot(
#     command_prefix=get_prefix,
#     description=config['description'])


# Here we load our extensions(cogs) listed above in [initial_extensions].
if __name__ == '__main__':
    for extension in initial_extensions:

        # Add '.cogs' prefix
        if not extension.startswith("cogs"):
            extension = 'cogs.' + extension

        try:
            bot.load_extension('bot.' + extension)
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=sys.stderr)
            traceback.print_exc()


@bot.event
async def on_ready():
    """
    http://discordpy.readthedocs.io/en/rewrite/api.html#discord.on_ready
    """
    bot.appinfo = await bot.application_info() # Store appinfos

    print(
        (f"""\n\n
        Logged in as: {bot.user.name} -{bot.user.id}\n
        Version: {discord.__version__}\n
        """))

    # Changes our bots Playing Status. t
    # ype=1(streaming) for a standard game you could remove type and url.
    # if config['activity']:
    #     await bot.change_presence(
    #         activity=discord.Game(name=config['activity']))

    print('Successfully logged in and booted...!')


# @bot.before_invoke
# async def before_any_command(ctx):
#    if config['activity']:
#        await bot.change_presence(
#           activity=discord.Game(name=config['activity']))
#    pass

@bot.after_invoke
async def after_any_command(ctx):
    if BotConfig.activity:
        await bot.change_presence(
            activity=discord.Game(name=BotConfig.activity))
    pass


bot.run(
    BotConfig.token,
    bot=True,
    reconnect=True
)


bot.http_session.close()
