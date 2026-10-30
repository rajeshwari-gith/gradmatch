from datetime import date

import pytest

from gradmatch.data_loader import DataError, load_programs, load_scholarships
from helpers import (PROGRAM_HEADER, PROGRAM_ROW, PROGRAMS, SCHOLARSHIP_HEADER, SCHOLARSHIP_ROW,
                     SCHOLARSHIPS, write_csv)


def test_load_programs(tmp_path):
    program = load_programs(write_csv(tmp_path, PROGRAM_HEADER, PROGRAM_ROW))[0]
    assert program.university == "Test University"
    assert program.tuition_in_state == 10000
    assert program.acceptance_rate == 0.5


def test_load_scholarships(tmp_path):
    scholarship = load_scholarships(write_csv(tmp_path, SCHOLARSHIP_HEADER, SCHOLARSHIP_ROW))[0]
    assert scholarship.degrees == ("MS", "PhD")
    assert scholarship.citizenship == ("US", "PR")
    assert scholarship.deadline == date(2026, 12, 1)


def test_empty_file(tmp_path):
    assert load_programs(write_csv(tmp_path, PROGRAM_HEADER)) == []


def test_real_files_load():
    programs = load_programs(PROGRAMS)
    assert len(programs) == 133
    assert {p.degree for p in programs} == {"MS", "PhD"}
    assert len(load_scholarships(SCHOLARSHIPS)) == 7


@pytest.mark.parametrize("bad_row, message", [
    (PROGRAM_ROW.replace("10000", "lots"), "invalid literal"),
    (PROGRAM_ROW.replace(",MS,", ",BS,"), "degree"),
    (PROGRAM_ROW.replace("10000", "-1"), "negative"),
    (PROGRAM_ROW.replace("0.5", "1.5"), "acceptance_rate"),
    (PROGRAM_ROW.replace("Test University", " "), "university is empty"),
    ("only,three,values", "wrong number"),
    (PROGRAM_ROW + ",extra", "wrong number"),
])
def test_bad_program_row(tmp_path, bad_row, message):
    with pytest.raises(DataError, match=message):
        load_programs(write_csv(tmp_path, PROGRAM_HEADER, bad_row))


@pytest.mark.parametrize("bad_row, message", [
    (SCHOLARSHIP_ROW.replace("5000", "-5"), "negative"),
    (SCHOLARSHIP_ROW.replace("3.0", "4.5"), "min_gpa"),
    (SCHOLARSHIP_ROW.replace("2026-12-01", "Dec 1"), "isoformat"),
])
def test_bad_scholarship_row(tmp_path, bad_row, message):
    with pytest.raises(DataError, match=message):
        load_scholarships(write_csv(tmp_path, SCHOLARSHIP_HEADER, bad_row))


def test_error_gives_the_line_number(tmp_path):
    path = write_csv(tmp_path, PROGRAM_HEADER, PROGRAM_ROW, PROGRAM_ROW.replace("0.5", "high"))
    with pytest.raises(DataError, match="line 3"):
        load_programs(path)


def test_missing_column(tmp_path):
    with pytest.raises(DataError, match="degree"):
        load_programs(write_csv(tmp_path, "university,program", "A,B"))
