from discord.ext import commands
import discord.ext.commands.errors
import discord


class Dev_Commands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='getchannels', aliases=['getchans'])
    @commands.is_owner()
    async def list_categories(self, ctx, *, lookup_category: discord.CategoryChannel):
        """List channels from a category"""
        await ctx.send(', '.join(channel.name.replace('_',r'\_') for channel in lookup_category.channels))
    
    
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

    @list_categories.error
    async def  list_categories_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'lookup_category':
                await ctx.send('Please provide a category name.')

    @do_repeat.error
    async def do_repeat_handler(self, ctx, error):
        """A local Error Handler for our command do_repeat.
        This will only listen for errors in do_repeat.

        The global on_command_error will still be invoked after."""

        # Check if our required argument inp is missing.
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'inp':
                await ctx.send("You forgot to give me input to repeat!")

def setup(bot):
    bot.add_cog(Dev_Commands(bot))
