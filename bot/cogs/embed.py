import logging
import shlex

import discord
from discord.ext import commands

from bot.utils.embedconverter import build_embed

log = logging.getLogger(__name__)


class Embed_Commands(commands.Cog, name='Embed Testing Cog'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='embed', aliases=['embd', 'mbd'])
    async def testembed(self, ctx, *, args):
        """
        A simple command which generate embeds using keywords.

        Examples:
        /mbd title="titre" descr="description"
        /embd title="titre" descr="description" print_dict=True
        /embed title="titre" descr="description" url="https://google.com"
        """

        args_dict = {}

        for arg in shlex.split(args):
            splitted_arg = arg.split("=")
            args_dict[splitted_arg[0]] = splitted_arg[1].strip('"').strip("'")

        embed = await build_embed(ctx, **args_dict)
        await ctx.send(embed=embed)

    #
    # ERROR HANDLER
    #
    @testembed.error
    async def getparam_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Title",
                description="Description",
                colour=ctx.author.color
            )
            await ctx.send(content='', embed=embed)


def setup(bot):
    bot.add_cog(Embed_Commands(bot))
