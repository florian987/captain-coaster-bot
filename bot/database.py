import asyncio
import asyncpg
import logging
import os
from pathlib import Path
from typing import List

import yaml
from yaml.constructor import ConstructorError

from bot.constants import Postgres


log = logging.getLogger(__name__)

async def connect():
    return await asyncpg.connect(user=Postgres.user, password=Postgres.password,
                                 database=Postgres.database, host=Postgres.host)

#async def disconnect():


async def run():
    conn = await asyncpg.connect(user="postgres", password="example",
                                 database="discordbot", host="localhost")
    values = await conn.fetch('''SELECT * FROM coaster_games''')
    print(values)
    await conn.close()

#loop = asyncio.get_event_loop()
#loop.run_until_complete(run())

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())

# DROP TABLE IF EXISTS "coaster_games";
# CREATE TABLE "public"."coaster_games" (
#     "GAMEID" character(30) NOT NULL,
#     "START" timestamp DEFAULT now() NOT NULL,
#     "END" timestamp NOT NULL,
#     "REQUESTER" bigint NOT NULL,
#     "GUILD" bigint NOT NULL,
#     "CHANNEL" bigint NOT NULL,
#     "COASTER" character varying(64) NOT NULL,
#     "PARK" character varying(64) NOT NULL,
#     "WINNER" bigint NOT NULL
# ) WITH (oids = false);