from discord.ext import commands
import discord
import requests


class Default_Commands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setups", aliases=["vrs-setups"])
    @commands.guild_only()
    async def setups(self, ctx):
        """Retrieve cars setups from Virtual Racing School Website"""

        # Check if VRS is online
        r = requests.get("https://virtualracingschool.appspot.com/#/DataPacks")

        if r.status_code == 200:
            title = "Le site VRS est Online!"
        else:
            title = "Le site VRS est offline :'("

        #title = "Coming soon!"
        text = "un peu de patience !"
        embed = discord.Embed(
            title=title,
            description=text,
            colour=ctx.author.colour)
        embed.set_author(icon_url=ctx.author.avatar_url,
                         name=str(ctx.author))
        await ctx.send(content='', embed=embed)


def setup(bot):
    bot.add_cog(Default_Commands(bot))
