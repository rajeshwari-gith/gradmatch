from gradmatch.fit import SAFETY
from gradmatch.search import find_programs
from helpers import make_program, make_student

# Follows each value in find_programs() from where it is set to where it is used


def names(results):
    return [r.program.university for r in results]


def test_home_state_is_used_for_cost():
    in_state = find_programs([make_program()], make_student(home_state="MI"))[0]
    out_of_state = find_programs([make_program()], make_student(home_state="OH"))[0]
    assert (in_state.cost, out_of_state.cost) == (25000, 35000)


def test_cost_is_used_in_the_budget_check():
    assert find_programs([make_program(living_cost=25000)], make_student(budget=34999)) == []


def test_cost_is_stored_in_the_result():
    result = find_programs([make_program(living_cost=25000)], make_student(budget=35000))[0]
    assert result.cost == 35000


def test_gpa_is_used_for_chance():
    assert find_programs([make_program()], make_student(gpa=3.9))[0].chance == SAFETY


def test_results_are_sorted_cheapest_first():
    programs = [make_program(university="B", living_cost=20000),
                make_program(university="A", living_cost=5000)]
    assert names(find_programs(programs, make_student())) == ["A", "B"]


def test_same_cost_is_sorted_by_name():
    programs = [make_program(university="Zeta"), make_program(university="Alpha")]
    assert names(find_programs(programs, make_student())) == ["Alpha", "Zeta"]
