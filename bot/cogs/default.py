import logging
import parser

import discord
from discord.ext import commands


log = logging.getLogger(__name__)


class Default_Commands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='calc', aliases=['calculate'])
    async def calc(self, ctx, *, args):
        """
        A simple command which does calculations.

        Examples:
        /calc 6 * 4 -- multiply
        /calc 6 + 5 -- add
        /calc 8 / 2 -- divide
        /calc 6 - 4 -- subtract
        /calc 6 ** 3 -- power
        """

        total = eval(parser.expr(args).compile())

        # embed doc
        # https://cdn.discordapp.com/attachments/84319995256905728/252292324967710721/embed.png
        embed = discord.Embed(
            title=f"Answer = **{total}**",
            description="Do another calc with `/help calc`!",
            colour=ctx.author.colour)
        embed.set_author(icon_url=ctx.author.avatar_url,
                         name=str(ctx.author))
        await ctx.send(content='', embed=embed)
        log.info(f"{ctx.author} did some maths: {args}")

    @commands.command(name='ping', aliases=['latency'])
    async def ping(self, ctx):
        """Get the bots latency"""
        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="Pong!",
            description=f"{latency} ms",
            colour=discord.Color.blue()
        )
        # embed.set_author(icon_url=ctx.author.avatar_url,
        #                 name=str(ctx.author))
        log.info(f"{ctx.author} pinged me at {latency}ms")
        return await ctx.send(content='', embed=embed)


def setup(bot):
    bot.add_cog(Default_Commands(bot))
