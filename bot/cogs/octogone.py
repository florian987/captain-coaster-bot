import logging
import random

import discord
from discord.ext import commands
from bot.constants import WINNER

log = logging.getLogger(__name__)


class Octofight(commands.Cog, name='Octocog'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='fight', aliases=['octofight'])
    @commands.guild_only()
    async def fight(self, ctx):
        """
        Octogone between tards
        """

        try:
            await ctx.message.delete()
        except Exception as e:
            log.info("No permission to delete messages")

        if ctx.message.mentions:
            ctx.message.mentions.append(ctx.message.author)

        # delete dupes
        players = list(dict.fromkeys(ctx.message.mentions))

        winner = random.choice(players)
        log.info(f"Octogone battle started by {ctx.message.author} with {' '.join([str(i) for i in players])}.")
        log.info(f"{winner} won the octogone battle started.")

        embed = discord.Embed(
            title=random.choice(WINNER),
            colour=discord.Colour.green())
        embed.set_author(icon_url=winner.avatar_url,
                         name=str(winner))
        await ctx.send(content='', embed=embed)


def setup(bot):
    bot.add_cog(Octofight(bot))
