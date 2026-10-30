"""Week 8 - Functional (black-box) testing.

These tests come from the requirements R1-R7 in docs/test-plan.md, not from reading the code.
"""
import pytest

from gradmatch.data_loader import DataError, load_programs
from gradmatch.fit import MATCH, REACH, SAFETY
from gradmatch.search import find_programs
from helpers import GOOD_ROW, make_program, make_student, write_csv

PROGRAMS = [
    make_program(university="CS Cheap", living_cost=5000),
    make_program(university="CS Dear", living_cost=28000),
    make_program(university="DS School", field="Data Science"),
    make_program(university="Ohio CS", state="OH"),
]


def names(results):
    return [r.program.university for r in results]


def test_r1_only_the_chosen_field_is_shown():
    results = find_programs(PROGRAMS, make_student(field="Data Science"))
    assert names(results) == ["DS School"]


def test_r2_only_programs_within_the_budget_are_shown():
    # A Michigan student with $30,000 can afford CS Cheap ($15,000) but not the others.
    results = find_programs(PROGRAMS, make_student(budget=30000))
    assert names(results) == ["CS Cheap"]


def test_r3_cost_uses_in_state_tuition_for_the_home_state():
    results = find_programs(PROGRAMS, make_student(home_state="OH", budget=100000))
    costs = {r.program.university: r.cost for r in results}
    assert costs["Ohio CS"] == 10000 + 15000      # in-state
    assert costs["CS Cheap"] == 20000 + 5000      # out-of-state


def test_r4_results_are_sorted_cheapest_first():
    results = find_programs(PROGRAMS, make_student(budget=100000))
    costs = [r.cost for r in results]
    assert costs == sorted(costs)


@pytest.mark.parametrize("gpa, expected", [(4.0, SAFETY), (3.5, MATCH), (2.5, REACH)])
def test_r5_chance_label(gpa, expected):
    result = find_programs([make_program(avg_gpa=3.5)], make_student(gpa=gpa))[0]
    assert result.chance == expected


@pytest.mark.parametrize("student", [make_student(gpa=4.2), make_student(budget=-10)],
                         ids=["gpa-too-high", "negative-budget"])
def test_r6_bad_input_is_rejected(student):
    with pytest.raises(ValueError):
        find_programs(PROGRAMS, student)


def test_r7_bad_data_file_names_the_line(tmp_path):
    path = write_csv(tmp_path, GOOD_ROW, GOOD_ROW.replace("3.5", "high"))
    with pytest.raises(DataError, match="line 3"):
        load_programs(path)
