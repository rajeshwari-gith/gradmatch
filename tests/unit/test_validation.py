"""Unit tests for validation.py.

Techniques: equivalence partitioning (valid / invalid classes) and
boundary-value analysis (values just below, on, and just above each limit).
"""
import pytest

from conftest import make_profile
from gradmatch.validation import is_valid, validate_profile

pytestmark = pytest.mark.unit


# The starting point: a normal student has no errors at all.
def test_valid_profile_has_no_errors():
    assert validate_profile(make_profile()) == []
    assert is_valid(make_profile())


# ---- GPA: boundary-value analysis around 0.0 and 4.0 ----

@pytest.mark.parametrize("gpa", [0.0, 0.01, 3.99, 4.0])
def test_gpa_on_or_inside_boundary_is_valid(gpa):
    assert is_valid(make_profile(gpa=gpa))


@pytest.mark.parametrize("gpa", [-0.01, 4.01])
def test_gpa_just_outside_boundary_is_invalid(gpa):
    assert "GPA must be between 0.0 and 4.0." in validate_profile(make_profile(gpa=gpa))


# ---- GRE: optional; boundary-value analysis around 260 and 340 ----

@pytest.mark.parametrize("gre", [None, 260, 261, 339, 340])
def test_gre_missing_or_in_range_is_valid(gre):
    assert is_valid(make_profile(gre=gre))


@pytest.mark.parametrize("gre", [259, 341])
def test_gre_just_outside_range_is_invalid(gre):
    assert "GRE score must be between 260 and 340." in validate_profile(make_profile(gre=gre))


# ---- TOEFL: boundary-value analysis around 0 and 120 ----

@pytest.mark.parametrize("toefl", [0, 120])
def test_toefl_on_boundary_is_valid(toefl):
    assert is_valid(make_profile(toefl=toefl))


@pytest.mark.parametrize("toefl", [-1, 121])
def test_toefl_just_outside_range_is_invalid(toefl):
    assert "TOEFL score must be between 0 and 120." in validate_profile(make_profile(toefl=toefl))


# ---- Budget: boundary at 0 ----
# Why: a $0 budget is allowed (a fully funded PhD costs nothing), but a negative one makes no sense.

def test_budget_zero_is_valid():
    assert is_valid(make_profile(annual_budget=0))


def test_budget_negative_is_invalid():
    assert "Budget cannot be negative." in validate_profile(make_profile(annual_budget=-1))


# ---- Equivalence classes for text/choice fields ----

@pytest.mark.parametrize("degree", ["BS", "MS", "PhD"])
def test_valid_degrees(degree):
    assert is_valid(make_profile(degree_sought=degree))


@pytest.mark.parametrize("degree", ["", "bs", "ms", "MBA"])
def test_invalid_degrees(degree):
    assert "Degree must be BS, MS or PhD." in validate_profile(make_profile(degree_sought=degree))


@pytest.mark.parametrize("field", ["", "   "])
def test_blank_field_is_invalid(field):
    assert "Field of study is required." in validate_profile(make_profile(field=field))


@pytest.mark.parametrize("state", ["", "XX", "mi", "Michigan"])
def test_invalid_home_state(state):
    errors = validate_profile(make_profile(home_state=state))
    assert "Home state must be a valid U.S. state code." in errors


def test_dc_is_a_valid_state():
    assert is_valid(make_profile(home_state="DC"))


def test_invalid_preferred_state_is_reported_by_name():
    errors = validate_profile(make_profile(preferred_states=("CA", "ZZ")))
    assert errors == ["Preferred state 'ZZ' is not a valid U.S. state code."]


@pytest.mark.parametrize("citizenship", ["", "Canadian", "us"])
def test_invalid_citizenship(citizenship):
    errors = validate_profile(make_profile(citizenship=citizenship))
    assert "Citizenship must be US, PR or International." in errors


# ---- Decision table: TOEFL requirement for international students ----
# citizenship      | toefl given | expected
# International    | no          | error
# International    | yes         | valid
# US / PR          | no          | valid

def test_international_without_toefl_is_invalid():
    errors = validate_profile(make_profile(citizenship="International", toefl=None))
    assert errors == ["TOEFL score is required for international students."]


def test_international_with_toefl_is_valid():
    assert is_valid(make_profile(citizenship="International", toefl=95))


@pytest.mark.parametrize("citizenship", ["US", "PR"])
def test_domestic_without_toefl_is_valid(citizenship):
    assert is_valid(make_profile(citizenship=citizenship, toefl=None))


# Why: the student should see every problem at once, not fix them one by one.
def test_all_errors_are_returned_together():
    profile = make_profile(degree_sought="MBA", gpa=5.0, annual_budget=-10)
    assert len(validate_profile(profile)) == 3


# ---- SAT and ACT (optional): boundary-value analysis ----

@pytest.mark.parametrize("sat", [400, 401, 1599, 1600, None])
def test_valid_sat_scores(sat):
    assert is_valid(make_profile(sat=sat))


@pytest.mark.parametrize("sat", [399, 1601, 0])
def test_invalid_sat_scores(sat):
    assert "SAT score must be between 400 and 1600." in validate_profile(make_profile(sat=sat))


@pytest.mark.parametrize("act", [1, 2, 35, 36, None])
def test_valid_act_scores(act):
    assert is_valid(make_profile(act=act))


@pytest.mark.parametrize("act", [0, 37])
def test_invalid_act_scores(act):
    assert "ACT score must be between 1 and 36." in validate_profile(make_profile(act=act))


# ---- Property-based: any profile inside every limit is valid ----
# Why: instead of picking values ourselves, Hypothesis builds many in-range profiles; none may be rejected.

from hypothesis import given, strategies as st
from gradmatch.validation import US_STATES


@given(gpa=st.floats(min_value=0.0, max_value=4.0, allow_nan=False),
       gre=st.one_of(st.none(), st.integers(260, 340)),
       toefl=st.one_of(st.none(), st.integers(0, 120)),
       sat=st.one_of(st.none(), st.integers(400, 1600)),
       act=st.one_of(st.none(), st.integers(1, 36)),
       budget=st.floats(min_value=0, max_value=500_000, allow_nan=False),
       state=st.sampled_from(US_STATES), degree=st.sampled_from(["BS", "MS", "PhD"]))
def test_every_profile_inside_the_limits_is_valid(gpa, gre, toefl, sat, act, budget, state, degree):
    profile = make_profile(gpa=gpa, gre=gre, toefl=toefl, sat=sat, act=act, annual_budget=budget,
                           home_state=state, degree_sought=degree)
    assert validate_profile(profile) == []
