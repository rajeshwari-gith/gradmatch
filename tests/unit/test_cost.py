"""Unit tests for cost.py.

Techniques: decision table (in-state vs out-of-state), boundary-value
analysis (cost exactly at, just under and just over the budget; cost
reduced to exactly 0), and property-based testing.
"""
import pytest
from hypothesis import given, strategies as st

from conftest import make_program
from gradmatch.cost import (cost_breakdown, is_affordable, total_cost, tuition_charged,
                            tuition_for, yearly_cost)

pytestmark = pytest.mark.unit

# make_program(): MI, in-state 15,000, out-of-state 30,000, 2 years, no stipend


# ---- Decision table: which tuition applies ----
# home state == program state | tuition used
# yes                         | in-state
# no                          | out-of-state

def test_same_state_uses_in_state_tuition():
    assert tuition_for(make_program(state="MI"), "MI") == 15000


def test_different_state_uses_out_of_state_tuition():
    assert tuition_for(make_program(state="MI"), "OH") == 30000


# ---- Yearly and total cost ----

def test_yearly_cost_adds_living_cost():
    assert yearly_cost(make_program(), "MI", living_cost=12000) == 27000


def test_yearly_cost_subtracts_stipend():
    assert yearly_cost(make_program(stipend=5000), "MI", living_cost=12000) == 22000


def test_stipend_equal_to_cost_gives_zero():
    assert yearly_cost(make_program(stipend=27000), "MI", living_cost=12000) == 0


def test_stipend_larger_than_cost_never_goes_below_zero():
    assert yearly_cost(make_program(stipend=40000), "MI", living_cost=12000) == 0


def test_total_cost_multiplies_by_duration():
    program = make_program(duration_years=1.5)
    assert total_cost(program, "OH", living_cost=10000) == 60000


# ---- Boundary-value analysis: budget vs yearly cost (27,000) ----

@pytest.mark.parametrize("budget, expected", [
    (26999.99, False),   # just under the cost
    (27000.00, True),    # exactly the cost
    (27000.01, True),    # just over the cost
])
def test_affordability_boundary(budget, expected):
    assert is_affordable(make_program(), "MI", 12000, budget) is expected


def test_zero_budget_affords_fully_funded_program():
    assert is_affordable(make_program(stipend=50000), "MI", 12000, annual_budget=0)


# ---- Property-based tests ----

money = st.floats(min_value=0, max_value=200_000, allow_nan=False)


@given(tuition=money, living=money, stipend=money)
def test_yearly_cost_is_never_negative(tuition, living, stipend):
    program = make_program(tuition_in_state=tuition, stipend=stipend)
    assert yearly_cost(program, "MI", living) >= 0


@given(stipend_a=money, stipend_b=money)
def test_more_stipend_never_costs_more(stipend_a, stipend_b):
    low, high = sorted([stipend_a, stipend_b])
    cost_low_stipend = yearly_cost(make_program(stipend=low), "MI", 12000)
    cost_high_stipend = yearly_cost(make_program(stipend=high), "MI", 12000)
    assert cost_high_stipend <= cost_low_stipend


# ---- Defect D-001: a funded PhD should not be charged tuition ----
# A PhD program that pays a stipend normally waives tuition. The first version
# of yearly_cost() subtracted the stipend from tuition + living cost, so a
# "Fully Funded" PhD (stipend above living cost) still showed a cost of
# tuition + living - stipend, e.g. $37,000 for a $56,000-tuition program.

def test_funded_phd_pays_no_tuition():
    program = make_program(degree="PhD", tuition_in_state=56000, stipend=48000)
    assert yearly_cost(program, "MI", living_cost=29000) == 0


# Decision table for tuition_charged():
# degree | stipend > 0 | tuition charged
# PhD    | yes         | 0 (waived)
# PhD    | no          | tuition
# MS     | yes         | tuition
# MS     | no          | tuition

def test_phd_with_stipend_has_tuition_waived():
    assert tuition_charged(make_program(degree="PhD", stipend=30000), "MI") == 0


def test_phd_without_stipend_pays_tuition():
    assert tuition_charged(make_program(degree="PhD", stipend=0), "MI") == 15000


@pytest.mark.parametrize("stipend", [0, 5000])
def test_ms_always_pays_tuition(stipend):
    assert tuition_charged(make_program(degree="MS", stipend=stipend), "MI") == 15000


@pytest.mark.parametrize("stipend, waived", [(0, False), (1, True)])
def test_phd_waiver_boundary_at_zero_stipend(stipend, waived):
    charged = tuition_charged(make_program(degree="PhD", stipend=stipend), "MI")
    assert (charged == 0) is waived


def test_partially_funded_phd_pays_only_the_gap_in_living_cost():
    program = make_program(degree="PhD", tuition_in_state=56000, stipend=10000)
    assert yearly_cost(program, "MI", living_cost=29000) == 19000


def test_funded_phd_out_of_state_student_also_pays_no_tuition():
    program = make_program(degree="PhD", tuition_out_state=60000, stipend=42000)
    assert yearly_cost(program, "OH", living_cost=18200) == 0


def test_ms_with_assistantship_still_subtracts_stipend_from_all_costs():
    program = make_program(degree="MS", tuition_in_state=15000, stipend=5000)
    assert yearly_cost(program, "MI", living_cost=12000) == 22000


# ---- cost_breakdown: the pieces add up to the yearly cost ----

def test_cost_breakdown_of_an_ms_program():
    program = make_program(tuition_in_state=15000, stipend=2000, duration_years=2)
    assert cost_breakdown(program, "MI", living_cost=12000) == {
        "tuition": 15000, "living": 12000, "stipend": 2000,
        "yearly": 25000, "total": 50000, "years": 2}


def test_cost_breakdown_of_a_funded_phd_has_no_tuition():
    program = make_program(degree="PhD", tuition_in_state=56000, stipend=48000, duration_years=5)
    breakdown = cost_breakdown(program, "MI", living_cost=29000)
    assert breakdown["tuition"] == 0
    assert breakdown["yearly"] == 0 and breakdown["total"] == 0


@given(tuition=money, living=money, stipend=money)
def test_cost_breakdown_pieces_add_up_to_the_yearly_cost(tuition, living, stipend):
    program = make_program(tuition_in_state=tuition, stipend=stipend)
    b = cost_breakdown(program, "MI", living)
    assert b["yearly"] == max(b["tuition"] + b["living"] - b["stipend"], 0.0)
