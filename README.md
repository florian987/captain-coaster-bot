## Selenium
Selenium a besoin de capabilities admin.
```sh
--cap-add=SYS_ADMIN
```

## CaptainCoaster
### Postgres

| Name | Type | Comment |
|---|---|---|
| GameID | SERIAL | hash(channel.id + time.time()) |
| Created_at | timestamp |  |
| Difficulty | int |  |
| Park | str |  |
| Coaster | str |  |
| park_solver_discordid | int |  |
| coaster_solver_discordid | int |  |
| park_solved_at| timestamp| |
| park_solved_at|timestmap| |


## TODO
- rework vote to use number emoji instead of randome using [inflect](https://github.com/jazzband/inflect)