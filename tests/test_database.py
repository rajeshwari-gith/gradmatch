import sqlite3
from contextlib import closing
from datetime import date

from gradmatch.data_loader import load_programs
from gradmatch.database import create_database, get_fields, get_programs
from helpers import PROGRAMS, make_program


def test_saved_programs_come_back_the_same():
    program = make_program(stipend=30000, avg_gre=320, deadline=date(2027, 1, 15))
    with closing(create_database([program])) as database:
        assert get_programs(database, "MS", "Computer Science") == [program]


def test_get_programs_filters_degree_and_field():
    programs = [make_program(university="A"), make_program(university="B", degree="PhD"),
                make_program(university="C", field="Statistics")]
    with closing(create_database(programs)) as database:
        assert [p.university for p in get_programs(database, "MS", "Computer Science")] == ["A"]


def test_empty_database():
    with closing(create_database([])) as database:
        assert get_programs(database, "MS", "Computer Science") == []


def test_real_data_in_the_database():
    with closing(create_database(load_programs(PROGRAMS))) as database:
        assert get_fields(database) == ["Computer Science", "Electrical Engineering",
                                        "Mechanical Engineering", "Statistics"]
        assert len(get_programs(database, "PhD", "Statistics")) == 8


def test_database_file(tmp_path):
    with closing(create_database([make_program()], tmp_path / "test.db")) as database:
        database.commit()
    with closing(sqlite3.connect(tmp_path / "test.db")) as database:
        assert database.execute("SELECT COUNT(*) FROM programs").fetchone() == (1,)
