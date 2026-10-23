"""Unit tests for validation.py.

Techniques: equivalence partitioning (valid / invalid classes) and
boundary-value analysis (values just below, on, and just above each limit).
"""
import pytest

from conftest import make_profile
from gradmatch.validation import is_valid, validate_profile

pytestmark = pytest.mark.unit


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

def test_budget_zero_is_valid():
    assert is_valid(make_profile(annual_budget=0))


def test_budget_negative_is_invalid():
    assert "Budget cannot be negative." in validate_profile(make_profile(annual_budget=-1))


# ---- Equivalence classes for text/choice fields ----

@pytest.mark.parametrize("degree", ["MS", "PhD"])
def test_valid_degrees(degree):
    assert is_valid(make_profile(degree_sought=degree))


@pytest.mark.parametrize("degree", ["", "BS", "ms", "MBA"])
def test_invalid_degrees(degree):
    assert "Degree must be MS or PhD." in validate_profile(make_profile(degree_sought=degree))


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


def test_all_errors_are_returned_together():
    profile = make_profile(degree_sought="BS", gpa=5.0, annual_budget=-10)
    assert len(validate_profile(profile)) == 3
