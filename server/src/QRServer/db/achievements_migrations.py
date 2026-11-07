from datetime import datetime, timezone
from QRServer.config import Config


async def execute_migrations(transaction, config: Config, max_version=None):
    async with transaction('r') as c:
        version = await _select_version(c)

    if version is None:
        async with transaction('w') as c:
            await c.execute("insert into metadata (name, value) values ('achievements_version', '0')")
            version = 0

    migrations = [
        _advent_2026_v1,
    ]

    for i in range(max_version if max_version and max_version <= len(migrations) else len(migrations)):
        if version <= i:
            async with transaction('w') as c:
                await migrations[i](c, config)


async def _select_version(c):
    await c.execute("select value from metadata where name='achievements_version'")
    row = await c.fetchone()
    return int(row[0]) if row is not None else None


async def _set_version(c, version):
    await c.execute("update metadata set value = ? where name='achievements_version'", (version,))


def _dt_timestamp(year: int, month: int, day: int) -> int:
    return int(datetime(year=year, month=month, day=day, tzinfo=timezone.utc).timestamp())


# # # # # # # #
# Migrations  #
# # # # # # # #
async def _advent_2026_v1(c, _config):
    await c.execute(
        "insert into achievements (key, name, description, created_at)"
        " values (?, ?, ?, ?)", (
            'advent_2026',
            'Advent 2026',
            'Completed every challenge during Advent 2026 event.',
            _dt_timestamp(2026, 11, 7),
        )
    )

    await _set_version(c, 1)
