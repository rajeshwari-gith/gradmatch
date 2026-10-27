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

from conftest import make_program
from gradmatch.deadlines import CLOSED, LATER, SOON, URGENT, deadline_of, deadline_status, upcoming
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
