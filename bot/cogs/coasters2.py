import logging

import aiohttp
import asyncio
import discord
import json
import random
from discord import errors
from discord.ext import commands
from discord.ext.commands import Context, group

import scrapper.rcdb as rcdb
from bot.utils.discord_emojis import emojis as dis_emojis
from bot.constants import Keys, URLs, CC_TAUNT
from bot.utils.embedconverter import build_embed
from bot.decorators import in_any_channel_or_dm


log = logging.getLogger(__name__)


class RollerCoasters:
    def __init__(self, bot):
        self.bot = bot
        self.std_emojis = dis_emojis()
        self.mapping = {
            'materialType': 'Type',
            'speed': 'Vitesse',
            'height': 'Hauteur',
            'length': 'Longueur',
            'inversionsNumber': "Inversions",
            'manufacturer': 'Constructeur',
            'status': 'Etat',
            'park': "Parc",
            'rank': "Classement"
        }

    async def is_online(self, site):
        async with aiohttp.ClientSession() as session:
            async with session.get(site) as r:
                if r.status != 503:
                    return True
                log.error(f'Requested website {site} is offline.')
                return False

    async def json_infos(self, url):
        async with aiohttp.ClientSession() as session:
            headers = {'X-AUTH-TOKEN': f'{Keys.captaincoaster}'}
            async with session.get(url, headers=headers) as r:
                return await r.json()

    async def coaster_embed(self, ctx, coaster_json):
        """
        Helper method to build Coasters infos from CC json
        """
        coaster_json.pop('id')  # Remove useless id info

        embed = await build_embed(
            ctx,
            title=coaster_json.pop('name'),
            colour='blue',
            author_icon=ctx.author.avatar_url,
            author_name=ctx.author.name
        )

        if coaster_json['mainImage'] is not None:
            embed.set_thumbnail(
                url=f"{URLs.captain_coaster}/images/coasters/{coaster_json.pop('mainImage')['path']}")

        for k, v in coaster_json.items():  # Fields mapping
            if k in self.mapping:
                k = self.mapping[k]
            if type(v) == int or type(v) == str and not k.startswith('@'):  # Add fields to embed
                embed.add_field(name=k, value=v)
            elif type(v) == dict:
                embed.add_field(name=k, value=v['name'])
        return embed

    @group(name='cc', aliases=['captaincoaster'], invoke_without_command=True)
    @in_any_channel_or_dm(473760830505091072, 502418016949239809)
    async def cc_group(self, ctx: Context, *, query=None):
        """
        Retrieve infos from Captain Coaster
        """

        if query is None:
            await ctx.invoke(self.bot.get_command("help"), "cc")
        else:
            await ctx.invoke(self.bot.get_command("cc search"), search=query)

    @cc_group.command(name="list", aliases=[])
    async def cc_list(self, ctx):
        """
        Get coasters list from Captain Coaster
        """
        if self.is_online(URLs.captain_coaster):
            json_paginator = commands.Paginator(prefix="```json", suffix="```")
            json_body = await self.json_infos(f'{URLs.captain_coaster}/api/coasters')
            for coaster in json_body['hydra:member']:
                json_paginator.add_line(json.dumps(coaster))
            for page in json_paginator.pages:
                await ctx.message.author.send(content=page)

    @cc_group.command(name="search", aliases=['infos', 'getinfos', 'get_infos'])
    async def cc_search(self, ctx, *, search):
        """
        Search coaster infos from Captain Coaster
        """

        if self.is_online(URLs.captain_coaster):
            json_body = await self.json_infos(
                f'{URLs.captain_coaster}/api/coasters?name={search}')
            if json_body['hydra:totalItems'] == 1:
                embed = await self.coaster_embed(
                    ctx, json_body['hydra:member'][0])
                if ctx.guild is not None:
                    try:
                        await ctx.message.delete()
                    except errors.Forbidden:
                        print('-' * 12)
                        print('JAIPALDROI')
                        pass
                await ctx.send(embed=embed)

            elif 1 < json_body['hydra:totalItems'] <= 20:
                emojis_association = {}
                # Build emojis list
                guild_emojis = [(e for e in self.bot.emojis if e.guild == ctx.guild and not e.managed)]
                allowed_emojis = guild_emojis + self.std_emojis

                # Create selection embed
                embed = await build_embed(
                    ctx, title="Tu parles de quel coaster ?", colour='gold')
                for coaster in json_body['hydra:member']:
                    # Pick a random emoji and add choice to embed/dict
                    chosen_emoji = random.choice([e for e in allowed_emojis if e not in emojis_association.keys()])
                    embed.add_field(
                        name=f"{coaster['name']} ({coaster['park']['name']})",
                        value=chosen_emoji, inline=True)
                    emojis_association[chosen_emoji] = coaster['id']
                message = await ctx.send(embed=embed)  # Send embed

                # Add reaction to embed
                for emoji in emojis_association.keys():
                    await message.add_reaction(emoji)

                def sender_react(reaction, user):
                    return user == ctx.message.author and reaction.emoji in emojis_association.keys()

                try:
                    reaction, user = await self.bot.wait_for(
                        'reaction_add', timeout=10.0, check=sender_react)
                except asyncio.TimeoutError:
                    await message.delete()
                else:
                    json_body = await self.json_infos(
                        f'{URLs.captain_coaster}/api/coasters?id={emojis_association[reaction.emoji]}')
                    embed = await self.coaster_embed(
                        ctx, json_body['hydra:member'][0])
                    if ctx.guild is not None:
                        try:
                            await ctx.message.delete()
                        except errors.Forbidden:
                            print('-' * 12)
                            print('JAIPALDROI')
                            pass

                    await message.delete()
                    await ctx.send(embed=embed)

            elif json_body['hydra:totalItems'] > 20:
                await ctx.send(
                    content=f"Trop de résultats ({json_body['hydra:totalItems']}).")
            else:
                await ctx.send(content="Aucun coaster trouvé.")

    @cc_group.command(name="game", aliases=['play', 'jeu'])
    async def cc_play(self, ctx):
        """
        Get a random image from CC and users should guess it
        """
        if self.is_online(URLs.captain_coaster):

            # Build images list
            datas = await self.json_infos(f'{URLs.captain_coaster}/api/images')
            random_page = random.randint(
                1, int(datas["hydra:view"]["hydra:last"].split('=')[1]))
            datas = await self.json_infos(
                f'{URLs.captain_coaster}/api/images?page={random_page}')

            # Pick random image
            chosen_image = random.choice(datas["hydra:member"])
            coaster_infos = await self.json_infos(
                URLs.captain_coaster + chosen_image['coaster'])

            # Send image to discord
            await ctx.send(embed=await build_embed(
                ctx,
                title="De quel coaster et quel parc s'agit-il ?",
                colour='gold',
                img=f"{URLs.captain_coaster}/images/coasters/{chosen_image['path']}"
            ))

            # Set valid answers
            valid_coaster_answers = [
                coaster_infos['name'].lower(),
                coaster_infos['name'].replace(' ', '').lower()
            ]

            valid_park_answers = [
                coaster_infos['park']['name'].lower(),
                coaster_infos['park']['name'].replace(' ', '').lower()
            ]

            def both_answers(m):
                return m.content.lower() in valid_park_answers or m.content.lower() in valid_coaster_answers

            def park_answers(m):
                return m.content.lower() in valid_park_answers

            def coaster_answers(m):
                return m.content.lower() in valid_coaster_answers

            while valid_park_answers and valid_coaster_answers:
                try:
                    msg = await self.bot.wait_for(
                        'message', timeout=300.0, check=both_answers)

                except asyncio.TimeoutError:
                    embed = await build_embed(
                        ctx,
                        colour='red',
                        title=random.choice(CC_TAUNT),
                        description=f"Il s'agissait de {coaster_infos['name']} se trouvant à {coaster_infos['park']['name']}")
                    await ctx.send(embed=embed)
                    break
                    
                else:
                    if coaster_answers(msg):                        
                        titre = f'Bravo {msg.author}, tu as trouvé le nom du coaster!"
                        if not valid_park_answers:
                            titre += " Saurez vous trouver sa localisation ?'
                        
                    else:
                        titre = f'Bravo {msg.author}, tu as trouvé le Parc!'
                        if not valid_park_answers:
                            titre += " Saurez vous trouver son nom ?'

                    embed = await build_embed(ctx, colour='green', title=titre)

                    await ctx.send(embed=embed)
                    valid_park_answers = []

            # Bravo de fin


            #await ctx.send(embed=embed)




    @commands.command(name="rcdb", aliases=[])
    @commands.guild_only()
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
            embed.set_author(
                icon_url=self.bot.user.avatar_url, name=str(self.bot.user.name))
            await ctx.send(content='', embed=embed)


def setup(bot):
    bot.add_cog(RollerCoasters(bot))
