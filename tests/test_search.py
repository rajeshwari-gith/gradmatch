from unittest.mock import Mock

import pytest
from hypothesis import given
from hypothesis import strategies as st

from gradmatch import search
from gradmatch.cost import yearly_cost
from gradmatch.fit import MATCH, SAFETY
from gradmatch.search import fields, find_programs
from helpers import make_program, make_student


def names(results):
    return [r.program.university for r in results]


def test_matching_program_is_found():
    result = find_programs([make_program()], make_student())[0]
    assert result.program.university == "Test University"
    assert result.cost == 25000
    assert result.chance == MATCH


def test_no_programs():
    assert find_programs([], make_student()) == []


def test_other_degree_is_left_out():
    assert find_programs([make_program(degree="PhD")], make_student()) == []


def test_other_field_is_left_out():
    assert find_programs([make_program(field="Mechanical Engineering")], make_student()) == []


def test_too_expensive_is_left_out():
    assert find_programs([make_program(living_cost=90000)], make_student()) == []


def test_mixed_list():
    programs = [make_program(degree="PhD"), make_program(field="Mechanical Engineering"),
                make_program(living_cost=90000), make_program(university="Kept")]
    assert names(find_programs(programs, make_student())) == ["Kept"]


@pytest.mark.parametrize("budget, found", [(25000, 1), (25001, 1), (24999, 0), (0, 0)])
def test_budget_edges(budget, found):
    assert len(find_programs([make_program()], make_student(budget=budget))) == found


def test_cheapest_first():
    programs = [make_program(university="B", living_cost=20000),
                make_program(university="A", living_cost=5000)]
    assert names(find_programs(programs, make_student())) == ["A", "B"]


def test_home_state_changes_the_cost():
    in_state = find_programs([make_program()], make_student(home_state="MI"))[0]
    out_of_state = find_programs([make_program()], make_student(home_state="OH"))[0]
    assert (in_state.cost, out_of_state.cost) == (25000, 35000)


def test_student_gpa_is_used_for_chance():
    result = find_programs([make_program()], make_student(gpa=3.9))[0]
    assert result.chance == SAFETY


@pytest.mark.parametrize("student", [make_student(gpa=4.2), make_student(gpa=-1),
                                     make_student(budget=-1)])
def test_bad_input(student):
    with pytest.raises(ValueError):
        find_programs([make_program()], student)


def test_cost_only_worked_out_for_matching_programs(monkeypatch):
    spy = Mock(wraps=yearly_cost)
    monkeypatch.setattr(search, "yearly_cost", spy)
    programs = [make_program(), make_program(degree="PhD"), make_program()]
    find_programs(programs, make_student())
    assert spy.call_count == 2


def test_fields():
    programs = [make_program(field="Mechanical Engineering"), make_program(), make_program()]
    assert fields(programs) == ["Computer Science", "Mechanical Engineering"]


money = st.integers(0, 100000)
program_lists = st.lists(st.builds(make_program, state=st.sampled_from(["MI", "OH"]),
                                   degree=st.sampled_from(["MS", "PhD"]),
                                   tuition_in_state=money, tuition_out_state=money,
                                   living_cost=money, acceptance_rate=st.floats(0, 1)), max_size=10)


@given(program_lists, st.floats(0, 4), money)
def test_results_always_match_and_are_in_order(programs, gpa, budget):
    results = find_programs(programs, make_student(gpa=gpa, budget=budget))
    costs = [r.cost for r in results]
    assert all(r.program.degree == "MS" for r in results)
    assert all(cost <= budget for cost in costs)
    assert costs == sorted(costs)
