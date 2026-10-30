"""Property-based tests (Hypothesis) for the fit rule in fit.py.

Instead of a few chosen examples, Hypothesis tries hundreds of GPAs and
acceptance rates and checks rules that must ALWAYS hold:
- with the rate fixed, a higher GPA never gives a worse chance;
- with the GPA fixed, a higher acceptance rate never gives a worse chance;
- an acceptance rate under 10% is always Reach.
"""
# In plain words: the fit rule has several steps (the 10% rule, test scores, the average GPA,
# and the estimate from the acceptance rate). A wrong cut-off in any step could make a better
# student look worse off, or an easier school look harder. These tests let Hypothesis hunt for
# such a case. The rate is sometimes the program's own and sometimes its university's rate
# (school_rate), because the rule uses both.

import pytest
from hypothesis import given, strategies as st

from conftest import make_program
from gradmatch.fit import MATCH, REACH, SAFETY, classify_fit

pytestmark = pytest.mark.unit

# Easier chances get a higher number, so "never worse" means "the number never goes down".
EASE = {REACH: 0, MATCH: 1, SAFETY: 2}

# GPAs and averages with two decimals (like real ones), rates with three.
gpas = st.integers(0, 400).map(lambda n: n / 100)
rates = st.integers(0, 1000).map(lambda n: n / 1000)
low_rates = st.integers(0, 99).map(lambda n: n / 1000)           # 0% to 9.9%
average_gpas = st.none() | gpas                                   # None = not published


def fit(gpa, rate, avg_gpa=None, own_rate=True):
    """The fit for a program with this average GPA and rate, given as its own or its university's."""
    program = make_program(avg_gpa=avg_gpa, acceptance_rate=rate if own_rate else None,
                           sat_25=None, sat_75=None, act_25=None, act_75=None)
    return classify_fit(gpa, program, school_rate=None if own_rate else rate)


@given(rate=rates, avg_gpa=average_gpas, own_rate=st.booleans(), gpa_a=gpas, gpa_b=gpas)
def test_a_higher_gpa_never_gives_a_worse_chance(rate, avg_gpa, own_rate, gpa_a, gpa_b):
    lower, higher = sorted((gpa_a, gpa_b))

    assert EASE[fit(higher, rate, avg_gpa, own_rate)] >= EASE[fit(lower, rate, avg_gpa, own_rate)]


@given(gpa=gpas, avg_gpa=average_gpas, own_rate=st.booleans(), rate_a=rates, rate_b=rates)
def test_a_higher_acceptance_rate_never_gives_a_worse_chance(gpa, avg_gpa, own_rate, rate_a, rate_b):
    lower, higher = sorted((rate_a, rate_b))

    assert EASE[fit(gpa, higher, avg_gpa, own_rate)] >= EASE[fit(gpa, lower, avg_gpa, own_rate)]


# Any GPA, any average, and even a test score at the top of the range: under 10% is Reach.
@given(rate=low_rates, gpa=gpas, avg_gpa=average_gpas, own_rate=st.booleans(),
       sat=st.none() | st.integers(400, 1600))
def test_a_rate_under_10_percent_is_always_reach(rate, gpa, avg_gpa, own_rate, sat):
    program = make_program(avg_gpa=avg_gpa, acceptance_rate=rate if own_rate else None,
                           sat_25=400, sat_75=400)        # any SAT would be Safety without the rule

    assert classify_fit(gpa, program, sat=sat, school_rate=None if own_rate else rate) == REACH
