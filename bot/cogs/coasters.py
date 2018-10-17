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
        self.mapping = {
            'materialType': 'Matériaux',
            'speed': 'Vitesse',
            'height': 'Hauteur',
            'length': 'Longueur'
            'inversionsNumber': "Nbre d'inversion",
            'manufacturer': 'Constructeur',
            'status': 'Etat'
        }

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
                    if len(json_body['hydra:member']) == 1:
                        for coaster_infos in json_body['hydra:member']:
                            coaster_infos.pop('id')
                            embed = await build_embed(
                                ctx,
                                title=coaster_infos.pop('name'),
                                colour='blue',
                                # url=cc + '/' + coaster_infos.pop('@id')
                            )
                            for k, v in coaster_infos.items():
                                # Fields mapping
                                if k in self.mapping:
                                    k = self.mapping[k]

                                # Add fields to embed
                                if type(v) == int or type(v) == str and not k.startswith('@'):
                                    embed.add_field(name=k, value=v)
                                elif type(v) == dict:
                                    embed.add_field(name=k, value=v['name'])

                            # await ctx.message.author.send(embed=embed)
                            message = await ctx.send(embed=embed)
                    # elif len(json_body['hydra:member']) > 1:
                    #     # Build emojis list
                    #     used_emojis = []
                    #     guild_emojis = [(e for e in self.bot.emojis if e.guild == ctx.guild and not e.managed)]
                    #     allowed_emojis = guild_emojis + self.std_emojis
# 
                    #     embed = await build_embed(ctx, title="Tu parles de quel coaster ?", colour='gold')
# 
                    #     for coaster in json_body['hydra:member']:
                    #         chosen_emoji = random.choice([e for e in allowed_emojis if e not in used_emojis])
                    #         embed.add_field(
                    #             name=f"{coaster['name']} ({coaster['park']})", value=chosen_emoji, inline=True)
                    #         used_emojis.append(chosen_emoji)
# 
                    #     message = await ctx.send(embed=embed)
# 
                    #     def check(m):
                    #         return m.author == ctx.message.author and m.channel == channel
# 
                    else:
                        await ctx.send(content="Aucun coaster trouvé")

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
