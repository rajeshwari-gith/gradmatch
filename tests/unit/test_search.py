"""Unit tests for search.py.

Techniques: equivalence partitioning on each filter (match / no match),
boundary-value analysis on the budget, checks on sort order, and a
property-based test that no result is ever over budget.
"""
import pytest
from hypothesis import given, strategies as st

from conftest import make_profile, make_program
from gradmatch.fit import MATCH
from gradmatch.funding import FULLY_FUNDED, SELF_FUNDED
from gradmatch.search import matches_filters, school_rates, search_programs, tuition_state

pytestmark = pytest.mark.unit

# In plain words: search is the heart of the app. These tests give it a handful of tiny programs
# and check three things: the right programs are kept, the wrong ones are dropped, and the
# order is right (MS cheapest first, PhD best funded first).

LIVING = {"MI": 12000, "CA": 25000, "TX": 14000, "OH": 11000}


def ids(results):
    return [r.program.program_id for r in results]


# ---- Filters: equivalence partitioning ----

def test_matching_program_passes_filters():
    assert matches_filters(make_profile(), make_program())


def test_different_field_is_filtered_out():
    assert not matches_filters(make_profile(), make_program(field="Biology"))


def test_different_degree_is_filtered_out():
    assert not matches_filters(make_profile(degree_sought="PhD"), make_program(degree="MS"))


def test_no_preferred_states_means_any_state():
    assert matches_filters(make_profile(preferred_states=()), make_program(state="CA"))


def test_program_in_preferred_state_passes():
    profile = make_profile(preferred_states=("CA", "TX"))
    assert matches_filters(profile, make_program(state="TX"))


def test_program_outside_preferred_states_is_filtered_out():
    profile = make_profile(preferred_states=("CA", "TX"))
    assert not matches_filters(profile, make_program(state="MI"))


# ---- Budget boundary (in-state MI program costs 15,000 + 12,000 = 27,000) ----

@pytest.mark.parametrize("budget, found", [(26999, False), (27000, True), (27001, True)])
def test_budget_boundary(budget, found):
    results = search_programs(make_profile(annual_budget=budget), [make_program()], LIVING)
    assert (len(results) == 1) is found


# ---- Result contents ----
# Why: each result must carry the cost, the fit label and the funding label the card will show.

def test_result_has_cost_fit_and_funding():
    [result] = search_programs(make_profile(gpa=3.40), [make_program()], LIVING)
    assert result.yearly_cost == 27000
    assert result.total_cost == 54000
    assert result.fit == MATCH
    assert result.funding == SELF_FUNDED


def test_out_of_state_student_pays_out_of_state_rate():
    profile = make_profile(home_state="OH", annual_budget=50000)
    [result] = search_programs(profile, [make_program()], LIVING)
    assert result.yearly_cost == 30000 + 12000


def test_only_programs_passing_filters_are_returned():
    programs = [make_program(program_id="CS"), make_program(program_id="BIO", field="Biology")]
    assert ids(search_programs(make_profile(), programs, LIVING)) == ["CS"]


def test_empty_program_list_gives_no_results():
    assert search_programs(make_profile(), [], LIVING) == []


def test_missing_living_cost_raises_clear_error():
    with pytest.raises(ValueError, match="No living cost found for state WA"):
        search_programs(make_profile(), [make_program(state="WA")], LIVING)


# ---- Sort order ----
# Why: students read from the top, so the most useful program must come first.

def test_ms_results_sorted_cheapest_first():
    programs = [
        make_program(program_id="CA1", state="CA"),   # 30,000 + 25,000
        make_program(program_id="MI1", state="MI"),   # 15,000 + 12,000 (in-state)
        make_program(program_id="OH1", state="OH"),   # 30,000 + 11,000
    ]
    results = search_programs(make_profile(annual_budget=100000), programs, LIVING)
    assert ids(results) == ["MI1", "OH1", "CA1"]


def test_phd_results_sorted_by_stipend_left_after_living_cost():
    profile = make_profile(degree_sought="PhD", annual_budget=100000)
    programs = [
        make_program(program_id="A", degree="PhD", state="CA", stipend=30000),  # +5,000
        make_program(program_id="B", degree="PhD", state="TX", stipend=30000),  # +16,000
        make_program(program_id="C", degree="PhD", state="MI", stipend=0),      # -12,000
    ]
    results = search_programs(profile, programs, LIVING)
    assert ids(results) == ["B", "A", "C"]
    assert results[0].funding == FULLY_FUNDED


# ---- Property-based test ----
# Why: whatever budget and stipends Hypothesis invents, no result may ever cost more than the budget.

@given(budget=st.floats(min_value=0, max_value=100_000, allow_nan=False),
       stipends=st.lists(st.integers(min_value=0, max_value=60_000), max_size=8))
def test_no_result_is_ever_over_budget(budget, stipends):
    programs = [make_program(program_id=str(i), stipend=s) for i, s in enumerate(stipends)]
    for result in search_programs(make_profile(annual_budget=budget), programs, LIVING):
        assert result.yearly_cost <= budget


# ---- A program that does not fit must not stop the search ----
# (A mutation-testing test: a bug that stopped at the first bad program survived until we added these.)
# Found by mutation testing: every earlier test listed the matching programs first.

def test_a_program_in_another_field_before_a_matching_one_does_not_stop_the_search():
    programs = [make_program(program_id="BIO", field="Biology"),
                make_program(program_id="CS")]
    assert ids(search_programs(make_profile(), programs, LIVING)) == ["CS"]


def test_a_too_expensive_program_before_an_affordable_one_does_not_stop_the_search():
    programs = [make_program(program_id="PRICEY", state="CA"),     # 30,000 + 25,000
                make_program(program_id="CHEAP", state="MI")]      # 15,000 + 12,000
    results = search_programs(make_profile(annual_budget=30000), programs, LIVING)
    assert ids(results) == ["CHEAP"]


# ---- Defect D-003: international students are not residents of any state ----
# The first version charged in-state tuition to anyone whose "home state" matched
# the program's state, so an international student who picked MI paid the in-state
# rate at a Michigan university. Public universities charge international students
# the non-resident rate.

def test_international_student_pays_out_of_state_tuition_even_with_a_matching_home_state():
    profile = make_profile(citizenship="International", toefl=100, home_state="MI",
                           annual_budget=100000)
    [result] = search_programs(profile, [make_program(state="MI")], LIVING)
    assert result.yearly_cost == 30000 + 12000      # out-of-state tuition + MI living cost


# Decision table for tuition_state():
# citizenship   | home state | tuition state
# US            | MI         | MI   (can get the in-state rate in MI)
# PR            | MI         | MI
# International | MI         | None (never in-state)

@pytest.mark.parametrize("citizenship, expected", [("US", "MI"), ("PR", "MI"), ("International", None)])
def test_tuition_state_depends_on_citizenship(citizenship, expected):
    profile = make_profile(citizenship=citizenship, toefl=100, home_state="MI")
    assert tuition_state(profile) == expected


def test_us_student_in_the_programs_state_still_pays_in_state_tuition():
    [result] = search_programs(make_profile(annual_budget=100000), [make_program(state="MI")], LIVING)
    assert result.yearly_cost == 15000 + 12000


def test_permanent_resident_in_the_programs_state_pays_in_state_tuition():
    profile = make_profile(citizenship="PR", annual_budget=100000)
    [result] = search_programs(profile, [make_program(state="MI")], LIVING)
    assert result.yearly_cost == 15000 + 12000


def test_international_total_cost_also_uses_the_out_of_state_rate():
    profile = make_profile(citizenship="International", toefl=100, annual_budget=100000)
    [result] = search_programs(profile, [make_program(state="MI", duration_years=2)], LIVING)
    assert result.total_cost == (30000 + 12000) * 2


# ---- Programs with unpublished values still appear ----

def test_programs_with_unpublished_values_are_found_with_an_estimated_chance():
    program = make_program(avg_gpa=None, stipend=None, application_deadline=None, source="ipeds")
    [result] = search_programs(make_profile(), [program], LIVING)
    assert (result.fit, result.funding) == ("Match", "Funding unknown")   # 40% accepted, GPA 3.5
    assert result.yearly_cost == 27000


def test_a_program_with_no_chance_at_all_is_left_out():
    program = make_program(avg_gpa=None, acceptance_rate=None)
    assert search_programs(make_profile(), [program], LIVING) == []


def test_a_graduate_program_borrows_its_universitys_rate():
    college = make_program(program_id="UG", degree="BS", acceptance_rate=0.75)
    masters = make_program(program_id="MS1", avg_gpa=None, acceptance_rate=None)
    assert school_rates([college, masters]) == {("Test University", "MI"): 0.75}
    [result] = search_programs(make_profile(), [college, masters], LIVING)
    assert (result.program.program_id, result.fit) == ("MS1", "Safety")


def test_only_bachelors_rows_with_a_rate_give_a_university_rate():
    rows = [make_program(degree="BS", acceptance_rate=None), make_program(degree="MS", acceptance_rate=0.3)]
    assert school_rates(rows) == {}


def test_phd_sort_treats_an_unpublished_stipend_as_zero():
    profile = make_profile(degree_sought="PhD", annual_budget=100000)
    programs = [make_program(program_id="NONE", degree="PhD", stipend=None),
                make_program(program_id="PAID", degree="PhD", stipend=10000)]
    assert ids(search_programs(profile, programs, LIVING)) == ["PAID", "NONE"]


# ---- Bachelor's programs ----

def test_bachelors_search_finds_bachelors_programs_cheapest_first():
    programs = [make_program(program_id="CA", degree="BS", state="CA", duration_years=4),
                make_program(program_id="MI", degree="BS", state="MI", duration_years=4),
                make_program(program_id="MS", degree="MS")]
    results = search_programs(make_profile(degree_sought="BS", annual_budget=100000), programs, LIVING)
    assert ids(results) == ["MI", "CA"]
    assert results[0].total_cost == (15000 + 12000) * 4


# ---- Test scores reach the fit label ----

def test_a_students_sat_decides_the_fit_of_a_college():
    college = make_program(degree="BS", sat_25=1100, sat_75=1300)
    results = search_programs(make_profile(degree_sought="BS", sat=1350, annual_budget=100000), [college], LIVING)
    assert results[0].fit == "Safety"
    results = search_programs(make_profile(degree_sought="BS", act=20, annual_budget=100000),
                              [make_program(degree="BS", act_25=24, act_75=29)], LIVING)
    assert results[0].fit == "Reach"


# ---- More property-based tests ----
# Why: rules that must hold for ANY budget and any list of programs, not just the examples above.

@given(low=st.floats(min_value=0, max_value=100_000, allow_nan=False),
       high=st.floats(min_value=0, max_value=100_000, allow_nan=False),
       states=st.lists(st.sampled_from(["MI", "CA", "TX", "OH"]), min_size=1, max_size=8))
def test_a_bigger_budget_never_removes_a_result(low, high, states):
    low, high = sorted([low, high])
    programs = [make_program(program_id=str(i), state=s) for i, s in enumerate(states)]
    few = set(ids(search_programs(make_profile(annual_budget=low), programs, LIVING)))
    many = set(ids(search_programs(make_profile(annual_budget=high), programs, LIVING)))
    assert few <= many


@given(states=st.lists(st.sampled_from(["MI", "CA", "TX", "OH"]), max_size=8))
def test_ms_results_always_come_back_cheapest_first(states):
    programs = [make_program(program_id=str(i), state=s) for i, s in enumerate(states)]
    costs = [r.yearly_cost for r in search_programs(make_profile(annual_budget=100_000), programs, LIVING)]
    assert costs == sorted(costs)


@given(states=st.lists(st.sampled_from(["MI", "CA", "TX", "OH"]), max_size=8))
def test_every_result_matches_the_students_field_and_degree(states):
    programs = [make_program(program_id=str(i), state=s, field=("Biology" if i % 2 else "Computer Science"))
                for i, s in enumerate(states)]
    for r in search_programs(make_profile(annual_budget=100_000), programs, LIVING):
        assert (r.program.field, r.program.degree) == ("Computer Science", "MS")


def test_a_program_with_no_chance_does_not_stop_the_search():
    programs = [make_program(program_id="NONE", avg_gpa=None, acceptance_rate=None),
                make_program(program_id="NEXT")]
    assert ids(search_programs(make_profile(), programs, LIVING)) == ["NEXT"]
