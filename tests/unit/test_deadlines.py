"""Unit tests for deadlines.py.

Technique: boundary-value analysis on days_left. The status changes at
0 (closed/urgent), 14/15 (urgent/soon) and 30/31 (soon/later), so the
tests use -1, 0, 14, 15, 30 and 31 days. Leap-year tests check that
February 29 is counted as a real day.

`today` is a fixed date in every test, never date.today().
"""
# In plain words: these tests check the deadline labels (closed / urgent / soon / later) and the
# list of open deadlines. Every test uses the same fixed "today", so the results never change
# from one day to the next. That is only possible because the code takes `today` as an argument.

from datetime import date, timedelta

import pytest
from hypothesis import given, strategies as st

from conftest import make_program
from gradmatch.deadlines import (CLOSED, LATER, SOON, URGENT, deadline_of, deadline_status, glance_counts,
                                 upcoming)
from gradmatch.models import Scholarship

pytestmark = pytest.mark.unit

# A fixed day for every test; the deadlines are written as "N days from TODAY".
TODAY = date(2026, 10, 23)


def make_scholarship(scholarship_id, deadline) -> Scholarship:
    return Scholarship(
        scholarship_id=scholarship_id,
        name="Test Scholarship",
        type="scholarship",
        amount=1000.0,
        degree_levels=("MS",),
        fields=("Any",),
        min_gpa=0.0,
        citizenship=("Any",),
        states=("Any",),
        special=(),
        deadline=deadline,
        website="https://example.org/s",
    )


def in_days(days) -> date:
    return TODAY + timedelta(days=days)


# ---- Boundary-value analysis on days_left ----
# Why (boundary values): mistakes hide at the edges, so we test both sides of each cut-off: -1/0, 14/15 and 30/31 days.

@pytest.mark.parametrize("days_left, expected", [
    (-1, CLOSED),    # yesterday
    (0, URGENT),     # due today: still open
    (14, URGENT),    # last urgent day
    (15, SOON),      # first soon day
    (30, SOON),      # last soon day
    (31, LATER),     # first later day
])
def test_deadline_status_boundaries(days_left, expected):
    assert deadline_status(in_days(days_left), TODAY) == expected


def test_deadline_status_far_past_is_closed():
    assert deadline_status(in_days(-365), TODAY) == CLOSED


def test_deadline_status_far_future_is_later():
    assert deadline_status(in_days(365), TODAY) == LATER



# ---- The warning window (urgent_days) ----
# Why (boundary values): the window moves the urgent/soon cut-off, so each window is tested on
# both sides of its own cut-off, plus the fixed 30-day cut-off and the allowed range 0-90.

@pytest.mark.parametrize("urgent_days, days_left, expected", [
    (7, 7, URGENT), (7, 8, SOON),            # a shorter window
    (30, 30, URGENT), (30, 31, LATER),       # window of 30: no "soon" left
    (0, 0, URGENT), (0, 1, SOON),            # window of 0: only "due today" is urgent
    (90, 90, URGENT), (90, 91, LATER),       # the longest window
    (7, -1, CLOSED),
])
def test_deadline_status_with_a_warning_window(urgent_days, days_left, expected):
    assert deadline_status(in_days(days_left), TODAY, urgent_days=urgent_days) == expected


def test_deadline_status_default_window_is_14_days():
    assert [deadline_status(in_days(d), TODAY) for d in (14, 15)] == [URGENT, SOON]


@pytest.mark.parametrize("urgent_days", [-1, 91, 7.5, True, "14"])
def test_warning_window_outside_0_to_90_whole_days_is_refused(urgent_days):
    with pytest.raises(ValueError, match="urgent_days must be a whole number from 0 to 90"):
        deadline_status(TODAY, TODAY, urgent_days=urgent_days)
    with pytest.raises(ValueError, match="urgent_days must be a whole number from 0 to 90"):
        glance_counts([], TODAY, urgent_days=urgent_days)


# ---- glance_counts() ----
# Why (boundary values): one item at each of -1, 0, 7, 14, 15, 30, 90 and 91 days shows exactly
# which count each edge falls into.

def items_at(*days):
    return [make_program(program_id=f"P{d}", application_deadline=in_days(d)) for d in days]


@pytest.mark.parametrize("days_left, expected", [
    (-1, dict(within_window=0, within_90=0, later=0, passed=1)),
    (0, dict(within_window=1, within_90=1, later=0, passed=0)),
    (7, dict(within_window=1, within_90=1, later=0, passed=0)),
    (14, dict(within_window=1, within_90=1, later=0, passed=0)),
    (15, dict(within_window=0, within_90=1, later=0, passed=0)),
    (30, dict(within_window=0, within_90=1, later=0, passed=0)),
    (90, dict(within_window=0, within_90=1, later=0, passed=0)),
    (91, dict(within_window=0, within_90=0, later=1, passed=0)),
])
def test_glance_counts_boundaries_with_the_default_window(days_left, expected):
    assert glance_counts(items_at(days_left), TODAY) == expected


@pytest.mark.parametrize("urgent_days, within_window", [(0, 1), (7, 2), (14, 3), (30, 4), (90, 5)])
def test_glance_counts_window_moves_only_within_window(urgent_days, within_window):
    counts = glance_counts(items_at(-1, 0, 7, 14, 30, 90, 91), TODAY, urgent_days=urgent_days)

    assert counts == dict(within_window=within_window, within_90=5, later=1, passed=1)


def test_glance_counts_mixes_programs_and_scholarships_and_skips_unpublished():
    items = [make_program(application_deadline=None), make_scholarship("S", in_days(3)),
             make_program(application_deadline=in_days(40))]

    assert glance_counts(items, TODAY) == dict(within_window=1, within_90=2, later=0, passed=0)


def test_glance_counts_of_nothing_is_all_zero():
    assert glance_counts([], TODAY) == dict(within_window=0, within_90=0, later=0, passed=0)

# ---- Leap year ----
# Why: February 29 is a real day in 2028; counting it wrong would move a deadline from "soon" to "later".

def test_deadline_status_leap_day_deadline():
    # 2028 is a leap year, so 2028-02-29 is a real deadline date.
    assert deadline_status(date(2028, 2, 29), date(2028, 2, 15)) == URGENT  # 14 days


def test_deadline_status_counts_february_29():
    # Same calendar dates, one year apart. Feb 1 -> Mar 3 is 30 days in 2027
    # but 31 days in 2028 because of February 29, so the status changes.
    assert deadline_status(date(2027, 3, 3), date(2027, 2, 1)) == SOON
    assert deadline_status(date(2028, 3, 3), date(2028, 2, 1)) == LATER


# ---- upcoming() ----
# Why: the Deadlines tab must leave out closed items, keep "due today", and sort programs and scholarships together.

def test_upcoming_drops_closed_items():
    closed = make_program(program_id="CLOSED", application_deadline=in_days(-1))
    open_ = make_program(program_id="OPEN", application_deadline=in_days(5))

    result = upcoming([closed, open_], TODAY)

    assert [p.program_id for p in result] == ["OPEN"]


def test_upcoming_keeps_item_due_today():
    due_today = make_program(application_deadline=TODAY)

    assert upcoming([due_today], TODAY) == [due_today]


def test_upcoming_sorted_by_deadline_earliest_first():
    later = make_program(program_id="LATER", application_deadline=in_days(60))
    soon = make_program(program_id="SOON", application_deadline=in_days(20))
    urgent = make_program(program_id="URGENT", application_deadline=in_days(3))

    result = upcoming([later, soon, urgent], TODAY)

    assert [p.program_id for p in result] == ["URGENT", "SOON", "LATER"]


def test_upcoming_mixes_programs_and_scholarships():
    program = make_program(program_id="PROG", application_deadline=in_days(10))
    scholarship = make_scholarship("SCH", in_days(2))
    closed_scholarship = make_scholarship("OLD", in_days(-3))

    result = upcoming([program, closed_scholarship, scholarship], TODAY)

    assert result == [scholarship, program]


def test_upcoming_empty_list():
    assert upcoming([], TODAY) == []


def test_upcoming_all_closed_gives_empty_list():
    items = [make_program(application_deadline=in_days(-1)), make_scholarship("OLD", in_days(-30))]

    assert upcoming(items, TODAY) == []


# ---- Deadlines that are not published (None) ----
# Why: imported programs often have no deadline. They must be left out, not crash the sort.

def test_deadline_of_unpublished_program_deadline_is_none():
    assert deadline_of(make_program(application_deadline=None)) is None


def test_upcoming_leaves_out_programs_without_a_deadline():
    unknown = make_program(program_id="UNKNOWN", application_deadline=None)
    known = make_program(program_id="KNOWN", application_deadline=in_days(5))
    scholarship = make_scholarship("SCH", in_days(1))

    result = upcoming([unknown, known, scholarship], TODAY)

    assert result == [scholarship, known]


def test_upcoming_only_unpublished_deadlines_gives_empty_list():
    items = [make_program(program_id=f"P{i}", application_deadline=None) for i in range(3)]

    assert upcoming(items, TODAY) == []


# ---- Property-based test (Hypothesis) ----
# Why (property-based): instead of a few chosen days, Hypothesis tries hundreds of random pairs of
# days and checks a rule that must ALWAYS hold: as the days left shrink, the label never becomes
# LESS urgent. later -> soon -> urgent -> closed, never backwards. A wrong cut-off (like a typo
# that makes day 20 "later") would break this for some pair of days.

URGENCY = {LATER: 0, SOON: 1, URGENT: 2, CLOSED: 3}


# Days from -60 to 60: around the cut-offs (0, 14, 30), where a mistake would show.
@given(more_days=st.integers(-60, 60), fewer_days=st.integers(-60, 60))
def test_status_never_gets_less_urgent_as_the_deadline_gets_closer(more_days, fewer_days):
    more_days, fewer_days = max(more_days, fewer_days), min(more_days, fewer_days)

    earlier_label = deadline_status(in_days(more_days), TODAY)
    later_label = deadline_status(in_days(fewer_days), TODAY)

    assert URGENCY[later_label] >= URGENCY[earlier_label]


@given(deadline=st.dates(), today=st.dates())
def test_status_depends_only_on_the_days_between(deadline, today):
    # Moving both dates by the same amount never changes the label (no hidden "today").
    shift = timedelta(days=100)
    if date.min + shift <= today and date.min + shift <= deadline:
        assert deadline_status(deadline, today) == deadline_status(deadline - shift, today - shift)
