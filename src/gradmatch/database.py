import sqlite3
from dataclasses import astuple, fields
from datetime import date

from gradmatch.models import Program

COLUMNS = [f.name for f in fields(Program)]


def to_row(program: Program) -> tuple:
    # SQLite has no date type, so the deadline is saved as text like "2027-01-15"
    return tuple(v.isoformat() if isinstance(v, date) else v for v in astuple(program))


def to_program(row: tuple) -> Program:
    values = dict(zip(COLUMNS, row))
    if values["deadline"]:
        values["deadline"] = date.fromisoformat(values["deadline"])
    return Program(**values)


def create_database(programs: list[Program], path=":memory:") -> sqlite3.Connection:
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.execute(f"CREATE TABLE programs ({', '.join(COLUMNS)})")
    connection.executemany(f"INSERT INTO programs VALUES ({', '.join('?' * len(COLUMNS))})",
                           [to_row(p) for p in programs])
    return connection


def get_programs(connection: sqlite3.Connection, degree: str, field: str) -> list[Program]:
    rows = connection.execute("SELECT * FROM programs WHERE degree = ? AND field = ?",
                              (degree, field))
    return [to_program(row) for row in rows]


def get_fields(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute("SELECT DISTINCT field FROM programs ORDER BY field")
    return [row[0] for row in rows]
