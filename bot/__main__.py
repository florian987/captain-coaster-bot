import logging
import sys
import traceback
import socket

import discord
from aiohttp import AsyncResolver, ClientSession, TCPConnector
from discord import Game
from discord.ext.commands import Bot, when_mentioned_or, errors
from bot.constants import Bot as BotConfig, Prefixes


log = logging.getLogger(__name__)

logging.basicConfig(level=BotConfig.loglevel)
# logging.basicConfig(level=logging.DEBUG)

bot = Bot(
    command_prefix=when_mentioned_or(*Prefixes.guild),
    activity=Game(name=BotConfig.activity),
    case_insensitive=True,
    max_messages=10_000,
    fetch_offline_members=True
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


# Here we load our extensions(cogs) listed above in BotConfig.cogs.
if __name__ == '__main__':
    log.info(f"Cog list: {BotConfig.cogs}")
    for extension in BotConfig.cogs:

        # Add '.cogs' prefix
        if not extension.startswith("cogs"):
            extension = 'cogs.' + extension

        try:
            bot.load_extension('bot.' + extension)
        except errors.ExtensionAlreadyLoaded as e:
            print(f'Extension already loaded: {extension}.', file=sys.stderr)
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=sys.stderr)
            traceback.print_exc()
        else:
            log.info(f"Cog loaded: {extension}")


@bot.event
async def on_ready():
    """
    http://discordpy.readthedocs.io/en/rewrite/api.html#discord.on_ready
    """
    bot.appinfo = await bot.application_info()  # Store appinfos

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
