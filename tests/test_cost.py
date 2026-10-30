import pytest
from hypothesis import given
from hypothesis import strategies as st

from gradmatch.cost import funding, tuition_for, yearly_cost
from helpers import make_program


def test_same_state_pays_in_state_tuition():
    assert tuition_for(make_program(state="MI"), "MI") == 10000


def test_other_state_pays_out_of_state_tuition():
    assert tuition_for(make_program(state="MI"), "OH") == 20000


@pytest.mark.parametrize("home_state, expected", [("MI", 25000), ("OH", 35000)])
def test_yearly_cost(home_state, expected):
    assert yearly_cost(make_program(), home_state) == expected


@given(st.integers(0, 100000), st.integers(0, 100000))
def test_yearly_cost_is_never_less_than_living_cost(tuition_amount, living):
    program = make_program(tuition_out_state=tuition_amount, living_cost=living)
    assert yearly_cost(program, "OH") >= living


@pytest.mark.parametrize("stipend, expected", [(10000, 5000), (15000, 0), (40000, 0)])
def test_stipend_waives_tuition_and_pays_living_cost(stipend, expected):
    assert yearly_cost(make_program(stipend=stipend), "OH") == expected


@pytest.mark.parametrize("stipend, expected", [
    (0, "No funding"), (1, "Partly funded"),
    (14999, "Partly funded"), (15000, "Fully funded"), (30000, "Fully funded"),
])
def test_funding(stipend, expected):
    assert funding(make_program(stipend=stipend)) == expected
