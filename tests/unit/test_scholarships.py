"""Unit tests for scholarships.py.

Technique: decision table. The eligibility rule has six conditions
(C1-C6). Rule R1 makes every condition true; each of R2-R7 makes exactly
one condition false, so each condition is shown to matter on its own.

    Condition                      R1  R2  R3  R4  R5  R6  R7
    C1 degree in degree_levels     T   F   T   T   T   T   T
    C2 field allowed               T   T   F   T   T   T   T
    C3 gpa >= min_gpa              T   T   T   F   T   T   T
    C4 citizenship allowed         T   T   T   T   F   T   T
    C5 home_state allowed          T   T   T   T   T   F   T
    C6 all special items held      T   T   T   T   T   T   F
    Eligible?                      Y   N   N   N   N   N   N

Extra tests cover the different ways a condition can be true ("Any",
GPA exactly equal, no special requirement) and the sort order.
"""
# In plain words: these tests prove a student sees exactly the scholarships they qualify for,
# in the right order. The main technique is a decision table: one row where every rule is met,
# then one row per rule where only that rule fails. If any rule were forgotten in the code,
# its row would wrongly say "eligible" and the test would fail.

from datetime import date

import pytest

from conftest import make_profile
from gradmatch.models import Scholarship
from gradmatch.scholarships import eligible_scholarships, is_eligible

pytestmark = pytest.mark.unit

# make_profile(): MS, gpa 3.50, Computer Science, home_state MI, citizenship US, special ()


# A scholarship the default student qualifies for. Tests change one field to break one rule.
def make_scholarship(**changes) -> Scholarship:
    """A scholarship that make_profile() is eligible for, with no "Any" values.

    It lists exact values so that each decision-table condition can be made
    false by changing one field.
    """
    values = dict(
        scholarship_id="S1",
        name="Test Scholarship",
        type="scholarship",
        amount=5000.0,
        degree_levels=("MS",),
        fields=("Computer Science",),
        min_gpa=3.0,
        citizenship=("US",),
        states=("MI",),
        special=(),
        deadline=date(2026, 12, 1),
        website="https://example.org/s1",
    )
    values.update(changes)
    return Scholarship(**values)


# ---- Decision table R1-R7 ----
# Why (decision table): R1 has every rule true; R2-R7 each make exactly one rule false.

@pytest.mark.parametrize("rule, profile_changes, scholarship_changes, expected", [
    ("R1 all true",         {},                               {},                              True),
    ("R2 C1 degree false",  {"degree_sought": "PhD"},         {},                              False),
    ("R3 C2 field false",   {"field": "Data Science"},        {},                              False),
    ("R4 C3 gpa false",     {"gpa": 2.99},                    {},                              False),
    ("R5 C4 citizen false", {"citizenship": "International"}, {},                              False),
    ("R6 C5 state false",   {"home_state": "OH"},             {},                              False),
    ("R7 C6 special false", {},                               {"special": ("first_gen",)},     False),
])
def test_decision_table(rule, profile_changes, scholarship_changes, expected):
    profile = make_profile(**profile_changes)
    scholarship = make_scholarship(**scholarship_changes)

    assert is_eligible(profile, scholarship) is expected, rule


# ---- Other ways each condition can be true ----
# Why: "Any", a GPA exactly at the minimum (boundary value) and extra special groups must all still pass.

def test_c1_degree_in_a_list_of_two_levels():
    assert is_eligible(make_profile(degree_sought="PhD"),
                       make_scholarship(degree_levels=("MS", "PhD")))


def test_c2_any_field_accepts_every_field():
    assert is_eligible(make_profile(field="Data Science"), make_scholarship(fields=("Any",)))


def test_c3_gpa_exactly_equal_to_minimum_is_eligible():
    # Boundary value: the rule is gpa >= min_gpa, so equal passes.
    assert is_eligible(make_profile(gpa=3.0), make_scholarship(min_gpa=3.0))


def test_c4_any_citizenship_accepts_international():
    assert is_eligible(make_profile(citizenship="International"),
                       make_scholarship(citizenship=("Any",)))


def test_c4_permanent_resident_in_list():
    assert is_eligible(make_profile(citizenship="PR"), make_scholarship(citizenship=("US", "PR")))


def test_c5_any_state_accepts_every_state():
    assert is_eligible(make_profile(home_state="OH"), make_scholarship(states=("Any",)))


def test_c6_profile_holding_the_special_item_is_eligible():
    assert is_eligible(make_profile(special=("first_gen",)),
                       make_scholarship(special=("first_gen",)))


def test_c6_extra_special_items_on_the_profile_do_not_matter():
    assert is_eligible(make_profile(special=("first_gen", "women_stem")), make_scholarship())


def test_c6_every_listed_special_item_is_required():
    # The scholarship needs two items; the student has only one.
    scholarship = make_scholarship(special=("first_gen", "mcnair_scholar"))

    assert not is_eligible(make_profile(special=("first_gen",)), scholarship)


# ---- eligible_scholarships(): filtering and sort order ----
# Why: students act on the soonest deadline first, and on the bigger award when two close the same day.

def test_only_eligible_scholarships_are_returned():
    good = make_scholarship(scholarship_id="GOOD")
    bad = make_scholarship(scholarship_id="BAD", min_gpa=3.9)

    result = eligible_scholarships(make_profile(), [bad, good])

    assert [s.scholarship_id for s in result] == ["GOOD"]


def test_sorted_by_deadline_earliest_first():
    late = make_scholarship(scholarship_id="LATE", deadline=date(2027, 3, 1))
    early = make_scholarship(scholarship_id="EARLY", deadline=date(2026, 11, 1))
    middle = make_scholarship(scholarship_id="MIDDLE", deadline=date(2027, 1, 15))

    result = eligible_scholarships(make_profile(), [late, early, middle])

    assert [s.scholarship_id for s in result] == ["EARLY", "MIDDLE", "LATE"]


def test_same_deadline_sorted_by_amount_highest_first():
    small = make_scholarship(scholarship_id="SMALL", amount=1000.0)
    big = make_scholarship(scholarship_id="BIG", amount=20000.0)
    zero = make_scholarship(scholarship_id="ZERO", amount=0.0)

    result = eligible_scholarships(make_profile(), [small, zero, big])

    assert [s.scholarship_id for s in result] == ["BIG", "SMALL", "ZERO"]


def test_deadline_is_compared_before_amount():
    # A bigger amount does not move a later deadline ahead.
    early_small = make_scholarship(scholarship_id="EARLY", amount=500.0,
                                   deadline=date(2026, 11, 1))
    late_big = make_scholarship(scholarship_id="LATE", amount=50000.0,
                                deadline=date(2026, 12, 1))

    result = eligible_scholarships(make_profile(), [late_big, early_small])

    assert [s.scholarship_id for s in result] == ["EARLY", "LATE"]


def test_no_scholarships_gives_empty_list():
    assert eligible_scholarships(make_profile(), []) == []


def test_none_eligible_gives_empty_list():
    assert eligible_scholarships(make_profile(gpa=1.0), [make_scholarship()]) == []
