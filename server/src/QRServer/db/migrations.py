from datetime import datetime as dt
from QRServer.common import utils


async def setup_metadata(dbconnector):
    c = await dbconnector.conn.cursor()
    await c.execute(
        "create table if not exists metadata ("
        "  name varchar primary key, "
        "  value varchar"
        ")")


async def execute_migrations(dbconnector):
    c = await dbconnector.conn.cursor()
    version = await _select_version(c)
    if version is None:
        await c.execute("insert into metadata (name, value) values ('version', '0')")
        version = 0

    if version <= 0:
        await c.execute(
            "create table users ("
            "  id varchar primary key,"
            "  username varchar unique,"
            "  password varchar"
            ")")
        await _set_version(c, 1)
    if version <= 1:
        await c.execute("alter table users add column comment varchar")
        await _set_version(c, 2)
    if version <= 2:
        await c.execute(
            "create table matches ("
            "  id varchar primary key,"
            "  winner_id varchar,"
            "  loser_id varchar,"
            "  winner_pieces_left integer,"
            "  loser_pieces_left integer,"
            "  move_counter integer,"
            "  grid_size varchar,"
            "  squadron_size varchar,"
            "  started_at integer,"
            "  finished_at integer,"
            "  is_ranked integer,"
            "  is_void integer,"
            "  foreign key(winner_id) references users (id),"
            "  foreign key(loser_id) references users (id)"
            ")")
        await _set_version(c, 3)
    if version <= 3:
        await c.execute(
            "alter table users"
            " add column created_at integer"
        )
        await _set_version(c, 4)
    if version <= 4:
        await c.execute(
            "alter table users"
            " add column discord_user_id varchar"
        )
        await _set_version(c, 5)
    if version <= 5:
        await c.execute(
            "create table rankings ("
            "  year integer,"
            "  month integer,"
            "  position integer,"
            "  user_id varchar,"
            "  wins integer,"
            "  total_games integer,"
            "  primary key (year, month, position),"
            "  foreign key(user_id) references users (id)"
            ")"
        )
        await c.execute(
            "select started_at"
            " from matches"
            " order by started_at asc"
            " limit 1"
        )
        row = await c.fetchone()
        if row:
            first_timestamp = row[0]
            first_dt = dt.fromtimestamp(first_timestamp)
            dates_range = utils.make_month_dates_range(start_date=first_dt, end_date=dt.now())

            for date in dates_range:
                start_date, end_date = utils.make_month_dates(date.month, date.year)

                ranking_entries = await dbconnector._generate_ranking(start_date, end_date)
                if ranking_entries:
                    await dbconnector._update_ranking(ranking_entries, year=date.year, month=date.month)

        await _set_version(c, 6)


async def _select_version(c):
    await c.execute("select value from metadata where name='version'")
    row = await c.fetchone()
    return int(row[0]) if row is not None else None


async def _set_version(c, version):
    await c.execute("update metadata set value = ? where name='version'", (version,))
