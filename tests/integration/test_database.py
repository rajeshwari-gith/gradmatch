import sqlite3
from contextlib import closing

import pytest

from gradmatch.database import (add_programs, add_scholarships, connect, get_fields, get_programs,
                                get_scholarships)
from helpers import DATABASE, make_program, make_scholarship


def test_programs_come_back_the_same():
    program = make_program()
    with closing(connect(":memory:")) as connection:
        add_programs(connection, [program])
        assert get_programs(connection) == [program]


def test_scholarships_come_back_the_same():
    scholarship = make_scholarship(degrees=("MS", "PhD"), fields=("Computer Science", "Statistics"))
    with closing(connect(":memory:")) as connection:
        add_scholarships(connection, [scholarship])
        assert get_scholarships(connection) == [scholarship]


def test_empty_database():
    with closing(connect(":memory:")) as connection:
        assert (get_programs(connection), get_scholarships(connection), get_fields(connection)) == ([], [], [])


def test_fields_are_listed_once_in_order():
    programs = [make_program(field="Statistics"), make_program(), make_program()]
    with closing(connect(":memory:")) as connection:
        add_programs(connection, programs)
        assert get_fields(connection) == ["Computer Science", "Statistics"]


def test_saved_to_a_file(tmp_path):
    with closing(connect(tmp_path / "test.db")) as connection:
        add_programs(connection, [make_program()])
    with closing(connect(tmp_path / "test.db")) as connection:
        assert len(get_programs(connection)) == 1


def test_real_database():
    with closing(connect(DATABASE)) as connection:
        programs = get_programs(connection)
        assert len(programs) == 159
        assert {p.degree for p in programs} == {"MS", "PhD"}
        assert len(get_scholarships(connection)) == 7
        assert get_fields(connection) == ["Computer Science", "Electrical Engineering",
                                          "Mechanical Engineering", "Statistics"]


# the database itself refuses bad values
@pytest.mark.parametrize("bad", [
    dict(university=""),
    dict(degree="BS"),
    dict(state="Michigan"),
    dict(tuition_in_state=-1),
    dict(living_cost=-1),
    dict(acceptance_rate=1.5),
    dict(tuition_in_state="lots"),
], ids=lambda bad: f"{list(bad)[0]}={list(bad.values())[0]}")
def test_bad_program_is_refused(bad):
    with closing(connect(":memory:")) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            add_programs(connection, [make_program(**bad)])


@pytest.mark.parametrize("bad", [dict(name=""), dict(amount=-5), dict(min_gpa=4.5)],
                         ids=["name", "amount", "min_gpa"])
def test_bad_scholarship_is_refused(bad):
    with closing(connect(":memory:")) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            add_scholarships(connection, [make_scholarship(**bad)])


def test_bad_deadline_is_refused():
    with closing(connect(":memory:")) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO scholarships VALUES ('A', 1, 'MS', 'Any', 3.0, 'Everyone', "
                               "'Feb 1', 'https://example.org')")
