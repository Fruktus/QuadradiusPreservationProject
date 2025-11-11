from datetime import datetime as dt
from QRServer.common import utils
from QRServer.common.classes import RankingEntry
from QRServer.config import Config


async def setup_metadata(c):
    await c.execute(
        "create table if not exists metadata ("
        "  name varchar primary key, "
        "  value varchar"
        ")")


async def execute_migrations(c, config: Config, max_version=None):
    version = await _select_version(c)
    if version is None:
        await c.execute("insert into metadata (name, value) values ('version', '0')")
        version = 0

    migrations = [
        _migration_upgrade_to_v1,
        _migration_upgrade_to_v2,
        _migration_upgrade_to_v3,
        _migration_upgrade_to_v4,
        _migration_upgrade_to_v5,
        _migration_upgrade_to_v6,
        _migration_upgrade_to_v7,
        _migration_upgrade_to_v8,
    ]

    for i in range(max_version if max_version and max_version <= len(migrations) else len(migrations)):
        if version <= i:
            await migrations[i](c, config)


async def _select_version(c):
    await c.execute("select value from metadata where name='version'")
    row = await c.fetchone()
    return int(row[0]) if row is not None else None


async def _set_version(c, version):
    await c.execute("update metadata set value = ? where name='version'", (version,))


# # # # # # # #
# Migrations  #
# # # # # # # #
async def _migration_upgrade_to_v1(c, _config):
    await c.execute(
            "create table users ("
            "  id varchar primary key,"
            "  username varchar unique,"
            "  password varchar"
            ")")
    await _set_version(c, 1)


async def _migration_upgrade_to_v2(c, _config):
    await c.execute("alter table users add column comment varchar")
    await _set_version(c, 2)


async def _migration_upgrade_to_v3(c, _config):
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


async def _migration_upgrade_to_v4(c, _config):
    await c.execute(
        "alter table users"
        " add column created_at integer"
    )
    await _set_version(c, 4)


async def _migration_upgrade_to_v5(c, _config):
    await c.execute(
        "alter table users"
        " add column discord_user_id varchar"
    )
    await _set_version(c, 5)


async def _migration_upgrade_to_v6(c, config):
    await c.execute(
        "create table rankings ("
        "  year integer,"
        "  month integer,"
        "  position integer,"
        "  user_id varchar,"
        "  wins integer,"
        "  total_games integer,"
        "  primary key(year, month, position),"
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

        ranked_only = config.leaderboards_ranked_only.get()
        include_void = config.leaderboards_include_void.get()

        for date in dates_range:
            start_date, end_date = utils.make_month_dates(date.month, date.year)

            # Generate rankings - same as the dbconnector's function at the time of writing
            await c.execute(
                "select"
                " u.username,"
                " u.id,"
                " sum(m.winner_id = u.id) as total_wins,"
                " count(*) as total_games,"
                " (sum(m.winner_id = u.id) * 1.0 / count(*)) as win_percentage"
                " from users u"
                " inner join matches m on (u.id = m.winner_id or u.id = m.loser_id)"
                " where m.finished_at >= ?"
                " and m.finished_at < ?"
                " and (case when ? = 1 then m.is_ranked = 1 else 1=1 end)"
                " and (case when ? = 0 then m.is_void = 0 else 1=1 end)"
                " group by u.username"
                " order by win_percentage desc, total_wins desc"
                " limit 100", (
                    start_date.timestamp(),
                    end_date.timestamp(),
                    1 if ranked_only else 0,
                    1 if include_void else 0
                )
            )

            ranking_entries = []
            rows = await c.fetchall()
            for row in rows:
                ranking_entries.append(RankingEntry(
                    username=row[0],
                    user_id=row[1],
                    wins=row[2],
                    games=row[3],
                ))

            # end
            if ranking_entries:
                for position, entry in enumerate(ranking_entries):
                    await c.execute(
                        "insert or replace into rankings ("
                        "  year,"
                        "  month,"
                        "  position,"
                        "  user_id,"
                        "  wins,"
                        "  total_games"
                        ") values ("
                        "?, ?, ?, ?, ?, ?"
                        ")", (
                            date.year,
                            date.month,
                            position+1,
                            entry.user_id,
                            entry.wins,
                            entry.games,
                        ))

    await _set_version(c, 6)


async def _migration_upgrade_to_v7(c, config):
    await c.execute(
        "create table user_ratings ("
        " user_id varchar,"
        " year integer,"
        " month integer,"
        " revision integer,"
        " rating integer,"
        " primary key(user_id, year, month),"
        " foreign key(user_id) references users (id)"
        ")"
    )
    await _set_version(c, 7)


async def _migration_upgrade_to_v8(c, _config):
    await c.execute(
        "create table tournaments ("
        " id varchar primary key,"
        " name varchar unique not null,"
        " created_by_dc_id varchar,"
        " tournament_msg_dc_id varchar,"
        " required_matches_per_duel integer,"
        " created_at integer,"
        " started_at integer,"
        " finished_at integer"
        ")"
    )

    await c.execute(
        "create table tournament_participants ("
        " tournament_id varchar,"
        " user_id varchar,"
        " primary key(tournament_id, user_id),"
        " foreign key(tournament_id) references tournaments (id),"
        " foreign key(user_id) references users (id)"
        ")"
    )

    await c.execute(
        "create table tournament_duels ("
        " tournament_id varchar,"
        " duel_idx integer,"
        " active_until integer,"
        " user1_id varchar,"
        " user2_id varchar,"
        " primary key(tournament_id, duel_idx),"
        " foreign key(user1_id) references users (id),"
        " foreign key(user2_id) references users (id),"
        " foreign key(tournament_id) references tournaments (id)"
        ")"
    )

    await c.execute(
        "create table tournament_matches ("
        " tournament_id varchar,"
        " duel_idx integer,"
        " match_id varchar,"
        " primary key(tournament_id, duel_idx, match_id),"
        " foreign key(tournament_id) references tournaments (id)"
        " foreign key(duel_idx) references tournament_duels (duel_idx)"
        " foreign key(match_id) references matches (id)"
        ")"
    )

    await _set_version(c, 8)
