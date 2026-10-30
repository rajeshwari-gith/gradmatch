import sqlite3
from contextlib import closing

import pytest

from gradmatch.database import (add_programs, add_scholarships, connect, get_fields, get_programs,
                                get_scholarships)
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
        assert get_fields(connection) == ["Computer Science"]


def test_real_database():
    with closing(connect(DATABASE)) as connection:
        assert len(get_programs(connection)) == 159
        assert len(get_scholarships(connection)) == 7
        assert get_fields(connection) == ["Computer Science", "Electrical Engineering",
                                          "Mechanical Engineering", "Statistics"]


def test_database_refuses_bad_data():
    bad_programs = [dict(university=""), dict(degree="BS"), dict(tuition_in_state=-1),
                    dict(acceptance_rate=1.5), dict(tuition_in_state="lots")]
    with closing(connect(":memory:")) as connection:
        for bad in bad_programs:
            with pytest.raises(sqlite3.IntegrityError):
                add_programs(connection, [make_program(**bad)])
        with pytest.raises(sqlite3.IntegrityError):
            add_scholarships(connection, [make_scholarship(min_gpa=4.5)])
        assert get_programs(connection) == []
