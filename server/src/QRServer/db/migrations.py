def setup_metadata(c):
    c.execute(
        "create table if not exists metadata ("
        "  name varchar primary key, "
        "  value varchar"
        ")")


def execute_migrations(c):
    version = _select_version(c)
    if version is None:
        c.execute("insert into metadata (name, value) values ('version', '0')")
        version = 0

    if version <= 0:
        c.execute(
            "create table users ("
            "  id varchar primary key,"
            "  username varchar unique,"
            "  password varchar"
            ")")
        _set_version(c, 1)
    if version <= 1:
        c.execute("alter table users add column comment varchar")
        _set_version(c, 2)
    if version <= 2:
        c.execute(
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
        _set_version(c, 3)


def _select_version(c):
    c.execute("select value from metadata where name='version'")
    row = c.fetchone()
    return int(row[0]) if row is not None else None


def _set_version(c, version):
    c.execute("update metadata set value = ? where name='version'", (version,))
