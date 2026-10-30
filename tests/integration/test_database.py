import sqlite3
from contextlib import closing

import pytest

from database import add_programs, add_scholarships, connect, get_programs, get_scholarships
from helpers import DATABASE, make_program, make_scholarship


def test_database(tmp_path):
    # save and read back
    with closing(connect(tmp_path / "test.db")) as connection:
        add_programs(connection, [make_program()])
        add_scholarships(connection, [make_scholarship()])
        assert get_programs(connection) == [make_program()]
        assert get_scholarships(connection) == [make_scholarship()]

        # REQ-8: the database refuses bad data
        for bad in [dict(degree="BS"), dict(tuition_in_state=-1), dict(acceptance_rate=1.5),
                    dict(tuition_in_state="lots")]:
            with pytest.raises(sqlite3.IntegrityError):
                add_programs(connection, [make_program(**bad)])
        with pytest.raises(sqlite3.IntegrityError):
            add_scholarships(connection, [make_scholarship(min_gpa=4.5)])

    # the real database
    with closing(connect(DATABASE)) as connection:
        assert len(get_programs(connection)) == 159
        assert len(get_scholarships(connection)) == 7
