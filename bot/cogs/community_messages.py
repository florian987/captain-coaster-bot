import discord
from discord.ext import commands

log = logging.getLogger(__name__)

class CommunityMessages(commands.Cog, name='Community Messages Management'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name=None, aliases=[])
    @commands.guild_only()
    async def on_reaction(self, ctx, reaction):
        """
        Pin message when chosen emoji is used in reaction
        """
        embed = discord.Embed(
            title=title,
            description=text,
            colour=ctx.author.colour)
        embed.set_author(icon_url=ctx.author.avatar_url,
                         name=str(ctx.author))
        await ctx.send(content='', embed=embed)


def setup(bot):
    bot.add_cog(Default_Commands(bot))
