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
    
    
    @commands.command(name='showconf', aliases=['displayconf'])
    @commands.is_owner()
    async def showconf(self, ctx):
        """Display Bot configuration"""
        print(dir(self.bot))
        print(dir(self.bot.user))
        print('name:', self.bot.user.name)
        print('avatar_url:', self.bot.user.avatar_url)
        print(self.bot.user)

    
    """Below is an example of a Local Error Handler for our command do_repeat"""
    @commands.command(name='repeat', aliases=['mimic', 'copy'])
    async def do_repeat(self, ctx, *, inp: str):
        """A simple command which repeats your input!
        inp  : The input to be repeated"""
        await ctx.send(inp)


    #
    # ERROR HANDLER
    #

    @list_categories.error
    async def  list_categories_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'lookup_category':
                await ctx.send('Please provide a category name.')
        if isinstance(error, commands.BadArgument):
            #print(type(error), dir(error))
            #print(error.args, error.__str__)
            await ctx.send(str(error).replace('Channel', 'Category'))

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
