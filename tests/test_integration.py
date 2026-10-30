"""Week 9 - Integration testing.

These tests run the loader, cost, fit and search modules together on real files.
"""
import pytest

from gradmatch.data_loader import DataError, load_programs
from gradmatch.search import fields, find_programs
from helpers import DATA, GOOD_ROW, make_student, write_csv


def test_real_data_file_loads():
    programs = load_programs(DATA)
    assert len(programs) == 15


def test_real_data_has_both_fields():
    assert fields(load_programs(DATA)) == ["Computer Science", "Data Science"]


def test_loader_and_search_work_together_on_the_real_file():
    # Michigan student, CS, $40,000: only GVSU ($32,600) and Wayne State ($38,200) fit.
    results = find_programs(load_programs(DATA), make_student(budget=40000))
    assert [(r.program.university, r.cost) for r in results] == [
        ("Grand Valley State University", 32600),
        ("Wayne State University", 38200),
    ]


def test_every_real_program_gets_a_cost_and_chance():
    # With a huge budget, every CS program comes back with a cost and a label.
    results = find_programs(load_programs(DATA), make_student(budget=1_000_000))
    assert len(results) == 11
    assert all(r.cost > 0 and r.chance in {"Safety", "Match", "Reach"} for r in results)


def test_file_written_to_disk_is_searched(tmp_path):
    path = write_csv(tmp_path, GOOD_ROW, GOOD_ROW.replace("Computer Science", "Data Science"))
    results = find_programs(load_programs(path), make_student(field="Data Science"))
    assert len(results) == 1


@pytest.mark.parametrize("bad_row, problem", [
    (GOOD_ROW.replace(",3.5,", ",5.0,"), "avg_gpa"),
    (GOOD_ROW.replace("10000", "-1"), "negative"),
    (GOOD_ROW.replace("Test University", " "), "empty"),
    ("only,three,values", "wrong number"),
    (GOOD_ROW + ",extra", "wrong number"),
])
def test_bad_rows_stop_loading_with_a_clear_message(tmp_path, bad_row, problem):
    with pytest.raises(DataError, match=problem):
        load_programs(write_csv(tmp_path, bad_row))


def test_missing_column_is_reported(tmp_path):
    path = tmp_path / "programs.csv"
    path.write_text("university,program\nA,B\n", encoding="utf-8")
    with pytest.raises(DataError, match="field"):
        load_programs(path)
