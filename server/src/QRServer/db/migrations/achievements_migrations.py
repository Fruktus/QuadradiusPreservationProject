from datetime import datetime, timezone
from QRServer.config import Config
from QRServer.db.migrations.runner import run_migrations, set_version


VERSION_KEY = 'achievements_version'


async def execute_migrations(transaction, config: Config, max_version=None):
    migrations = [
        _v1_winter_2026,
    ]

    await run_migrations(transaction, config, migrations, version_key=VERSION_KEY, max_version=max_version)


def _dt_timestamp(year: int, month: int, day: int) -> int:
    return int(datetime(year=year, month=month, day=day, tzinfo=timezone.utc).timestamp())


async def _set_version(c, version):
    await set_version(c, VERSION_KEY, version)


# # # # # # # #
# Migrations  #
# # # # # # # #
async def _v1_winter_2026(c, _config):
    await c.execute(
        "insert into achievements (key, name, description, created_at)"
        " values (?, ?, ?, ?)", (
            'winter_2026',
            'Winter Calendar 2026',
            'Completed the 2026 Winter Calendar event.',
            _dt_timestamp(2026, 11, 7),
        )
    )

    await _set_version(c, 1)
