import pytest
from hypothesis import given
from hypothesis import strategies as st

from gradmatch.fit import MATCH, REACH, SAFETY, chance, check_gpa, check_gre


# decision table: acceptance rate (rows) x GPA (columns)
@pytest.mark.parametrize("rate, gpa, expected", [
    (0.05, 4.0, REACH), (0.05, 3.5, REACH), (0.05, 2.5, REACH),
    (0.15, 4.0, MATCH), (0.15, 3.5, REACH), (0.15, 2.5, REACH),
    (0.40, 4.0, SAFETY), (0.40, 3.5, MATCH), (0.40, 2.5, REACH),
    (0.80, 4.0, SAFETY), (0.80, 3.5, SAFETY), (0.80, 2.5, MATCH),
])
def test_decision_table(rate, gpa, expected):
    assert chance(gpa, rate) == expected


@pytest.mark.parametrize("rate, expected", [
    (0.09, REACH), (0.10, REACH),
    (0.24, REACH), (0.25, MATCH),
    (0.59, MATCH), (0.60, SAFETY),
])
def test_rate_edges(rate, expected):
    assert chance(3.5, rate) == expected


@pytest.mark.parametrize("gpa, expected", [
    (2.99, REACH), (3.0, MATCH),
    (3.69, MATCH), (3.7, SAFETY),
])
def test_gpa_edges(gpa, expected):
    assert chance(gpa, 0.40) == expected


@pytest.mark.parametrize("gpa", [0.0, 2.0, 4.0])
def test_valid_gpa(gpa):
    check_gpa(gpa)


@pytest.mark.parametrize("gpa", [-0.01, 4.01, -3.0, 9.0])
def test_invalid_gpa(gpa):
    with pytest.raises(ValueError):
        check_gpa(gpa)


def test_chance_rejects_invalid_gpa():
    with pytest.raises(ValueError):
        chance(5.0, 0.5)


@given(st.floats(0, 4), st.floats(0, 1))
def test_chance_is_always_one_of_three(gpa, rate):
    assert chance(gpa, rate) in {SAFETY, MATCH, REACH}


# GRE moves the chance one step when the program's average GRE is known
@pytest.mark.parametrize("gre, expected", [
    (None, MATCH), (325, SAFETY), (324, MATCH), (315, MATCH), (314, REACH),
])
def test_gre_edges(gre, expected):
    assert chance(3.5, 0.40, gre, 320) == expected


def test_gre_ignored_when_program_average_unknown():
    assert chance(3.5, 0.40, 340, None) == MATCH


@pytest.mark.parametrize("gre", [260, 300, 340])
def test_valid_gre(gre):
    check_gre(gre)


@pytest.mark.parametrize("gre", [259, 341])
def test_invalid_gre(gre):
    with pytest.raises(ValueError):
        check_gre(gre)
