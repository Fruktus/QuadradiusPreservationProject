import sqlite3
import threading
import uuid

from QRServer import config
from QRServer.db import migrations
from QRServer.db.password import password_verify, password_hash


class DBConnector:
    conn: sqlite3.Connection

    def __init__(self, file):
        self.conn = sqlite3.connect(file)
        c = self.conn.cursor()
        migrations.setup_metadata(c)
        migrations.execute_migrations(c)
        self.conn.commit()

    def add_member(self, username, password):
        c = self.conn.cursor()
        _id = uuid.uuid4()
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

    def authenticate_member(self, username: str, password: bytes):
        c = self.conn.cursor()
        c.execute("select id, password from users where username = ?", (username,))
        row = c.fetchone()
        if row is None:
            return None
        _id = c.fetchone()[0]
        hashed = c.fetchone()[1]
        if password_verify(password, hashed):
            return _id
        else:
            return None


_connector = threading.local()


def connector():
    try:
        return _connector.value
    except AttributeError:
        c = DBConnector(config.data_dir + '/database.sqlite3')
        _connector.value = c
        return c
