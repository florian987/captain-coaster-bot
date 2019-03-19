import logging
import random
import inflect

import discord
from discord.ext import commands
from discord.ext.commands import Context
import bot.utils.emojis as emojis

log = logging.getLogger(__name__)

p = inflect.engine()
intemojis = emojis.emojis_numbers()


class Poll(commands.Cog, name='Poll Cog'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='poll', aliases=['vote'])
    @commands.guild_only()
    async def poll(self, ctx: Context, *args: commands.clean_content):
        """
        /poll "Question ?" "Choice 1" "Choice 2" "Choice 3"
        """

        await ctx.message.delete()

        # Transform tuple args to list so we can pop items
        argslist = list(args)

        if len(argslist) < 3 or len(argslist) > 11:
            return

        embed = discord.Embed(
            title=argslist.pop(0),
            colour=discord.Colour.dark_gold())
        embed.set_author(
            icon_url=ctx.author.avatar_url,
            name=ctx.author.name,
            url=ctx.author.avatar_url)

        # Link emojis to choices
        for i, opt in enumerate(argslist):
            embed.add_field(
                name=f'{intemojis[p.number_to_words(i)]} {opt}',
                value=" ‏‏‎ ", inline=False)

        # Send embed
        message = await ctx.send(content='', embed=embed)

        # Add reaction to embed
        for i, opt in enumerate(argslist):
            await message.add_reaction(intemojis[p.number_to_words(i)])

        log.info(f"{ctx.author} started a poll: {args}")

    #
    # ERROR HANDLER
    #
    # @poll.error
    # async def getparam_handler(self, ctx, error):
    #     if isinstance(error, commands.MissingRequiredArgument):
    #         log.error(f"{ctx.author} triied to start a poll on '{ctx.guild}' "
    #                   "Guild without arguments")
    #         embed = discord.Embed(
    #             description="Poll need question and choices",
    #             colour=discord.Colour.red()
    #         )
    #     elif isinstance(error, commands.BadArgument):
    #         log.error(f"{ctx.author} failed to start a poll on '{ctx.guild}' "
    #                   f"Guild malformed arguments:\n'{ctx.message.content}'")
    #         embed = discord.Embed(
    #             description=f"Poll - malformed arguments\n"
    #                         f"{ctx.message.content}",
    #             colour=discord.Colour.red()
    #         )
    #     await ctx.send(content='', embed=embed)



def setup(bot):
    bot.add_cog(Poll(bot))
