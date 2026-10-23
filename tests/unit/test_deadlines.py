"""Unit tests for deadlines.py.

Technique: boundary-value analysis on days_left. The status changes at
0 (closed/urgent), 14/15 (urgent/soon) and 30/31 (soon/later), so the
tests use -1, 0, 14, 15, 30 and 31 days. Leap-year tests check that
February 29 is counted as a real day.

`today` is a fixed date in every test, never date.today().
"""
from datetime import date, timedelta

import pytest

from conftest import make_program
from gradmatch.deadlines import CLOSED, LATER, SOON, URGENT, deadline_status, upcoming
from gradmatch.models import Scholarship

pytestmark = pytest.mark.unit

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

def test_deadline_status_leap_day_deadline():
    # 2028 is a leap year, so 2028-02-29 is a real deadline date.
    assert deadline_status(date(2028, 2, 29), date(2028, 2, 15)) == URGENT  # 14 days


def test_deadline_status_counts_february_29():
    # Same calendar dates, one year apart. Feb 1 -> Mar 3 is 30 days in 2027
    # but 31 days in 2028 because of February 29, so the status changes.
    assert deadline_status(date(2027, 3, 3), date(2027, 2, 1)) == SOON
    assert deadline_status(date(2028, 3, 3), date(2028, 2, 1)) == LATER


# ---- upcoming() ----

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
