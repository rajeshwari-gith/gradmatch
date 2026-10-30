import pytest

from gradmatch.data_loader import DataError, load_programs, parse_row
from helpers import DATA, GOOD_ROW, HEADER, write_csv


def test_parse_row():
    program = parse_row(dict(zip(HEADER.strip().split(","), GOOD_ROW.split(","))))
    assert program.university == "Test University"
    assert program.tuition_in_state == 10000
    assert program.avg_gpa == 3.5


def test_load_two_rows(tmp_path):
    assert len(load_programs(write_csv(tmp_path, GOOD_ROW, GOOD_ROW))) == 2


def test_load_empty_file(tmp_path):
    assert load_programs(write_csv(tmp_path)) == []


def test_load_real_file():
    programs = load_programs(DATA)
    assert len(programs) == 15
    assert {p.field for p in programs} == {"Computer Science", "Data Science"}


@pytest.mark.parametrize("bad_row, message", [
    (GOOD_ROW.replace("10000", "lots"), "invalid literal"),
    (GOOD_ROW.replace(",3.5,", ",5.0,"), "avg_gpa"),
    (GOOD_ROW.replace("10000", "-1"), "negative"),
    (GOOD_ROW.replace("Test University", " "), "empty"),
    ("only,three,values", "wrong number"),
    (GOOD_ROW + ",extra", "wrong number"),
])
def test_bad_row(tmp_path, bad_row, message):
    with pytest.raises(DataError, match=message):
        load_programs(write_csv(tmp_path, bad_row))


def test_error_gives_the_line_number(tmp_path):
    path = write_csv(tmp_path, GOOD_ROW, GOOD_ROW.replace("3.5", "high"))
    with pytest.raises(DataError, match="line 3"):
        load_programs(path)


def test_missing_column(tmp_path):
    path = tmp_path / "programs.csv"
    path.write_text("university,program\nA,B\n", encoding="utf-8")
    with pytest.raises(DataError, match="field"):
        load_programs(path)
