from datetime import date

import pytest

from gradmatch.deadlines import today, upcoming

TODAY = date(2026, 11, 1)


def due(day):
    return (f"Due {day}", day)


@pytest.mark.parametrize("deadline, days_left, soon", [
    (date(2026, 11, 1), 0, True),
    (date(2026, 11, 15), 14, True),
    (date(2026, 11, 16), 15, False),
])
def test_days_left_and_soon(deadline, days_left, soon):
    d = upcoming([due(deadline)], TODAY)[0]
    assert (d.days_left, d.soon) == (days_left, soon)


def test_passed_deadline_is_left_out():
    assert upcoming([due(date(2026, 10, 31))], TODAY) == []


def test_sorted_by_date():
    found = upcoming([due(date(2027, 1, 5)), due(date(2026, 11, 20))], TODAY)
    assert [d.date for d in found] == [date(2026, 11, 20), date(2027, 1, 5)]


def test_no_scholarships():
    assert upcoming([], TODAY) == []


def test_today_is_the_real_date():
    assert today() == date.today()
