from discord.ext import commands
import discord
import os


class Default_Commands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name=None, aliases=[])
    @commands.is_owner()
    async def config_save(self, ctx):
        """Save bot configuraiton into a json file"""

        cfg_file = 'config.json'

        with open (cfg_file, 'w') as file:
            




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
