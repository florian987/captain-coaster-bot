import logging
import random
from asyncio import Lock
from functools import wraps
from weakref import WeakValueDictionary

from discord import Colour
from discord.ext import commands
from discord.ext.commands import Context  # , Embed

from bot.constants import ERROR_REPLIES
from bot.utils.checks import with_role_check, without_role_check


log = logging.getLogger(__name__)


def with_role(*role_ids: int):
    """
    Returns True if the user has any one
    of the roles in role_ids.
    """

    async def predicate(ctx: Context):
        return with_role_check(ctx, *role_ids)
    return commands.check(predicate)


def without_role(*role_ids: int):
    """
    Returns True if the user does not have any
    of the roles in role_ids.
    """

    async def predicate(ctx: Context):
        return without_role_check(ctx, *role_ids)
    return commands.check(predicate)


def in_channel(channel_id: int):
    async def predicate(ctx: Context):
        check = ctx.channel.id == channel_id
        log.info(f"{ctx.author} tried to call the '{ctx.command.name}' "
                  "command. "
                  f"The result of the in_channel check was {check}")
        return check
    return commands.check(predicate)


def in_dm():
    async def predicate(ctx: Context):
        check = ctx.guild is None
        log.info(f"{ctx.author} tried to call the '{ctx.command.name}' "
                  "command. "
                  f"The result of the in_dm check was {check}")
        return check
    return commands.check(predicate)


def in_channel_or_dm(channel_id: int):
    async def predicate(ctx: Context):
        check = ctx.channel.id == channel_id or ctx.guild is None
        log.info(f"{ctx.author} tried to call the '{ctx.command.name}' "
                  "command. "
                  f"The result of the in_channel check was {check}")
        return check
    return commands.check(predicate)


def in_any_channel_or_dm(*args):
    async def predicate(ctx: Context):
        check = ctx.channel.id in args or ctx.guild is None
        log.info(f"{ctx.author} tried to call the '{ctx.command.name}' command."
                 f" The result of the in_channel check was {check}")
        return check
    return commands.check(predicate)


def in_any_channel_guild(*args):
    async def predicate(ctx: Context):
        check = ctx.channel.id in args or ctx.guild.id in args or ctx.guild is None
        log.debug(f"{ctx.author} tried to call the '{ctx.command.name}' "
                  "command. "
                  f"The result of the in_channel check was {check}")
        return check
    return commands.check(predicate)


# PlaceHolder, need constants
def locked():
    """
    Allows the user to only run one instance of the decorated command at a time.
    Subsequent calls to the command from the same author are
    ignored until the command has completed invocation.

    This decorator has to go before (below) the `command` decorator.
    """

    def wrap(func):
        func.__locks = WeakValueDictionary()

        @wraps(func)
        async def inner(self, ctx, *args, **kwargs):
            lock = func.__locks.setdefault(ctx.author.id, Lock())
            if lock.locked():
                embed = Embed()
                embed.colour = Colour.red()

                log.debug(f"User tried to invoke a locked command.")
                embed.description = (
                    "You're already using this command. Please wait until it is done before you use it again."
                )
                embed.title = random.choice(ERROR_REPLIES)
                await ctx.send(embed=embed)
                return

            async with func.__locks.setdefault(ctx.author.id, Lock()):
                return await func(self, ctx, *args, **kwargs)
        return inner
    return wrap
