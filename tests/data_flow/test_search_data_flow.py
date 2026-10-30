from fit import SAFETY
from search import find_programs
from helpers import make_program, make_student

# follows each value in find_programs() from where it is set to where it is used


def test_req3_home_state_is_used_for_cost():
    in_state = find_programs([make_program()], make_student(home_state="MI"))[0]
    out_of_state = find_programs([make_program()], make_student(home_state="OH"))[0]
    assert (in_state.cost, out_of_state.cost) == (25000, 35000)


def test_req2_cost_is_used_in_budget_check_and_result():
    assert find_programs([make_program()], make_student(budget=24999)) == []
    assert find_programs([make_program()], make_student(budget=25000))[0].cost == 25000


def test_req4_gpa_is_used_for_chance():
    assert find_programs([make_program()], make_student(gpa=3.9))[0].chance == SAFETY


def test_req2_results_are_sorted():
    programs = [make_program(university="C", living_cost=20000),
                make_program(university="B"), make_program(university="A")]
    found = find_programs(programs, make_student())
    assert [r.program.university for r in found] == ["A", "B", "C"]
