import logging

import aiohttp
import discord
from discord.ext import commands

import bot.scrapper.rcdb as rcdb
from bot.constants import Channels, Roles
from bot.decorators import in_channel, with_role
from bot.utils.embedconverter import build_embed


log = logging.getLogger(__name__)


class RollerCoasters:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rcdb", aliases=[])
    # @commands.guild_only()
    # @with_role(Roles.pilotes)
    async def rcdb_infos(self, ctx, search):
        """Retrieve infos from rcdb"""
        # Check if RCDB is online
        async def rcdb_online():
            async with aiohttp.ClientSession() as session:
                async with session.get('https://rcdb.com') as r:
                    if r.status == 200:
                        return True
                    log.error("RCDB website offline, aborting.")
                    return False

        if rcdb_online():
            # Create webdriver
            driver = rcdb.build_driver(
                headless=True, log_path='chromedriver.log')
            coaster_infos = await self.bot.loop.run_in_executor(
                None, rcdb.build_coaster, driver, search
            )

            embed = await build_embed(
                ctx,
                title=coaster_infos.pop('name'),
                colour='blue'
            )
            for k, v in coaster_infos.items():
                if type(v) is str:
                    embed.add_field(name=k, value=v)
                elif type(v) is list:
                    embed.add_field(name=k, value=', '.join(v))

            await ctx.send(embed=embed)

        else:
            """If rcdb offline"""
            embed = await discord.Embed(
                title="RCDB Offline :(",
                description="Va falloir attendre mon mignon",
                colour=discord.Colour.red()
            )
            embed.set_author(icon_url=self.bot.user.avatar_url,
                             name=str(self.bot.user.name)
                             )
            await ctx.send(content='', embed=embed)


def setup(bot):
    bot.add_cog(RollerCoasters(bot))
