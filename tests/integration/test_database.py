import sqlite3
from contextlib import closing

import pytest

from gradmatch.database import add_programs, add_scholarships, connect, get_programs, get_scholarships
from helpers import DATABASE, make_program, make_scholarship


def test_save_and_read_back(tmp_path):
    program, scholarship = make_program(), make_scholarship()
    with closing(connect(tmp_path / "test.db")) as connection:
        assert get_programs(connection) == []
        add_programs(connection, [program])
        add_scholarships(connection, [scholarship])
    with closing(connect(tmp_path / "test.db")) as connection:
        assert get_programs(connection) == [program]
        assert get_scholarships(connection) == [scholarship]


def test_real_database():
    with closing(connect(DATABASE)) as connection:
        assert len(get_programs(connection)) == 159
        assert len(get_scholarships(connection)) == 7
        assert {p.field for p in get_programs(connection)} == {
            "Computer Science", "Electrical Engineering", "Mechanical Engineering", "Statistics"}


def test_req8_database_refuses_bad_data():
    bad_programs = [dict(university=""), dict(degree="BS"), dict(state="OHI"),
                    dict(tuition_in_state=-1), dict(living_cost=-1), dict(acceptance_rate=1.5),
                    dict(tuition_in_state="lots")]
    bad_scholarships = [dict(name=""), dict(amount=-5), dict(min_gpa=4.5)]
    with closing(connect(":memory:")) as connection:
        for bad in bad_programs:
            with pytest.raises(sqlite3.IntegrityError):
                add_programs(connection, [make_program(**bad)])
        for bad in bad_scholarships:
            with pytest.raises(sqlite3.IntegrityError):
                add_scholarships(connection, [make_scholarship(**bad)])
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO scholarships VALUES "
                               "('A', 1, 'MS', 'Any', 3.0, 'Everyone', '2027-02-30', 'x')")
        assert get_programs(connection) == []
