import discord
from discord.ext import commands


class Default_Commands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name=None, aliases=[])
    @commands.guild_only()
    async def test(self, ctx):
        """
        This is a example of how a embed would work
        """
        title = None
        text = None
        embed = discord.Embed(
            title=title,
            description=text,
            colour=ctx.author.colour)
        embed.set_author(icon_url=ctx.author.avatar_url,
                         name=str(ctx.author))
        await ctx.send(content='', embed=embed)


def setup(bot):
    bot.add_cog(Default_Commands(bot))
