from discord.ext import commands
import discord.ext.commands.errors
import discord


class Dev_Commands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='getchannels', aliases=['getchans'])
    @commands.is_owner()
    async def test(self, ctx, lookup_category: discord.CategoryChannel = None):
        """List channels from a category"""
        if not lookup_category:
            await ctx.send("Please provide a category name.")
        else:
            await ctx.send(', '.join(channel.name.replace('_',r'\_') for channel in lookup_category.channels))
        #except discord.ext.commands.errors.BadArgument:
        #    await ctx.send(f'No category name {lookup_category} found.')
    
    
    """Below is an example of a Local Error Handler for our command do_repeat"""
    @commands.command(name='repeat', aliases=['mimic', 'copy'])
    async def do_repeat(self, ctx, *, inp: str):
        """A simple command which repeats your input!
        inp  : The input to be repeated"""

        await ctx.send(inp)


        # TODO Error handler cog
        #https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612

            #category = discord.utils.find(lambda c: c.name == lookup_category, ctx.guild.categories)
            #print(category)
            #if category:
            #    print(category.channels)
            #    await ctx.send(', '.join(channel.name for channel in category.channels))
            #else:
            #    await ctx.send(f'No category name {lookup_category} found.')


        #title = None
        #text = None
        #embed = discord.Embed(
        #    title=title,
        #    description=text,
        #    colour=ctx.author.colour)
        #embed.set_author(icon_url=ctx.author.avatar_url,
        #                 name=str(ctx.author))
        #await ctx.send(content='', embed=embed)


def setup(bot):
    bot.add_cog(Dev_Commands(bot))
