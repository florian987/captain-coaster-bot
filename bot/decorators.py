import logging
import random
from asyncio import Lock
from functools import wraps
from weakref import WeakValueDictionary

from discord import Colour
from discord.ext import commands
from discord.ext.commands import Context  # , Embed

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
