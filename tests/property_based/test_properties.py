from hypothesis import given
from hypothesis import strategies as st

from helpers import make_program, make_student
from programs import find_programs

money = st.integers(0, 100000)
programs = st.lists(st.builds(make_program, degree=st.sampled_from(["MS", "PhD"]),
                              tuition_out_state=money, living_cost=money,
                              acceptance_rate=st.floats(0, 1)), max_size=10)


@given(programs, st.floats(0, 4), money)
def test_results_always_fit_the_student(program_list, gpa, budget):
    results = find_programs(program_list, make_student(gpa=gpa, budget=budget, home_state="OH"))
    costs = [r.cost for r in results]
    assert all(r.program.degree == "MS" and r.chance in {"Safety", "Match", "Reach"} for r in results)
    assert all(cost <= budget for cost in costs)
    assert costs == sorted(costs)
