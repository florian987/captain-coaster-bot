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

async def run():
    conn = await asyncpg.connect(user=Postgres.user, password=Postgres.password,
                                 database=Postgres.database, host=Postgres.host)
    values = await conn.fetch('''SELECT * FROM mytable''')
    await conn.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(run())