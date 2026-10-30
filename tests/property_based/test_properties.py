from hypothesis import given
from hypothesis import strategies as st

from gradmatch.fit import MATCH, REACH, SAFETY, chance
from gradmatch.search import find_programs
from helpers import make_program, make_student

money = st.integers(0, 100000)
programs = st.lists(st.builds(make_program, state=st.sampled_from(["MI", "OH"]),
                              degree=st.sampled_from(["MS", "PhD"]),
                              tuition_in_state=money, tuition_out_state=money, living_cost=money,
                              acceptance_rate=st.floats(0, 1)), max_size=10)


@given(st.floats(0, 4), st.floats(0, 1))
def test_chance_is_always_one_of_three(gpa, rate):
    assert chance(gpa, rate) in {SAFETY, MATCH, REACH}


@given(programs, st.floats(0, 4), money)
def test_results_always_fit_the_student(program_list, gpa, budget):
    results = find_programs(program_list, make_student(gpa=gpa, budget=budget))
    costs = [r.cost for r in results]
    assert all(r.program.degree == "MS" for r in results)
    assert all(cost <= budget for cost in costs)
    assert costs == sorted(costs)
