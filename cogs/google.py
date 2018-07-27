from discord.ext import commands
import discord
from googlesearch import search


class Default_Commands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="google", aliases=["ggl"])
    @commands.guild_only()
    async def setups(self, ctx, query):
        """Google query"""

        # Check if VRS is online
        
        for url in search(query, stop=5):
            print(url)
            #title = "Coming soon!"
            text = url
            embed = discord.Embed(
                title="results",
                description=text,
                colour=ctx.author.colour)
            embed.set_author(icon_url=ctx.author.avatar_url,
                            name=str(ctx.author))
            await ctx.send(content='', embed=embed)


def setup(bot):
    bot.add_cog(Default_Commands(bot))
