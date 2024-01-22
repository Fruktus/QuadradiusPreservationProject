import logging
import os
import sqlite3
import threading
import uuid
from datetime import datetime
from typing import Optional

from QRServer import config
from QRServer.common.classes import GameResultHistory, MatchResult
from QRServer.db import migrations
from QRServer.db.password import password_verify, password_hash

log = logging.getLogger('dbconnector')


class DBConnector:
    conn: sqlite3.Connection

    def __init__(self, file):
        self.conn = sqlite3.connect(file)
        c = self.conn.cursor()
        migrations.setup_metadata(c)
        migrations.execute_migrations(c)
        self.conn.commit()

    def add_member(self, username: str, password: bytes) -> Optional[str]:
        c = self.conn.cursor()
        _id = str(uuid.uuid4())
        c.execute(
            "insert into users ("
            "  id,"
            "  username,"
            "  password"
            ") values (?, ?, ?)", (
                _id,
                username,
                password_hash(password)
            ))
        self.conn.commit()
        return _id

    def add_guest(self, username: str) -> Optional[str]:
        c = self.conn.cursor()
        _id = str(uuid.uuid4())
        c.execute(
            "insert into users ("
            "  id,"
            "  username,"
            ") values (?, ?)", (
                _id,
                username
            ))
        self.conn.commit()
        return _id

    def get_comment(self, user_id: str) -> Optional[str]:
        c = self.conn.cursor()
        c.execute(
            "select comment from users where id = ?", (
                user_id,
            ))
        row = c.fetchone()
        if row is None:
            return None
        return str(row[0])

    def set_comment(self, user_id: str, comment: str) -> None:
        c = self.conn.cursor()
        c.execute(
            "update users set"
            "  comment = ?"
            "where id = ?", (
                comment,
                user_id
            ))
        self.conn.commit()

    def authenticate_member(self, username: str, password: bytes) -> Optional[str]:
        c = self.conn.cursor()
        c.execute("select id, password from users where username = ?", (username,))
        row = c.fetchone()
        if row is None:
            if config.auto_register.get():
                log.info(f'Auto registering member {username}')
                return self.add_member(username, password)
            return None
        _id = row[0]
        hashed = row[1]
        if password_verify(password, hashed):
            return _id
        else:
            return None

    def get_user_id_by_username(self, username: str):
        c = self.conn.cursor()
        c.execute("select id from users where username = ?", (username,))
        row = c.fetchone()
        if not row:
            return None
        return row[0]

    def is_guest(self, username: str):
        c = self.conn.cursor()
        c.execute("select id, password from users where username = ?", (username,))
        row = c.fetchone()
        if not row:
            return True
        return row[1] is None

    def add_match_result(self, match_result: MatchResult):
        winner_id = self.get_user_id_by_username(match_result.winner_username)
        loser_id = self.get_user_id_by_username(match_result.loser_username)

        if not winner_id or not loser_id:
            log.warning(f'Missing ID for one of players: {[match_result.winner_username, match_result.loser_username]}')
            return

        c = self.conn.cursor()
        _id = str(uuid.uuid4())
        c.execute(
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
                _id,
                winner_id,
                loser_id,
                match_result.winner_pieces_left,
                match_result.loser_pieces_left,
                match_result.move_counter,
                match_result.grid_size,
                match_result.squadron_size,
                match_result.started_at,
                match_result.finished_at,
                match_result.is_ranked,
                match_result.is_void
            ))
        self.conn.commit()
        return _id

    def get_recent_matches(self, count=15):
        c = self.conn.cursor()

        # Gets all recent matches, minus void ones
        c.execute("select"
                  " u1.username,"
                  " u2.username,"
                  " m.winner_pieces_left,"
                  " m.loser_pieces_left,"
                  " m.started_at,"
                  " m.finished_at"
                  " from matches m"
                  " left join users u1 on m.winner_id = u1.id"
                  " left join users u2 on m.loser_id = u2.id"
                  " where m.is_void = 0"
                  " order by m.finished_at"
                  " limit ?", (count,))

        recent_matches = []
        rows = c.fetchall()

        for row in rows:
            recent_matches.append(GameResultHistory(
                player_won=row[0],
                player_lost=row[1],
                won_score=row[2],
                lost_score=row[3],
                start=datetime.fromtimestamp(row[4]),
                finish=datetime.fromtimestamp(row[5])
            ))
        return recent_matches


_connector = threading.local()


def connector():
    try:
        return _connector.value
    except AttributeError:
        data_dir = os.path.abspath(config.data_dir.get())
        os.makedirs(data_dir, exist_ok=True)
        dbfile = os.path.join(data_dir, 'database.sqlite3')
        log.debug(f'Opening database: {dbfile}')
        c = DBConnector(dbfile)
        _connector.value = c
        return c
