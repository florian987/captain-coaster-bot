## Selenium
Selenium a besoin de capabilities admin.
```sh
--cap-add=SYS_ADMIN
```

## CaptainCoaster
### Postgres

| Name | Type | exemple |
|---|---|---|
| GameID | SERIAL | 1 |
| Created_at | timestamp | 2019-03-10 14:00:27.927209 |
| Difficulty | int | 3 |
| Park | str | Parc Astérix |
| Coaster | str | Oz'Iris |
| park_solver_discordid | int | 4563473457357 |
| coaster_solver_discordid | int | 4563473457357 |
| park_solved_at| timestamp|2019-03-10 14:00:27.927209|
| park_solved_at|timestmap|2019-03-10 14:00:27.927209|


| Name | Type |
|---|---|
|game_id| int|
|event|text|
|author|int|
|park|int|
|coaster|text|

#### pgsql without on_ready()
```py
    def __init__(self, bot):
        self.bot = bot
        ...

        self.bot.loop.create_task(self.init_db())

    async def init_db(self):
        self.db_pool = ...
```