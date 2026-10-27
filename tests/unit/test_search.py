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
from gradmatch.search import matches_filters, search_programs, tuition_state

pytestmark = pytest.mark.unit

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

@given(budget=st.floats(min_value=0, max_value=100_000, allow_nan=False),
       stipends=st.lists(st.integers(min_value=0, max_value=60_000), max_size=8))
def test_no_result_is_ever_over_budget(budget, stipends):
    programs = [make_program(program_id=str(i), stipend=s) for i, s in enumerate(stipends)]
    for result in search_programs(make_profile(annual_budget=budget), programs, LIVING):
        assert result.yearly_cost <= budget


# ---- A program that does not fit must not stop the search ----
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
