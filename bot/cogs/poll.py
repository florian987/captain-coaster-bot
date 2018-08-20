
# import re
# import shlex

import logging
import random

import discord
from discord.ext import commands
from discord.ext.commands import Context

from emoji import UNICODE_EMOJI

log = logging.getLogger(__name__)


class Poll_Commands:
    def __init__(self, bot):
        self.bot = bot
        self.std_emojis = [e for e in UNICODE_EMOJI if len(e) == 1]

    @commands.command(name='poll', aliases=['vote'])
    @commands.guild_only()
    async def poll(self, ctx: Context, *args: commands.clean_content):
        """Start a poll.
        Usage: /poll "Question ?" "Choice 1" "Choice 2" "Choice 3"
        """

        # Delete original message
        await ctx.message.delete()

        # TODO useless transform ?
        argslist = list(args)

        if len(argslist) < 3:
            return

        embed = discord.Embed(
            title=argslist.pop(0),
            colour=discord.Colour.dark_gold()
        )

        embed.set_author(
            icon_url=ctx.author.avatar_url,
            name=ctx.author.name,
            url=ctx.author.avatar_url
        )

        # Build emojis list
        used_emojis = []
        guild_emojis = [(e for e in self.bot.emojis if
                         e.guild == ctx.guild and not e.managed)]
        allowed_emojis = guild_emojis + self.std_emojis

        # Link emojis to choices
        while len(argslist):
            chosen_emoji = random.choice(
                [e for e in allowed_emojis if e not in used_emojis])
            embed.add_field(
                name=argslist.pop(0), value=chosen_emoji, inline=True)
            used_emojis.append(chosen_emoji)

        # Send embed
        message = await ctx.send(content='', embed=embed)

        # Add reaction to embed
        while len(used_emojis):
            await message.add_reaction(used_emojis.pop(0))

        log.info(f"{ctx.author} started a poll: {args}")

    #
    # ERROR HANDLER
    #
    @poll.error
    async def getparam_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            log.error(f"{ctx.author} triied to start a poll on '{ctx.guild}' "
                      "Guild without arguments")
            embed = discord.Embed(
                description="Poll need question and choices",
                colour=discord.Colour.red()
            )
        elif isinstance(error, commands.BadArgument):
            log.error(f"{ctx.author} failed to start a poll on '{ctx.guild}' "
                      f"Guild malformed arguments:\n'{ctx.message.content}'")
            embed = discord.Embed(
                description=f"Poll - malformed arguments\n"
                            f"{ctx.message.content}",
                colour=discord.Colour.red()
            )
        # elif isinstance(error, commands.CommandInvokeError):
        #    log.error(
        #       f"{ctx.author} triied to start a poll on '{ctx.guild}' Guild "
        #            "but it doesn't have enough emojis")
        #    embed = discord.Embed(
        #        description="Not enough emojis on this server :(.",
        #        colour=discord.Colour.red()
        #    )

        await ctx.send(content='', embed=embed)

# Not enough emojis
# Command raised an exception: IndexError: Cannot choose from an empty sequence
# <built-in method with_traceback of CommandInvokeError


def setup(bot):
    bot.add_cog(Poll_Commands(bot))
