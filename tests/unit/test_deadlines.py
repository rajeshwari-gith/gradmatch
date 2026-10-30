from datetime import date

from scholarships import today, upcoming


def test_upcoming():
    found = upcoming([("B", "2027-01-05"), ("A", "2026-11-20")], date(2026, 11, 1))
    assert [d["name"] for d in found] == ["A", "B"]
    assert today() == date.today()
