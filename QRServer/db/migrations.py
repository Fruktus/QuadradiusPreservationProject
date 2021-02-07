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


def _select_version(c):
    c.execute("select value from metadata where name='version'")
    row = c.fetchone()
    return int(row[0]) if row is not None else None


def _set_version(c, version):
    c.execute("update metadata set value = ? where name='version'", (version,))
