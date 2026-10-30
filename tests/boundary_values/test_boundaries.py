from datetime import date

import pytest

from gradmatch.deadlines import upcoming
from gradmatch.fit import MATCH, REACH, SAFETY, chance, check_gpa
from gradmatch.scholarships import find_scholarships, qualifies
from gradmatch.search import find_programs
from helpers import make_program, make_scholarship, make_student


def test_gpa_must_be_0_to_4():
    check_gpa(0.0)
    check_gpa(4.0)
    for bad in [-0.01, 4.01]:
        with pytest.raises(ValueError):
            check_gpa(bad)


def test_chance_gpa_edges():
    assert [chance(gpa, 0.40) for gpa in [2.99, 3.0, 3.69, 3.7]] == [REACH, MATCH, MATCH, SAFETY]


def test_chance_acceptance_rate_edges():
    rates = [0.09, 0.10, 0.24, 0.25, 0.59, 0.60]
    assert [chance(3.5, rate) for rate in rates] == [REACH, REACH, REACH, MATCH, MATCH, SAFETY]


def test_budget_edges():
    # the program costs $25,000 a year
    for budget, found in [(25001, 1), (25000, 1), (24999, 0)]:
        assert len(find_programs([make_program()], make_student(budget=budget))) == found
    with pytest.raises(ValueError):
        find_programs([make_program()], make_student(budget=-1))


def test_scholarship_min_gpa_edge():
    scholarship = make_scholarship(min_gpa=3.0)
    assert [qualifies(scholarship, make_student(gpa=gpa)) for gpa in [2.99, 3.0]] == [False, True]


def test_deadline_day_edges():
    today = date(2026, 11, 1)
    found = upcoming([("0", date(2026, 11, 1)), ("14", date(2026, 11, 15)),
                      ("15", date(2026, 11, 16)), ("passed", date(2026, 10, 31))], today)
    assert [(d.days_left, d.soon) for d in found] == [(0, True), (14, True), (15, False)]


def test_empty_lists():
    assert find_programs([], make_student()) == []
    assert find_scholarships([], make_student()) == []
    assert upcoming([], date(2026, 11, 1)) == []
