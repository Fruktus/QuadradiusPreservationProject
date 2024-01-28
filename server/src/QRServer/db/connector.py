import logging
import os
import uuid
from datetime import datetime
from typing import Optional

import aiosqlite

from QRServer import config
from QRServer.common.classes import GameResultHistory
from QRServer.db import migrations
from QRServer.db.models import DbUser, DbMatchReport
from QRServer.db.password import password_verify, password_hash

log = logging.getLogger('dbconnector')


class DbConnector:
    conn: aiosqlite.Connection

    def __init__(self, file):
        self.file = file

    async def connect(self):
        self.conn = await aiosqlite.connect(self.file)
        c = await self.conn.cursor()
        await migrations.setup_metadata(c)
        await migrations.execute_migrations(c)
        await self.conn.commit()

    async def add_member(self, username: str, password: bytes) -> Optional[str]:
        c = await self.conn.cursor()
        _id = str(uuid.uuid4())
        await c.execute(
            "insert into users ("
            "  id,"
            "  username,"
            "  password,"
            "  created_at"
            ") values (?, ?, ?, ?)", (
                _id,
                username,
                password_hash(password),
                datetime.now().timestamp()
            ))
        await self.conn.commit()
        return _id

    async def add_guest(self, username: str) -> Optional[str]:
        c = await self.conn.cursor()
        _id = str(uuid.uuid4())
        await c.execute(
            "insert into users ("
            "  id,"
            "  username,"
            "  created_at"
            ") values (?, ?, ?)", (
                _id,
                username,
                datetime.now().timestamp(),
            ))
        await self.conn.commit()
        return _id

    async def get_user(self, user_id: str) -> Optional[DbUser]:
        c = await self.conn.cursor()
        await c.execute(
            "select id, username, password, created_at from users where id = ?", (
                user_id,
            ))
        row = await c.fetchone()
        if row is None:
            return None
        return DbUser(
            user_id=row[0],
            username=row[1],
            password=row[2],
            created_at=row[3]
        )

    async def get_user_by_username(self, username) -> Optional[DbUser]:
        c = await self.conn.cursor()
        await c.execute(
            "select id, username, password, created_at from users where username = ?", (
                username,
            ))
        row = await c.fetchone()
        if row is None:
            return None
        return DbUser(
            user_id=row[0],
            username=row[1],
            password=row[2],
            created_at=row[3]
        )

    async def get_comment(self, user_id: str) -> Optional[str]:
        c = await self.conn.cursor()
        await c.execute(
            "select comment from users where id = ?", (
                user_id,
            ))
        row = await c.fetchone()
        if row is None:
            return None
        return str(row[0])

    async def set_comment(self, user_id: str, comment: str) -> None:
        c = await self.conn.cursor()
        await c.execute(
            "update users set"
            "  comment = ?"
            "where id = ?", (
                comment,
                user_id,
            ))
        await self.conn.commit()

    async def authenticate_member(self, username: str, password: bytes) -> Optional[str]:
        c = await self.conn.cursor()
        await c.execute("select id, password from users where username = ?", (username,))
        row = await c.fetchone()
        if row is None:
            if config.auto_register.get():
                log.info(f'Auto registering member {username}')
                return await self.add_member(username, password)
            return None
        _id = row[0]
        hashed = row[1]
        if password_verify(password, hashed):
            return _id
        else:
            return None

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

    async def close(self):
        await self.conn.close()


_connector = None


async def connector() -> DbConnector:
    global _connector
    if _connector:
        return _connector

    data_dir = os.path.abspath(config.data_dir.get())
    os.makedirs(data_dir, exist_ok=True)
    dbfile = os.path.join(data_dir, 'database.sqlite3')
    log.debug(f'Opening database: {dbfile}')
    c = DbConnector(dbfile)
    await c.connect()
    _connector = c
    return c
