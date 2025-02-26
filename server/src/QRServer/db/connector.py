import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional

import aiosqlite

from QRServer.common.classes import GameResultHistory, RankingEntry
from QRServer.common import utils
from QRServer.db import migrations
from QRServer.db.models import DbUser, DbMatchReport
from QRServer.db.password import password_verify, password_hash

log = logging.getLogger('qr.dbconnector')


class DbConnector:
    conn: aiosqlite.Connection

    def __init__(self, file, config):
        self.file = file
        self.config = config

    async def connect(self):
        self.conn = await aiosqlite.connect(self.file, autocommit=False)
        c = await self.conn.cursor()
        await migrations.setup_metadata(c)
        await migrations.execute_migrations(c, self.config)
        await self.conn.commit()

    async def get_user(self, user_id: str) -> Optional[DbUser]:
        c = await self.conn.cursor()
        await c.execute(
            "select id, username, password, created_at, discord_user_id from users where id = ?", (
                user_id,
            ))
        row = await c.fetchone()
        if row is None:
            return None
        return DbUser(
            user_id=row[0],
            username=row[1],
            password=row[2],
            created_at=row[3],
            discord_user_id=row[4],
        )

    async def get_user_by_username(self, username) -> Optional[DbUser]:
        c = await self.conn.cursor()
        await c.execute(
            "select id, username, password, created_at, discord_user_id from users where username = ?", (
                username,
            ))
        row = await c.fetchone()
        if row is None:
            return None
        return DbUser(
            user_id=row[0],
            username=row[1],
            password=row[2],
            created_at=row[3],
            discord_user_id=row[4],
        )

    async def get_users_by_discord_id(self, discord_user_id: str) -> List[DbUser]:
        c = await self.conn.cursor()
        await c.execute(
            "select id, username, password, created_at, discord_user_id from users where discord_user_id = ?", (
                discord_user_id,
            ))
        rows = await c.fetchall()
        if rows is None:
            return []
        result = []

        for row in rows:
            result.append(
                DbUser(
                    user_id=row[0],
                    username=row[1],
                    password=row[2],
                    created_at=row[3],
                    discord_user_id=row[4]
                )
            )
        return result

    async def create_member(self, username: str, password: bytes, discord_user_id: Optional[str] = None) -> None:
        c = await self.conn.cursor()
        await c.execute(
            "insert into users("
            "  id, username, password, created_at, discord_user_id"
            ") values (?, ?, ?, ?, ?)", (
                str(uuid.uuid4()),
                username,
                password_hash(password) if password else None,
                datetime.now().timestamp(),
                discord_user_id,
            ))
        await self.conn.commit()

    async def authenticate_user(self, username: str, password: Optional[bytes], auto_create=False,
                                verify_password=True) -> Optional[DbUser]:
        c = await self.conn.cursor()
        if auto_create:
            await c.execute(
                "insert or ignore into users("
                "  id, username, password, created_at, discord_user_id"
                ") values (?, ?, ?, ?, ?)", (
                    str(uuid.uuid4()),
                    username,
                    password_hash(password) if password else None,
                    datetime.now().timestamp(),
                    None
                )
            )
            await self.conn.commit()

        await c.execute("select id, username, password, created_at, discord_user_id from users where username = ?",
                        (username,))

        row = await c.fetchone()
        if row is None:
            return None

        db_user = DbUser(
            user_id=row[0],
            username=row[1],
            password=row[2],
            created_at=row[3],
            discord_user_id=row[4],
        )

        if not db_user.is_guest and verify_password and not password_verify(password, db_user.password):
            return None

        return db_user

    async def change_user_password(self, user_id: str, password: Optional[bytes]):
        c = await self.conn.cursor()
        await c.execute(
            "update users set password = ? where id = ?", (
                password_hash(password) if password else None,
                user_id
            ))
        await self.conn.commit()

    async def claim_member(self, user_id: str, password: Optional[bytes], discord_user_id: str):
        c = await self.conn.cursor()
        await c.execute(
            "update users set password = ?, discord_user_id = ? where id = ? and password is null", (
                password_hash(password) if password else None,
                discord_user_id,
                user_id,
            ))
        await self.conn.commit()

    async def add_match_result(self, match_result: DbMatchReport):
        c = await self.conn.cursor()
        await c.execute(
            "insert into matches ("
            "  id,"
            "  winner_id,"
            "  loser_id,"
            "  winner_pieces_left,"
            "  loser_pieces_left,"
            "  move_counter,"
            "  grid_size,"
            "  squadron_size,"
            "  started_at,"
            "  finished_at,"
            "  is_ranked,"
            "  is_void"
            ") values ("
            "?, ?, ?, ?, ?, ?,"
            "?, ?, ?, ?, ?, ?"
            ")", (
                match_result.match_id,
                match_result.winner_id,
                match_result.loser_id,
                match_result.winner_pieces_left,
                match_result.loser_pieces_left,
                match_result.move_counter,
                match_result.grid_size,
                match_result.squadron_size,
                match_result.started_at.timestamp(),
                match_result.finished_at.timestamp(),
                match_result.is_ranked,
                match_result.is_void
            ))

        start_date, end_date = utils.make_month_dates(
            month=match_result.finished_at.month, year=match_result.finished_at.year)

        new_ranking = await self._generate_ranking(
            start_date, end_date)

        await self._update_ranking(new_ranking, year=start_date.year, month=start_date.month)

        await self.conn.commit()

    async def get_match(self, match_id: str) -> Optional[DbMatchReport]:
        c = await self.conn.cursor()
        await c.execute(
            "select id, winner_id, loser_id, winner_pieces_left,"
            " loser_pieces_left, move_counter, grid_size,"
            " squadron_size, started_at, finished_at, is_ranked,"
            " is_void"
            " from matches where id = ?", (
                match_id,
            ))
        row = await c.fetchone()
        if row is None:
            return None
        return DbMatchReport(
            match_id=row[0],
            winner_id=row[1],
            loser_id=row[2],
            winner_pieces_left=row[3],
            loser_pieces_left=row[4],
            move_counter=row[5],
            grid_size=row[6],
            squadron_size=row[7],
            started_at=datetime.fromtimestamp(row[8]),
            finished_at=datetime.fromtimestamp(row[9]),
            is_ranked=row[10],
            is_void=row[11],
        )

    async def get_match2(self, match_id: str):
        c = await self.conn.cursor()

        await c.execute(
            "select"
            " u1.username,"
            " u2.username,"
            " m.winner_pieces_left,"
            " m.loser_pieces_left,"
            " m.started_at,"
            " m.finished_at,"
            " m.move_counter"
            " from matches m"
            " left join users u1 on m.winner_id = u1.id"
            " left join users u2 on m.loser_id = u2.id"
            " where m.id = ?", (match_id,))

        row = await c.fetchone()
        if row is None:
            return None
        return GameResultHistory(
            player_won=row[0],
            player_lost=row[1],
            won_score=row[2],
            lost_score=row[3],
            start=datetime.fromtimestamp(row[4]),
            finish=datetime.fromtimestamp(row[5]),
            moves=row[6],
        )

    async def get_recent_matches(self, count=15):
        c = await self.conn.cursor()

        # Gets all recent matches, minus void ones
        await c.execute("select"
                        " u1.username,"
                        " u2.username,"
                        " m.winner_pieces_left,"
                        " m.loser_pieces_left,"
                        " m.started_at,"
                        " m.finished_at,"
                        " m.move_counter"
                        " from matches m"
                        " left join users u1 on m.winner_id = u1.id"
                        " left join users u2 on m.loser_id = u2.id"
                        " where m.is_void = 0"
                        " order by m.finished_at desc"
                        " limit ?", (count,))

        recent_matches = []
        rows = await c.fetchall()
        for row in rows:
            recent_matches.append(GameResultHistory(
                player_won=row[0],
                player_lost=row[1],
                won_score=row[2],
                lost_score=row[3],
                start=datetime.fromtimestamp(row[4]),
                finish=datetime.fromtimestamp(row[5]),
                moves=row[6],
            ))
        return recent_matches

    async def get_ranking(self, start_date: datetime, end_date: datetime, ranked_only=True,
                          include_void=False) -> List[RankingEntry]:
        c = await self.conn.cursor()

        # Gets matches sort
        await c.execute(
            "select"
            " u.username,"
            " r.user_id,"
            " wins,"
            " total_games"
            " from rankings r"
            " inner join users u on u.id = r.user_id"
            " where r.year == ?"
            " and r.month == ?"
            " order by r.position asc"  # Lower position - higher in leaderboards
            " limit 100", (
                start_date.year,
                start_date.month,
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
        return ranking_entries

    async def _update_ranking(self, ranking_entries: List[RankingEntry], year: int, month: int) -> None:
        for position, entry in enumerate(ranking_entries):
            c = await self.conn.cursor()
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
                    year,
                    month,
                    position+1,
                    entry.user_id,
                    entry.wins,
                    entry.games,
                ))

    async def _generate_ranking(self, start_date: datetime, end_date: datetime) -> List[RankingEntry]:
        ranked_only = self.config.leaderboards_ranked_only.get()
        include_void = self.config.leaderboards_include_void.get()

        c = await self.conn.cursor()

        # Gets matches sort
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
        return ranking_entries

    async def close(self):
        await self.conn.close()


async def create_connector(config) -> DbConnector:
    data_dir = os.path.abspath(config.data_dir.get())
    os.makedirs(data_dir, exist_ok=True)
    dbfile = os.path.join(data_dir, 'database.sqlite3')
    log.debug(f'Opening database: {dbfile}')
    c = DbConnector(dbfile, config)
    await c.connect()
    return c
