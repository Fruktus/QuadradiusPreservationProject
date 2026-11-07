from typing import Callable
from QRServer.config import Config


async def setup_metadata(c):
    await c.execute(
        "create table if not exists metadata ("
        "  name varchar primary key, "
        "  value varchar"
        ")")


async def run_migrations(transaction, config: Config, migrations: list[Callable], version_key: str, max_version=None):
    async with transaction('r') as c:
        version = await select_version(c, version_key)

    if version is None:
        async with transaction('w') as c:
            await c.execute("insert into metadata (name, value) values (?, '0')", (version_key, ))
            version = 0

    for i in range(max_version if max_version and max_version <= len(migrations) else len(migrations)):
        if version <= i:
            async with transaction('w') as c:
                await migrations[i](c, config)


async def select_version(c, key: str):
    await c.execute("select value from metadata where name = ?", (key, ))
    row = await c.fetchone()
    return int(row[0]) if row is not None else None


async def set_version(c, key: str, version):
    await c.execute("update metadata set value = ? where name = ?", (version, key, ))
