"""Unit tests for cost.py.

Techniques: decision table (in-state vs out-of-state), boundary-value
analysis (cost exactly at, just under and just over the budget; cost
reduced to exactly 0), and property-based testing.
"""
import pytest
from hypothesis import given, strategies as st

from conftest import make_program
from gradmatch.cost import is_affordable, total_cost, tuition_for, yearly_cost

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

@pytest.mark.xfail(strict=True, reason="D-001: funded PhD tuition is not waived yet")
def test_funded_phd_pays_no_tuition():
    program = make_program(degree="PhD", tuition_in_state=56000, stipend=48000)
    assert yearly_cost(program, "MI", living_cost=29000) == 0
