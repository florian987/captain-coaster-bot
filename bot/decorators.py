import logging
import random
from asyncio import Lock
from functools import wraps
from weakref import WeakValueDictionary

from discord import Colour
from discord.ext import commands
from discord.ext.commands import Context  # , Embed

from bot.constants import ERROR_REPLIES


log = logging.getLogger(__name__)


def with_role(*role_ids: int):
    async def predicate(ctx: Context):
        if not ctx.guild:  # Block in DM
            log.debug(f"{ctx.author} tried to us the '{ctx.command.name}' "
                      "command from a DM.\n"
                      "This command is restricted by the with_role decorator. "
                      "Rejecting request.")
            return False

        for role in ctx.author.roles:
            if role.id in role_ids:
                log.debug(f"{ctx.author} has the '{role.name}' role, and passes the check.")
                return True

        log.debug(f"{ctx.author} does not have the required role to use "
                  f"the '{ctx.command.name}' command, so the request "
                  "is rejected.")
        return False
    return commands.check(predicate)


def without_role(*role_ids: int):
    async def predicate(ctx: Context):
        if not ctx.guild:  # Block in DM
            log.debug(f"{ctx.author} tried to us the '{ctx.command.name}' "
                      "command from a DM.\n"
                      "This command is restricted by the with_role decorator. "
                      "Rejecting request.")
            return False

        author_roles = [role.id for role in ctx.author.roles]
        check = all(role not in author_roles for role in role_ids)
        log.debug(f"{ctx.author} tried to call the '{ctx.command.name}' "
                  "command. "
                  f"The result of the without_role check was {check}")
        return check
    return commands.check(predicate)


def in_channel(channel_id: int):
    async def predicate(ctx: Context):
        check = ctx.channel.id == channel_id
        log.debug(f"{ctx.auhtor} tried to call the '{ctx.command.name}' "
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
