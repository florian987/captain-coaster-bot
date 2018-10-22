import logging

import aiohttp
import asyncio
import discord
import json
import random
import unidecode
import re
from discord import errors
from discord.ext import commands
from discord.ext.commands import Context, group
from fuzzywuzzy import fuzz

import scrapper.rcdb as rcdb
from bot.utils.discord_emojis import emojis as dis_emojis
from bot.constants import Keys, URLs, CC_TAUNT
from bot.utils.embedconverter import build_embed
from bot.decorators import in_any_channel_guild


log = logging.getLogger(__name__)


class RollerCoasters:
    """Interract with Captain Coaster API"""

    HEADERS = {'X-AUTH-TOKEN': Keys.captaincoaster}

    def __init__(self, bot):
        self.bot = bot
        self.std_emojis = dis_emojis()
        self.game_in_progress = False
        self.game_in_progress = {}
        self.mapping = {
            'materialType': 'Type',
            'speed': 'Vitesse',
            'height': 'Hauteur',
            'length': 'Longueur',
            'inversionsNumber': "Inversions",
            'manufacturer': 'Constructeur',
            'status': 'Etat',
            'park': "Parc",
            'rank': "Classement",
            'validDuels': "Duels",
            "totalRatings": "Votes",
            "score": "Score"
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
            async with session.get(url, headers=self.HEADERS) as r:
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
    @in_any_channel_guild(473760830505091072, 502418016949239809, 249216021599223808)
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
    async def cc_play(self, ctx, difficulty='easy'):
        """
        Quizz avec les images de CC.

        Une pertinence de 80% est nécessaire pour avoir une réponse validée.
        """

        # Configuration
        TIMEOUT = 120.0
        park_found = False
        coaster_found = False

        lvl_map = {
            'easy': '[gt]=10',
            'medium': '[between]=1..10',
            'hard': '[lt]=1'
        }

        # Check functions
        def normalize(string):
            return re.sub("\(.*?\)", "", unidecode.unidecode(string.lower().strip().replace("'", "").replace("-", "").replace(":", "")))
            #return re.sub("\(.*?\)", "", unidecode.unidecode(string.lower().strip().replace(' ', '').replace("'", "").replace("-", "").replace(":", "")))

        def park_answers(m):
            return fuzz.ratio(normalize(m.content), normalize(coaster['park']['name'])) >= 80

        def coaster_answers(m):
            return fuzz.ratio(normalize(m.content), normalize(coaster['name'])) >= 80

        def both_answers(m):
            return park_answers(m) or coaster_answers(m)

        def on_the_park_way(m):
            return 50 <= fuzz.ratio(normalize(m.content), normalize(coaster['park']['name'])) < 80

        def on_the_coaster_way(m):
            return 50 <= fuzz.ratio(normalize(m.content), normalize(coaster['park'])) < 80

        # Game
        

        if self.is_online(URLs.captain_coaster):
            
            if ctx.guild is not None:
                await ctx.message.delete()
                
            if ctx.channel.id in self.game_in_progress and self.game_in_progress[ctx.channel.id]:
                log.info(f"{ctx.message.author} tried to start a game in {ctx.channel} but a game is already running.")
                try:
                    await ctx.message.author.send(content="Une partie est déjà en cours mon mignon.")
                except errors.Forbidden:
                    pass                
            
            if difficulty not in lvl_map:
                await ctx.send(content="Une erreur de frappe ? On lance en mode facile.")
                difficulty = 'easy'

            else:
                self.game_in_progress[ctx.channel.id] = True

                # Build images list
                base_infos = await self.json_infos(f'{URLs.captain_coaster}/api/coasters?totalRatings{lvl_map[difficulty]}&mainImage[exists]=true')
                last_page = base_infos["hydra:view"]["hydra:last"].split('=')[-1:][0]
                chosen_page = await self.json_infos(f'{URLs.captain_coaster}/api/coasters?totalRatings{lvl_map[difficulty]}&mainImage[exists]=true&page={random.randint(1, int(last_page))}')
                coaster = chosen_page["hydra:member"][random.randint(1, len(chosen_page["hydra:member"])) - 1]
                coaster_imgs = await self.json_infos(f'{URLs.captain_coaster}/api/images?coaster={coaster["id"]}')
                rdm_image = coaster_imgs["hydra:member"][random.randint(1, len(coaster_imgs["hydra:member"])) - 1]["path"]

                log.info(f"Game started by {ctx.message.author} in {ctx.channel}."
                         f"Coaster: {coaster['name']}, Parc: {coaster['park']['name']}")

                embed_question = await build_embed(
                    ctx,
                    title=f"De quel coaster et quel parc s'agit-il ? ({difficulty})",
                    colour='gold',
                    img=f"{URLs.captain_coaster}/images/coasters/{rdm_image}",
                    author_icon=ctx.author.avatar_url,
                    author_name=ctx.author.name
                )

                # Send image to discord
                question = await ctx.send(embed=embed_question)

                while not park_found or not coaster_found:

                    # ANSWER
                    try:
                        msg = await self.bot.wait_for(
                            'message', timeout=TIMEOUT, check=both_answers)

                    except asyncio.TimeoutError:
                        embed = await build_embed(
                            ctx,
                            colour='red',
                            title=random.choice(CC_TAUNT),
                            description=f"Il s'agissait de {coaster['name']} se trouvant à {coaster['park']['name']}")
                        await ctx.send(embed=embed)
                        break

                    else:
                        if coaster_answers(msg):
                            coaster_found = True                            
                            titre = f"Bravo {msg.author.name}, tu as trouvé le coaster!"
                            descr = coaster['name']
                            embed_question = embed_question.add_field(name="Coaster", value=f"{coaster['name']} ({msg.author.name})")
                            log.info(f"{ctx.message.author} found coaster {coaster['name']}.")
                            if not park_found:
                                titre += "\nSaurez vous trouver son Parc ?"
                            # TODO validate
                            else:
                                embed_question.colour = 'green'

                        else:
                            park_found = True
                            titre = f"Bravo {msg.author.name}, tu as trouvé le Parc!"
                            descr = coaster['park']['name']
                            embed_question = embed_question.add_field(name="Parc", value=f"{coaster['park']['name']} ({msg.author.name})")
                            log.info(f"{ctx.message.author} found park  {coaster['park']['name']}.")
                            if not coaster_found:
                                titre += "\nSaurez vous trouver le coaster ?"
                            # TODO validate
                            else:
                                embed_question.colour = 'green'

                        # Send 'bravo' embed
                        embed = await build_embed(ctx, colour='green', title=titre, descr=descr)
                        await ctx.send(embed=embed)

                        # Edit original embed
                        await question.edit(embed=embed_question)

                    # HINT Park
                    if not park_found:
                        try:
                            msg = await self.bot.wait_for(
                                'message',
                                timeout=TIMEOUT,
                                check=on_the_park_way)

                        except asyncio.TimeoutError:
                            pass

                        except:
                            await ctx.send(content="Ca chauffe!")

                    # HINT Coaster
                    if not coaster_found:
                        try:
                            msg = await self.bot.wait_for(
                                'message',
                                timeout=TIMEOUT,
                                check=on_the_coaster_way)

                        except asyncio.TimeoutError:
                            pass

                        except:
                            await ctx.send(content="Ca chauffe!")

                log.info(f"Game ended in {ctx.channel}")
                self.game_in_progress[ctx.channel.id] = False



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
            embed.set_or(
                icon_url=self.bot.user.avatar_url, name=str(self.bot.user.name))
            await ctx.send(content='', embed=embed)


def setup(bot):
    bot.add_cog(RollerCoasters(bot))
