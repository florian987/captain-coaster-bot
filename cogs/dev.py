from discord.ext import commands
import discord.ext.commands.errors
import discord

class Dev_Commands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='getchannels', aliases=['getchans'])
    @commands.is_owner()
    @commands.guild_only()
    async def list_channels(self, ctx, *, lookup_category: discord.CategoryChannel):
        """List channels from a category"""

        await ctx.send(', '.join(channel.name.replace('_',r'\_') for channel in lookup_category.channels))
        print(ctx.guild.roles)
        print(dir(ctx))

    @commands.command(name='repeat', aliases=['mimic', 'copy'])
    @commands.is_owner()
    async def do_repeat(self, ctx, *, inp: str):
        """A simple command which repeats your input!
        inp  : The input to be repeated"""
        await ctx.send(inp)


    @commands.command(name='say', aliases=['talk'])
    @commands.is_owner()
    async def say(self, ctx, *, inp: str):
        """Make the bot talks"""
        await ctx.message.delete()
        await ctx.send(inp)

    @commands.command(name='args')
    @commands.is_owner()
    async def printargs(self, ctx, *args):
        await ctx.send(content=f"**\*args**\n```\n{args}\n```")

    @commands.command(name='astargs')
    @commands.is_owner()
    async def printastargs(self, ctx, *, args):
        await ctx.send(content=f"**\*, args**\n```\n{args}\n```")

    #
    # ERROR HANDLER
    #

    @list_channels.error
    async def list_channels_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'lookup_category':
                embed = discord.Embed(
                    description="Please provide a category name.",
                    color=discord.Colour.red()
                )
        elif isinstance(error, commands.BadArgument):
            #print(type(error), dir(error))
            #print(error.args, error.__str__)
            embed = discord.Embed(
                    description=str(error).replace('Channel', 'Category'),
                    color=discord.Colour.red()
                )
        await ctx.send(content='', embed=embed)

    @do_repeat.error
    async def do_repeat_handler(self, ctx, error):
        """A local Error Handler for our command do_repeat.
        This will only listen for errors in do_repeat.

        The global on_command_error will still be invoked after."""

        # Check if our required argument inp is missing.
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'inp':
                embed = discord.Embed(
                    description='I need some text my dude.',
                    color=discord.Colour.red()
                )
        await ctx.send(content='', embed=embed)

def setup(bot):
    bot.add_cog(Dev_Commands(bot))
