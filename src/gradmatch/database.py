import sqlite3
from datetime import date

from gradmatch.models import Program, Scholarship

# STRICT makes SQLite refuse a value of the wrong type, and CHECK refuses bad values
SCHEMA = """
CREATE TABLE IF NOT EXISTS programs (
    university        TEXT    NOT NULL CHECK (university != ''),
    degree            TEXT    NOT NULL CHECK (degree IN ('MS', 'PhD')),
    field             TEXT    NOT NULL CHECK (field != ''),
    state             TEXT    NOT NULL CHECK (length(state) = 2),
    tuition_in_state  INTEGER NOT NULL CHECK (tuition_in_state >= 0),
    tuition_out_state INTEGER NOT NULL CHECK (tuition_out_state >= 0),
    living_cost       INTEGER NOT NULL CHECK (living_cost >= 0),
    acceptance_rate   REAL    NOT NULL CHECK (acceptance_rate BETWEEN 0 AND 1),
    deadline          TEXT    NOT NULL CHECK (date(deadline) IS deadline),
    website           TEXT    NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS scholarships (
    name     TEXT    NOT NULL CHECK (name != ''),
    amount   INTEGER NOT NULL CHECK (amount >= 0),
    degrees  TEXT    NOT NULL,
    fields   TEXT    NOT NULL,
    min_gpa  REAL    NOT NULL CHECK (min_gpa BETWEEN 0 AND 4),
    open_to  TEXT    NOT NULL,
    deadline TEXT    NOT NULL CHECK (date(deadline) IS deadline),
    website  TEXT    NOT NULL
) STRICT;
"""


def connect(path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.executescript(SCHEMA)
    return connection


def add_programs(connection: sqlite3.Connection, programs: list[Program]) -> None:
    rows = [(p.university, p.degree, p.field, p.state, p.tuition_in_state,
             p.tuition_out_state, p.living_cost, p.acceptance_rate, p.deadline.isoformat(),
             p.website) for p in programs]
    connection.executemany("INSERT INTO programs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    connection.commit()


def add_scholarships(connection: sqlite3.Connection, scholarships: list[Scholarship]) -> None:
    rows = [(s.name, s.amount, ";".join(s.degrees), ";".join(s.fields), s.min_gpa, s.open_to,
             s.deadline.isoformat(), s.website) for s in scholarships]
    connection.executemany("INSERT INTO scholarships VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
    connection.commit()


def get_programs(connection: sqlite3.Connection) -> list[Program]:
    rows = connection.execute("SELECT * FROM programs ORDER BY university")
    return [Program(*row[:8], date.fromisoformat(row[8]), row[9]) for row in rows]


def get_scholarships(connection: sqlite3.Connection) -> list[Scholarship]:
    rows = connection.execute("SELECT * FROM scholarships ORDER BY name")
    return [Scholarship(name, amount, tuple(degrees.split(";")), tuple(fields.split(";")), min_gpa,
                        open_to, date.fromisoformat(deadline), website)
            for name, amount, degrees, fields, min_gpa, open_to, deadline, website in rows]

