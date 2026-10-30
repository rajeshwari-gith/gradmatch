import pytest

from gradmatch.search import find_programs
from helpers import make_program, make_student

# One test per branch of find_programs() in search.py


def names(results):
    return [r.program.university for r in results]


@pytest.mark.parametrize("student", [make_student(gpa=4.2), make_student(gpa=-1)])
def test_bad_gpa_stops(student):
    with pytest.raises(ValueError):
        find_programs([make_program()], student)


def test_negative_budget_stops():
    with pytest.raises(ValueError):
        find_programs([make_program()], make_student(budget=-1))


def test_loop_runs_zero_times():
    assert find_programs([], make_student()) == []


def test_other_degree_is_skipped():
    assert find_programs([make_program(degree="PhD")], make_student()) == []


def test_other_field_is_skipped():
    assert find_programs([make_program(field="Statistics")], make_student()) == []


def test_state_not_chosen_is_skipped():
    assert find_programs([make_program(state="OH")], make_student(states=("IN",))) == []


def test_no_states_chosen_keeps_every_state():
    programs = [make_program(state="OH"), make_program(state="IN")]
    assert len(find_programs(programs, make_student(budget=100000))) == 2


def test_too_expensive_is_skipped():
    assert find_programs([make_program(living_cost=90000)], make_student()) == []


def test_program_is_kept():
    assert len(find_programs([make_program()], make_student())) == 1


def test_loop_takes_every_branch():
    programs = [make_program(degree="PhD"), make_program(field="Statistics"),
                make_program(state="WI"), make_program(living_cost=90000),
                make_program(university="Kept")]
    found = find_programs(programs, make_student(states=("MI",)))
    assert names(found) == ["Kept"]
