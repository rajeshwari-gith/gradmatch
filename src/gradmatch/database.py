import sqlite3
from dataclasses import astuple, fields

from gradmatch.models import Program

COLUMNS = [f.name for f in fields(Program)]


def create_database(programs: list[Program], path=":memory:") -> sqlite3.Connection:
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.execute(f"CREATE TABLE programs ({', '.join(COLUMNS)})")
    connection.executemany(f"INSERT INTO programs VALUES ({', '.join('?' * len(COLUMNS))})",
                           [astuple(p) for p in programs])
    return connection


def get_programs(connection: sqlite3.Connection, degree: str, field: str) -> list[Program]:
    rows = connection.execute("SELECT * FROM programs WHERE degree = ? AND field = ?",
                              (degree, field))
    return [Program(*row) for row in rows]


def get_fields(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute("SELECT DISTINCT field FROM programs ORDER BY field")
    return [row[0] for row in rows]
