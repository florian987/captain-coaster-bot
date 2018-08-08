from discord.ext import commands
import discord


class OwnerCog:

    def __init__(self, bot):
        self.bot = bot

    # Hidden means it won't show up on the default help.
    @commands.command(name='load', hidden=True)
    @commands.is_owner()
    async def cog_load(self, ctx, *, cog: str):
        """Command which Loads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send('**`ERROR:`** {} - {}'.format(type(e).__name__, e))
        else:
            embed = discord.Embed(
                description='Cog loaded.',
                colour=discord.Colour.green())
            #await ctx.send('**`SUCCESS`**')
            await ctx.send(content='', embed=embed)

    @commands.command(name='unload', hidden=True)
    @commands.is_owner()
    async def cog_unload(self, ctx, *, cog: str):
        """Command which Unloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send('**`ERROR:`** {} - {}'.format(type(e).__name__, e))
        else:
            embed = discord.Embed(
                description='Cog unloaded.',
                colour=discord.Colour.green())
            #await ctx.send('**`SUCCESS`**')
            await ctx.send(content='', embed=embed)

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def cog_reload(self, ctx, *, cog: str):
        """Command which Reloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send('**`ERROR:`** {} - {}'.format(type(e).__name__, e))
        else:
            embed = discord.Embed(
                description='Cog reloaded.',
                colour=discord.Colour.green())
            #await ctx.send('**`SUCCESS`**')
            await ctx.send(content='', embed=embed)

    @commands.command(name='listcogs', hidden=True)
    @commands.is_owner()
    async def cog_list(self, ctx):
        """Command which List loaded Modules."""

        await ctx.send('```\n' + ", ".join([ext.split(".")[1] for ext in ctx.bot.extensions]) + '\n```')


def setup(bot):
    bot.add_cog(OwnerCog(bot))
