from datetime import date

from gradmatch.deadlines import today, upcoming


def test_upcoming():
    found = upcoming([("B", date(2027, 1, 5)), ("A", date(2026, 11, 20))], date(2026, 11, 1))
    assert [d.name for d in found] == ["A", "B"]
    assert today() == date.today()
