import logging
import traceback

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class OwnerCog(commands.Cog, name='Owner Cog'):

    def __init__(self, bot):
        self.bot = bot
        self.paginator = commands.Paginator(prefix="```py", suffix="```")

    # Hidden means it won't show up on the default help.
    @commands.command(name='load', hidden=True)
    @commands.is_owner()
    async def cog_load(self, ctx, *, cog: str):
        """
        Command which Loads a Module.
        Remember to use dot path. e.g: cogs.owner
        """

        if not cog.startswith("cogs"):
            cog = 'cogs.' + cog
        try:
            self.bot.load_extension('bot.' + cog)
        except Exception as e:
            log.error(f"{ctx.author} failed to load {cog}.")

            embed = discord.Embed(
                title=f"Failed to load {cog} cog.",
                description=f'{type(e).__name__} - {e}',
                colour=discord.Color.red()
            )

            traceback_msg = "".join(
                traceback.format_exception(
                    type(e), e, e.__traceback__
                )
            )

            owner_embed = discord.Embed(
                title="Fix ya shit",
                colour=discord.Color.dark_red()
            )
            if ctx.guild:
                owner_embed.add_field(
                    name="Guild",
                    value=ctx.guild
                )
            owner_embed.add_field(
                name="Channel",
                value=f'#{ctx.channel}'
            )
            owner_embed.add_field(
                name="Cog",
                value=f"{ctx.cog}"
            )
            owner_embed.add_field(
                name="Command",
                value=f'```\n{ctx.message.content}\n```'
            )

            # if e.original:
            #    owner_embed.add_field(
            #        name='original',
            #        value=f"```py\n{e.original}\n```",
            #        inline=False
            #    )

            await self.bot.appinfo.owner.send(content="", embed=owner_embed)

            for line in traceback_msg.splitlines():  # Create traceback pages
                self.paginator.add_line(line)

            while len(self.paginator.pages):  # Send paginated traceback
                await self.bot.appinfo.owner.send(content=self.paginator.pages.pop(0))

            print(traceback_msg)

        else:
            log.info(f"{ctx.author} loaded cog '{cog.replace('cogs.', '')}'.")
            embed = discord.Embed(
                description=f"Cog `{cog.replace('cogs.', '')}` loaded.",
                colour=discord.Colour.green())
            # await ctx.send('**`SUCCESS`**')
        await ctx.send(content='', embed=embed)

    @commands.command(name='unload', hidden=True)
    @commands.is_owner()
    async def cog_unload(self, ctx, *, cog: str):
        """Command which Unloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        if not cog.startswith("cogs"):
            cog = 'cogs.' + cog
        try:
            self.bot.unload_extension('bot.' + cog)
        except Exception as e:
            log.error(f"{ctx.author} failed to unload {cog}.")
            # await ctx.send(
            # '**`ERROR:`** {} - {}'.format(type(e).__name__, e))
            embed = discord.Embed(
                title=f"Failed to unload {cog} cog.",
                description=f'{type(e).__name__} - {e}',
                colour=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                description='Cog unloaded.',
                colour=discord.Colour.green())
            log.info(f"{ctx.author} unloaded {cog}.")
            # await ctx.send('**`SUCCESS`**')
        await ctx.send(content='', embed=embed)

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def cog_reload(self, ctx, *, cog: str):
        """
        Command which Reloads a Module.
        Remember to use dot path. e.g: cogs.owner
        """

        if not cog.startswith("cogs"):
            cog = 'cogs.' + cog
        try:
            self.bot.unload_extension('bot.' + cog)
            self.bot.load_extension('bot.' + cog)
        except Exception as e:
            log.error(f"{ctx.author} failed to load {cog}.")

            embed = discord.Embed(
                title=f"Failed to reload {cog} cog.",
                description=f'{type(e).__name__} - {e}',
                colour=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                description='Cog reloaded.',
                colour=discord.Colour.green())
            # await ctx.send('**`SUCCESS`**')
        await ctx.send(content='', embed=embed)

    @commands.command(name='listcogs', hidden=True, aliases=['cogslist'])
    @commands.is_owner()
    async def cog_list(self, ctx):
        """
        Command which List loaded Modules.
        """

        await ctx.send(
            '```\n' + ", ".join(
                [ext.split(".")[2] for ext in ctx.bot.extensions]
            ) + '\n```')


def setup(bot):
    bot.add_cog(OwnerCog(bot))
