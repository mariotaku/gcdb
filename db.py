import os
import sqlite3
from os import PathLike, path
from sqlite3 import Connection, Cursor
from typing import Dict, Optional


class Schema:
    version: int
    migrations: Dict[int, str or PathLike[str]]

    def __init__(self, version: int, migrations: Dict[int, str or PathLike[str]]):
        self.version = version
        self.migrations = migrations

    def migrate(self, conn: Connection, from_version: int):
        cursor = conn.cursor()
        for to_version in range(from_version + 1, self.version + 1):
            with open(self.migrations[to_version]) as migration:
                cursor.executescript(migration.read())
        conn.commit()


class Database:
    conn: Connection

    def __init__(self, name: str, schema: Optional[Schema] = None):
        os.makedirs(path.dirname(name), exist_ok=True)
        self.conn = sqlite3.connect(name)
        version = self.schema_version
        if schema and version < schema.version:
            schema.migrate(self.conn, version)
            self.schema_version = schema.version

    @property
    def schema_version(self) -> int:
        version, = self.conn.execute('PRAGMA schema_version').fetchone()
        return version

    @schema_version.setter
    def schema_version(self, version: int):
        self.conn.execute(f'PRAGMA schema_version = {version}')

    def cursor(self) -> Cursor:
        return self.conn.cursor()

    def execute(self, *args, **kwargs):
        return self.conn.execute(*args, **kwargs)

    def executemany(self, *args, **kwargs):
        return self.conn.executemany(*args, **kwargs)

    def commit(self):
        return self.conn.commit()
