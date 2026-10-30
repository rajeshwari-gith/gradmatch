"""Week 2 - Unit testing.

Each test checks one function on its own, with simple values we can work out by hand.
"""
import pytest

from gradmatch.cost import tuition, yearly_cost
from gradmatch.data_loader import DataError, load_programs, parse_row
from gradmatch.fit import MATCH, REACH, SAFETY, chance, check_gpa
from gradmatch.search import fields, find_programs
from helpers import GOOD_ROW, HEADER, make_program, make_student, write_csv


# ---- cost.py ----

def test_student_from_the_same_state_pays_in_state_tuition():
    assert tuition(make_program(state="MI"), "MI") == 10000


def test_student_from_another_state_pays_out_of_state_tuition():
    assert tuition(make_program(state="MI"), "OH") == 20000


def test_yearly_cost_is_tuition_plus_living_cost():
    assert yearly_cost(make_program(), "MI") == 10000 + 15000


# ---- fit.py ----

def test_gpa_well_above_average_is_safety():
    assert chance(3.9, 3.5) == SAFETY


def test_gpa_near_average_is_match():
    assert chance(3.5, 3.5) == MATCH


def test_gpa_well_below_average_is_reach():
    assert chance(3.0, 3.5) == REACH


def test_check_gpa_accepts_a_normal_gpa():
    check_gpa(3.2)  # no error means it passed


def test_check_gpa_rejects_a_gpa_above_4():
    with pytest.raises(ValueError):
        check_gpa(4.5)


# ---- data_loader.py ----

def test_parse_row_turns_text_into_numbers():
    program = parse_row(dict(zip(HEADER.strip().split(","), GOOD_ROW.split(","))))
    assert program.tuition_in_state == 10000
    assert program.avg_gpa == 3.5


def test_load_programs_reads_every_row(tmp_path):
    path = write_csv(tmp_path, GOOD_ROW, GOOD_ROW)
    assert len(load_programs(path)) == 2


def test_load_programs_stops_at_a_bad_row(tmp_path):
    path = write_csv(tmp_path, GOOD_ROW.replace("10000", "lots"))
    with pytest.raises(DataError):
        load_programs(path)


# ---- search.py ----

def test_find_programs_returns_a_matching_program():
    results = find_programs([make_program()], make_student())
    assert [r.program.university for r in results] == ["Test University"]


def test_find_programs_gives_cost_and_chance():
    result = find_programs([make_program()], make_student())[0]
    assert result.cost == 25000
    assert result.chance == MATCH


def test_fields_lists_each_field_once_in_order():
    programs = [make_program(field="Data Science"), make_program(), make_program()]
    assert fields(programs) == ["Computer Science", "Data Science"]
