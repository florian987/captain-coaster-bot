import logging

import aiohttp
import asyncio
import asyncpg
import datetime
import discord
import json
import random
import time
import unidecode
import re
from discord import errors
from discord.ext import commands
from discord.ext.commands import Context, group
from fuzzywuzzy import fuzz

from bot.utils.emojis import emojis
from bot.constants import Keys, CC_TAUNT, Postgres, URLs
from bot.utils.embedconverter import build_embed
from bot.decorators import in_any_channel_guild


log = logging.getLogger(__name__)


cc_api = URLs.captain_coaster
cc_cdn = URLs.captain_cdn


class RollerCoasters(commands.Cog, name='RollerCoasters Cog'):
    """Interact with Captain Coaster API"""

    HEADERS = {'Authorization': Keys.captaincoaster}
    games_in_progress = []
    mapping = {
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
        "score": "Score"}

    def __init__(self, bot):
        self.bot = bot
        self.std_emojis = emojis()
        self.bot.loop.create_task(self.init_db())
        self.lvl_map = {
            'easy': '[gt]=100',
            'medium': '[between]=30..100',
            'hard': '[lt]=30'}

    async def init_db(self):
        # Check if DB is up and exists
        for _ in range(3):
            try:
                self.db_pool = await asyncpg.create_pool(
                    host=Postgres.host,
                    database=Postgres.database,
                    user=Postgres.user,
                    password=Postgres.password,
                    command_timeout=60)
                log.debug("DB pool created")
            except ConnectionRefusedError as e:
                log.debug("Waiting for 5 seconds before retrying again")
                await asyncio.sleep(5)

        async with self.db_pool.acquire() as con:
            await con.execute(
                '''CREATE TABLE IF NOT EXISTS cc_games(
                    game_id bigint,
                    guild_id bigint,
                    channel_id bigint,
                    time int,
                    creation_date timestamp,
                    difficulty int,
                    park text,
                    coaster text,
                    park_solver_discordid bigint,
                    coaster_solver_discordid bigint,
                    park_solved_at timestamp,
                    coaster_solved_at timestamp
                );''')

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
        coaster_json.pop('id')

        embed = await build_embed(
            ctx,
            title=coaster_json.pop('name'),
            colour='blue',
            author_icon=ctx.author.avatar_url,
            author_name=ctx.author.name)

        if coaster_json['mainImage'] is not None:
            embed.set_thumbnail(
                url=f"{cc_cdn}/1440x1440/{coaster_json.pop('mainImage')['path']}")

        log.info(url);

        # Fields mapping
        for k, v in coaster_json.items():
            if k in self.mapping:
                k = self.mapping[k]
            # Add fields to embed
            if type(v) == int or type(v) == str and not k.startswith('@'):
                embed.add_field(name=k, value=v)
            elif type(v) == dict:
                embed.add_field(name=k, value=v['name'])
        return embed

    @group(name='cc', aliases=['captaincoaster'], invoke_without_command=True)
    @in_any_channel_guild(473760830505091072, 502418016949239809, 249216021599223808, 554231046992822273)
    async def cc_group(self, ctx: Context, *, query=None):
        """
        Retrieve infos from Captain Coaster
        """

        if query is None:
            await ctx.invoke(self.bot.get_command("help"), "cc")
        else:
            await ctx.invoke(self.bot.get_command("cc search"), search=query)

    @commands.is_owner()
    @cc_group.command(name="listgames")
    async def cc_listgames(self, ctx):
        await ctx.message.author.send(content=f"Parties en cours.\n{self.games_in_progress}")

    @cc_group.command(name="list", aliases=[])
    async def cc_list(self, ctx):
        """
        Get coasters list from Captain Coaster
        """
        if self.is_online(cc_api):
            json_paginator = commands.Paginator(prefix="```json", suffix="```")
            json_body = await self.json_infos(f'{cc_api}/api/coasters')
            for coaster in json_body['hydra:member']:
                json_paginator.add_line(json.dumps(coaster))
            for page in json_paginator.pages:
                await ctx.message.author.send(content=page)

    @cc_group.command(name="search", aliases=['infos', 'getinfos', 'get_infos'])
    async def cc_search(self, ctx, *, search):
        """
        Search coaster infos from Captain Coaster
        """

        if self.is_online(cc_api):
            json_body = await self.json_infos(
                f'{cc_api}/api/coasters?name={search}')
            if json_body['hydra:totalItems'] == 1:
                embed = await self.coaster_embed(
                    ctx, json_body['hydra:member'][0])
                if ctx.guild is not None:
                    try:
                        await ctx.message.delete()
                    except errors.Forbidden:
                        print('---- No permissions to delete message')
                        pass
                await ctx.send(embed=embed)

            # TODO Rework this part with in emojis
            #
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

                message = await ctx.send(embed=embed)

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
                        f'{cc_api}/api/coasters?id={emojis_association[reaction.emoji]}')
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

    @commands.guild_only()
    @cc_group.command(name="score", aliases=['points'])
    async def cc_score(self, ctx, *, player: discord.User = None):
        """
        Get player score
        """

        await ctx.message.delete()

        if player is None:
            player = ctx.message.author

        async with self.db_pool.acquire() as con:

            park_points = await con.fetchval(
                f'''SELECT sum(difficulty) from cc_games
                WHERE park_solver_discordid = {player.id}''')

            coaster_points = await con.fetchval(
                f'''SELECT sum(difficulty) from cc_games
                WHERE coaster_solver_discordid = {player.id}''')

            if isinstance(park_points, int) and isinstance(coaster_points, int):
                points = park_points + coaster_points
            elif isinstance(park_points, int) and not isinstance(coaster_points, int):
                points = park_points
            elif not isinstance(park_points, int) and isinstance(coaster_points, int):
                points = coaster_points
            else:
                points = "Tu n'es pas encore classé."

            embed = await build_embed(
                ctx,
                title="**Score**",
                colour='blue',
                author_icon=player.avatar_url,
                author_name=player.name)

            embed.add_field(name="Points", value=points)

        await ctx.send(embed=embed)

    @commands.guild_only()
    @cc_group.command(name="levels", aliases=["lvl", "level", "lvls", "niveaux"])
    async def cc_levels(self, ctx):
        """Get current levels"""

        await ctx.message.delete()

        mbd = await build_embed(
            ctx,
            title=f"Levels",
            colour='blue',
            author_icon=ctx.author.avatar_url,
            author_name=ctx.author.name
        )

        for k, v in self.lvl_map.items():
            r = await self.json_infos(
                f'{cc_api}/api/coasters?totalRatings{self.lvl_map[k]}&mainImage[exists]=true')
            mbd.add_field(name=k, value=f'{v} ({r["hydra:totalItems"]})', inline=False)

        await ctx.send(embed=mbd)

    @commands.guild_only()
    @cc_group.command(name="classement", aliases=['leaderboard', 'top'])
    async def cc_leaderboard(self, ctx, *, limit: int = 10, hardlimit: int = 25):
        """Get Leaderboard"""

        await ctx.message.delete()

        if limit > hardlimit:
            limit = hardlimit

        embed = await build_embed(
            ctx,
            title="**Leaderboard**",
            colour='blue',
            author_icon=ctx.author.avatar_url,
            author_name=ctx.author.name,
            thumbnail='https://image.flaticon.com/icons/png/512/262/262831.png')

        async with self.db_pool.acquire() as con:
            r = await con.fetch(
                f'''
                select discord_uid, sum(dif) as score
                from (select coaster_solver_discordid as discord_uid, sum(difficulty) as dif from cc_games where coaster_solved_at > 'now'::timestamp - '1 month'::interval group by discord_uid
                union
                select park_solver_discordid as discord_uid, sum(difficulty) as dif from cc_games where park_solved_at > 'now'::timestamp - '1 month'::interval group by discord_uid)
                as alias where discord_uid is not null group by discord_uid order by score desc limit {limit};
                ''')

            count = 0
            while count < len(r):
                try:  # Handle player who left the server
                    nickname = ctx.guild.get_member(r[count]['discord_uid']).display_name
                except AttributeError as e:
                    log.debug("Error leaderboard")
                    log.debug(e)
                    nickname = "Unknown player"

                embed.add_field(
                    name=f"{str(count + 1)} - {nickname} ({str(r[count]['score'])})",
                    value="‌‌ ",
                    inline=False)

                count += 1

        await ctx.send(embed=embed)

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
        min_match = 80

        int_lvl_map = {
            'easy': 1,
            'medium': 2,
            'hard': 3}

        # Check functions
        def normalize(string):
            return re.sub("\(.*?\)", "", unidecode.unidecode(string.lower().strip().replace("'", "").replace("-", "").replace(":", "")))

        def park_answers(m):
            return fuzz.ratio(normalize(m.content), normalize(coaster['park']['name'])) >= min_match

        def coaster_answers(m):
            return fuzz.ratio(normalize(m.content), normalize(coaster['name'])) >= min_match

        def on_park_way(m):
            return 60 <= fuzz.ratio(normalize(m.content), normalize(coaster['park']['name'])) < min_match

        def on_coaster_way(m):
            return 60 <= fuzz.ratio(normalize(m.content), normalize(coaster['name'])) < min_match

        # Game
        if await self.is_online(cc_api):

            if ctx.guild is not None:
                await ctx.message.delete()

            if ctx.channel.id in self.games_in_progress:
                log.info(f"{ctx.message.author} tried to start a game in {ctx.channel} but a game is already running.")
                try:
                    await ctx.message.author.send(content="Une partie est déjà en cours !")
                except errors.Forbidden:
                    pass
                finally:
                    return

            if difficulty not in self.lvl_map:
                await ctx.send(content="Une erreur de frappe ? On lance en mode facile.")
                difficulty = 'easy'

            else:
                self.games_in_progress.append(ctx.channel.id)

                # Build images list
                base_infos = await self.json_infos(f'{cc_api}/api/coasters?totalRatings{self.lvl_map[difficulty]}&mainImage[exists]=true')
                if "hydra:last" in base_infos["hydra:view"]:
                    last_page = base_infos["hydra:view"]["hydra:last"].split('=')[-1:][0]
                else:
                    last_page = 1
                page_id = random.randint(1, int(last_page))
                chosen_page = await self.json_infos(f'{cc_api}/api/coasters?totalRatings{self.lvl_map[difficulty]}&mainImage[exists]=true&page={page_id}')
                coaster_id = random.randint(1, len(chosen_page["hydra:member"])) - 1
                coaster = chosen_page["hydra:member"][coaster_id]
                coaster_imgs = await self.json_infos(f'{cc_api}/api/images?coaster={coaster["id"]}')
                rdm_image = coaster_imgs["hydra:member"][random.randint(1, len(coaster_imgs["hydra:member"])) - 1]["path"]

                log.info(f"Game started by {ctx.message.author} in {ctx.channel}.\n"
                         f"Coaster: {coaster['name']}, Parc: {coaster['park']['name']} - (Page: {page_id}, CoasterID: {coaster_id})")

                embed_question = await build_embed(
                    ctx,
                    title=f"De quel coaster et quel parc s'agit-il ? ({difficulty})",
                    colour='gold',
                    img=f"{cc_cdn}/1440x1440/{rdm_image}",
                    author_icon=ctx.author.avatar_url,
                    author_name=ctx.author.name)

                # Send image to discord
                question = await ctx.send(embed=embed_question)

                # Insert party in DB
                game_id = hash(int(ctx.channel.id) + int(time.time()))

                async with self.db_pool.acquire() as con:
                    await con.execute(
                            '''INSERT INTO cc_games(
                                game_id, guild_id, channel_id, time, creation_date, difficulty, park, coaster
                            )
                            VALUES($1, $2, $3, $4, $5, $6, $7, $8)''',
                        game_id,
                        ctx.guild.id,
                        ctx.channel.id,
                        time.time(),
                        datetime.datetime.now(),
                        int_lvl_map[difficulty],
                        coaster['park']['name'],
                        coaster['name'])

                while not park_found or not coaster_found:

                    # ANSWER
                    try:
                        msg = await self.bot.wait_for(
                            'message', timeout=TIMEOUT)

                    except asyncio.TimeoutError:
                        embed = await build_embed(
                            ctx,
                            colour='red',
                            title=random.choice(CC_TAUNT),
                            description=f"Il s'agissait de {coaster['name']} se trouvant à {coaster['park']['name']}")
                        await ctx.send(embed=embed)

                        # Change original embed
                        if coaster_found or park_found:
                            embed_question.colour = discord.Colour.dark_red()
                        else:
                            embed_question.colour = discord.Colour.red()
                        await question.edit(embed=embed_question)
                        break

                    else:
                        if (coaster_answers(msg) and not coaster_found) or (park_answers(msg) and not park_found):
                            if coaster_answers(msg) and not coaster_found:
                                coaster_found = True
                                titre = f"Bravo {msg.author.name}, tu as trouvé le coaster!"
                                descr = coaster['name']
                                embed_question = embed_question.add_field(name="Coaster", value=f"{coaster['name']} ({msg.author.name})")
                                log.info(f"{ctx.message.author} found coaster {coaster['name']}.")
                                async with self.db_pool.acquire() as con:
                                    await con.execute(
                                        f'''UPDATE cc_games SET (
                                            park_solver_discordid,
                                            park_solved_at
                                        ) = (
                                            {msg.author.id},
                                            now()
                                        ) where game_id = {game_id}''')
                                if not park_found:
                                    titre += "\nSaurez vous trouver son Parc ?"
                                else:
                                    embed_question.colour = discord.Colour.green()

                            else:
                                park_found = True
                                titre = f"Bravo {msg.author.name}, tu as trouvé le Parc!"
                                descr = coaster['park']['name']
                                embed_question = embed_question.add_field(name="Parc", value=f"{coaster['park']['name']} ({msg.author.name})")
                                log.info(f"{ctx.message.author} found park  {coaster['park']['name']}.")
                                async with self.db_pool.acquire() as con:
                                    await con.execute(
                                        f'''
                                        UPDATE cc_games SET
                                        (coaster_solver_discordid,  coaster_solved_at)
                                        = ({msg.author.id}, now())
                                        where game_id = {game_id}
                                        '''
                                    )
                                if not coaster_found:
                                    titre += "\nSaurez vous trouver le coaster ?"
                                else:
                                    embed_question.colour = discord.Colour.green()

                            # Send 'bravo' embed
                            embed = await build_embed(ctx, colour='green', title=titre, description=descr)
                            await ctx.send(embed=embed)

                            # Edit original embed
                            await question.edit(embed=embed_question)

                        # HINT
                        elif (on_coaster_way(msg) and not coaster_found) or (on_park_way(msg) and not park_found):
                            await ctx.send(content="Ca chauffe!")

                log.info(f"Game ended in {ctx.channel}")
                self.games_in_progress.remove(ctx.channel.id)


def setup(bot):
    bot.add_cog(RollerCoasters(bot))
