import pytest
from hypothesis import given
from hypothesis import strategies as st

from gradmatch.fit import MATCH, REACH, SAFETY, chance, check_gpa


@pytest.mark.parametrize("gpa, expected", [(3.9, SAFETY), (3.5, MATCH), (3.0, REACH)])
def test_chance(gpa, expected):
    assert chance(gpa, 3.5) == expected


# on and next to the +0.20 and -0.15 edges
@pytest.mark.parametrize("gpa, expected", [
    (3.70, SAFETY),
    (3.69, MATCH),
    (3.35, MATCH),
    (3.34, REACH),
])
def test_chance_at_the_edges(gpa, expected):
    assert chance(gpa, 3.5) == expected


@pytest.mark.parametrize("gpa", [0.0, 2.0, 4.0])
def test_valid_gpa(gpa):
    check_gpa(gpa)


@pytest.mark.parametrize("gpa", [-0.01, 4.01, -3.0, 9.0])
def test_invalid_gpa(gpa):
    with pytest.raises(ValueError):
        check_gpa(gpa)


def test_chance_rejects_invalid_gpa():
    with pytest.raises(ValueError):
        chance(5.0, 3.5)


@given(st.floats(0, 4), st.floats(0, 4))
def test_chance_is_always_one_of_three(gpa, avg_gpa):
    assert chance(gpa, avg_gpa) in {SAFETY, MATCH, REACH}
