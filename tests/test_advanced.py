"""Week 14 - Advanced testing: property-based tests with Hypothesis.

Instead of picking inputs by hand, Hypothesis makes hundreds of random students and programs
and checks that some rules are always true.
"""
from hypothesis import given
from hypothesis import strategies as st

from gradmatch.fit import chance
from gradmatch.search import find_programs
from helpers import make_program, make_student

gpas = st.floats(min_value=0, max_value=4)
money = st.integers(min_value=0, max_value=100_000)
programs = st.lists(st.builds(make_program, state=st.sampled_from(["MI", "OH"]),
                              field=st.sampled_from(["Computer Science", "Data Science"]),
                              tuition_in_state=money, tuition_out_state=money,
                              living_cost=money, avg_gpa=gpas), max_size=10)


@given(gpas, gpas)
def test_chance_is_always_one_of_three_labels(gpa, avg_gpa):
    assert chance(gpa, avg_gpa) in {"Safety", "Match", "Reach"}


@given(programs, gpas, money)
def test_every_result_is_in_the_field_and_within_budget(program_list, gpa, budget):
    results = find_programs(program_list, make_student(gpa=gpa, budget=budget))
    assert all(r.program.field == "Computer Science" and r.cost <= budget for r in results)


@given(programs, gpas, money)
def test_results_are_always_sorted_by_cost(program_list, gpa, budget):
    costs = [r.cost for r in find_programs(program_list, make_student(gpa=gpa, budget=budget))]
    assert costs == sorted(costs)
