import logging

import aiohttp
import discord
import json
from discord.ext import commands
from discord.ext.commands import Context, group

import scrapper.rcdb as rcdb
from bot.constants import Keys
from bot.utils.embedconverter import build_embed


log = logging.getLogger(__name__)


class RollerCoasters:
    def __init__(self, bot):
        self.bot = bot

    async def is_online(self, site):
        async with aiohttp.ClientSession() as session:
            async with session.get(site) as r:
                if r.status != 503:
                    return True
                log.error(f'Requested website {site} is offline.')
                return False


    @group(name='cc', aliases=['captaincoaster'], invoke_without_command=True)
    # @commands.guild_only()
    async def cc_group(self, ctx: Context, *, query=None):
        """
        Retrieve infos from Captain Coaster
        """

        if query is None:
            await ctx.invoke(self.bot.get_command("help"), "cc")
        else:
            await ctx.invoke(self.bot.get_command("cc search"), search=query)

    @cc_group.command(name="list", aliases=[])
    # @commands.guild_only()
    async def cc_list(self, ctx):
        """Get coasters list from Captain Coaster"""
        cc = 'https://captaincoaster.com'
        if self.is_online(cc):            
            json_paginator = commands.Paginator(prefix="```json", suffix="```")
            async with aiohttp.ClientSession() as session:
                headers = {'X-AUTH-TOKEN': f'{Keys.captaincoaster}'}
                async with session.get(f'{cc}/api/coasters', headers=headers) as r:
                    json_body = await r.json()
                    for coaster in json_body['hydra:member']:
                        json_paginator.add_line(json.dumps(coaster))
                    for page in json_paginator.pages:
                        await ctx.message.author.send(content=page)

    @cc_group.command(name="search", aliases=['infos', 'getinfos', 'get_infos'])
    # @commands.guild_only()
    async def cc_search(self, ctx, *, search):
        """Search coaster infos from Captain Coaster"""
        cc = 'https://captaincoaster.com'
        if self.is_online(cc):
            async with aiohttp.ClientSession() as session:
                headers = {'X-AUTH-TOKEN': f'{Keys.captaincoaster}'}
                async with session.get(
                    f'{cc}/api/coasters?name={search}',
                    headers=headers
                ) as r:
                    json_body = await r.json()
                    for coaster_infos in json_body['hydra:member']:
                        embed = await build_embed(
                            ctx,
                            title=coaster_infos.pop('name'),
                            colour='blue'
                        )
                        for k, v in coaster_infos.items():
                            if type(v) == int or type(v) == str and not k.startswith('@'):
                                embed.add_field(name=k, value=v)
                            elif type(v) == dict:
                                embed.add_field(name=k, value=v['name'])

                        await ctx.message.author.send(embed=embed)

    @commands.command(name="rcdb", aliases=[])
    @commands.guild_only()
    # @with_role(Roles.pilotes)
    async def rcdb_infos(self, ctx, search):
        """Try to retrieve infos from rcdb (experimental)"""

        if self.is_online('https://rcdb.com'):
            # Create webdriver
            driver = rcdb.build_driver(
                headless=True, log_path='logs/chromedriver.log')
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
