"""Unit tests for fit.py.

Techniques: boundary-value analysis on the GPA difference (around +0.20
and -0.15) and on the acceptance rate (around 0.10), plus a decision
table showing the acceptance-rate rule overrides the GPA rule.
"""
import pytest

from conftest import make_program
from gradmatch.fit import MATCH, REACH, SAFETY, classify_fit

pytestmark = pytest.mark.unit

# make_program(): avg_gpa = 3.40, acceptance_rate = 0.40


# ---- Boundary-value analysis on gpa - avg_gpa ----

@pytest.mark.parametrize("gpa, expected", [
    (3.61, SAFETY),   # diff +0.21
    (3.60, SAFETY),   # diff +0.20  (boundary)
    (3.59, MATCH),    # diff +0.19
    (3.40, MATCH),    # diff  0.00
    (3.26, MATCH),    # diff -0.14
    (3.25, MATCH),    # diff -0.15  (boundary)
    (3.24, REACH),    # diff -0.16
])
def test_gpa_difference_boundaries(gpa, expected):
    assert classify_fit(gpa, make_program()) == expected


def test_extreme_gpas():
    assert classify_fit(4.0, make_program()) == SAFETY
    assert classify_fit(0.0, make_program()) == REACH


# ---- Boundary-value analysis on acceptance rate ----

@pytest.mark.parametrize("rate, expected", [
    (0.09, REACH),    # below 10%: always Reach
    (0.10, SAFETY),   # exactly 10%: GPA rule applies
    (0.11, SAFETY),
])
def test_acceptance_rate_boundary(rate, expected):
    program = make_program(acceptance_rate=rate)
    assert classify_fit(4.0, program) == expected


# ---- Decision table ----
# acceptance < 10% | GPA rule says | result
# yes              | Safety        | Reach
# yes              | Reach         | Reach
# no               | Safety        | Safety
# no               | Match         | Match
# no               | Reach         | Reach

@pytest.mark.parametrize("rate, gpa, expected", [
    (0.05, 4.00, REACH),
    (0.05, 2.50, REACH),
    (0.40, 4.00, SAFETY),
    (0.40, 3.40, MATCH),
    (0.40, 2.50, REACH),
])
def test_fit_decision_table(rate, gpa, expected):
    assert classify_fit(gpa, make_program(acceptance_rate=rate)) == expected
