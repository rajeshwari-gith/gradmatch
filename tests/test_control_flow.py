"""Week 5 - Control-flow testing.

The control-flow graphs for chance() and find_programs() are drawn in docs/control-and-data-flow.md.
Each test below follows one path through a graph. Node numbers match the drawings.
"""
import pytest

from gradmatch.fit import MATCH, REACH, SAFETY, chance
from gradmatch.search import find_programs
from helpers import make_program, make_student


# ---- chance(): 4 paths ----

def test_chance_path_1_bad_gpa_raises():
    # 1 -> raise
    with pytest.raises(ValueError):
        chance(5.0, 3.5)


def test_chance_path_2_safety():
    # 1 -> 2 -> 3 (true) -> 4
    assert chance(3.8, 3.5) == SAFETY


def test_chance_path_3_match():
    # 1 -> 2 -> 3 (false) -> 5 (true) -> 6
    assert chance(3.5, 3.5) == MATCH


def test_chance_path_4_reach():
    # 1 -> 2 -> 3 (false) -> 5 (false) -> 7
    assert chance(3.0, 3.5) == REACH


# ---- find_programs(): every branch ----

def test_search_path_bad_gpa_raises():
    # 1 (bad GPA) -> raise
    with pytest.raises(ValueError):
        find_programs([make_program()], make_student(gpa=-1))


def test_search_path_negative_budget_raises():
    # 1 -> 2 (true) -> raise
    with pytest.raises(ValueError):
        find_programs([make_program()], make_student(budget=-1))


def test_search_path_loop_runs_zero_times():
    # 1 -> 2 -> 3 -> 4 (no programs) -> 9
    assert find_programs([], make_student()) == []


def test_search_path_wrong_field_is_skipped():
    # 4 -> 5 (true: other field) -> back to 4
    assert find_programs([make_program(field="Data Science")], make_student()) == []


def test_search_path_too_expensive_is_skipped():
    # 4 -> 5 (false) -> 6 -> 7 (true: over budget) -> back to 4
    assert find_programs([make_program(living_cost=90000)], make_student()) == []


def test_search_path_program_is_kept():
    # 4 -> 5 (false) -> 6 -> 7 (false) -> 8 -> back to 4 -> 9
    assert len(find_programs([make_program()], make_student())) == 1


def test_search_loop_runs_many_times_through_every_branch():
    # The loop runs 3 times and takes all three branches once.
    programs = [make_program(field="Data Science"), make_program(living_cost=90000),
                make_program(university="Kept")]
    results = find_programs(programs, make_student())
    assert [r.program.university for r in results] == ["Kept"]
