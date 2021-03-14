import logging
import os
import sqlite3
import threading
import uuid
from typing import Optional

from QRServer import config
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
                log.info('Auto registering member {}', username)
                return self.add_member(username, password)
            return None
        _id = row[0]
        hashed = row[1]
        if password_verify(password, hashed):
            return _id
        else:
            return None


_connector = threading.local()


def connector():
    try:
        return _connector.value
    except AttributeError:
        dbfile = os.path.abspath(config.data_dir.get() + '/database.sqlite3')
        log.debug('Opening database: {}'.format(dbfile))
        c = DBConnector(dbfile)
        _connector.value = c
        return c
