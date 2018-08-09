from discord.ext import commands
from discord.ext.commands import Context
import discord
import shlex


class Poll_Commands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='poll', aliases=['vote'])
    @commands.guild_only()
    async def poll(self, ctx: Context, *, args: str):
        """Start a poll.
        /poll "Question ?" "Choice 1" "Choice 2" "Choice 3"
        """

        splitted_args = shlex.split(args)

        embed = discord.Embed(
            title = splitted_args.pop(0)
        )

        choice_count = 1
        while len(splitted_args):
            embed.add_field(name=f"Choice {str(choice_count)}", value=splitted_args.pop(0), inline=True)
            choice_count += 1


        await ctx.send(content='', embed=embed)

    #
    # ERROR HANDLER
    #
    @poll.error
    async def getparam_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Title",
                description="Description",
                colour=ctx.author.color
            )
            await ctx.send(content='', embed=embed)

def setup(bot):
    bot.add_cog(Poll_Commands(bot))
