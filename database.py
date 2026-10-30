# SQLite database for programs and scholarships
import sqlite3

# CHECK makes SQLite refuse bad values
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
);

CREATE TABLE IF NOT EXISTS scholarships (
    name     TEXT    NOT NULL CHECK (name != ''),
    amount   INTEGER NOT NULL CHECK (amount >= 0),
    degrees  TEXT    NOT NULL,
    fields   TEXT    NOT NULL,
    min_gpa  REAL    NOT NULL CHECK (min_gpa BETWEEN 0 AND 4),
    open_to  TEXT    NOT NULL,
    deadline TEXT    NOT NULL CHECK (date(deadline) IS deadline),
    website  TEXT    NOT NULL
);
"""


def connect(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row  # rows can be read by column name
    connection.executescript(SCHEMA)
    return connection


def add_program(connection, program):
    connection.execute(
        "INSERT INTO programs VALUES (:university, :degree, :field, :state, :tuition_in_state, "
        ":tuition_out_state, :living_cost, :acceptance_rate, :deadline, :website)", program)
    connection.commit()


def add_scholarship(connection, scholarship):
    connection.execute(
        "INSERT INTO scholarships VALUES (:name, :amount, :degrees, :fields, :min_gpa, :open_to, "
        ":deadline, :website)", scholarship)
    connection.commit()


def get_programs(connection):
    rows = connection.execute("SELECT * FROM programs ORDER BY university")
    return [dict(row) for row in rows]


def get_scholarships(connection):
    rows = connection.execute("SELECT * FROM scholarships ORDER BY name")
    return [dict(row) for row in rows]
