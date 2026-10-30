from datetime import date

import pytest

from gradmatch.deadlines import upcoming
from gradmatch.fit import MATCH, REACH, SAFETY, chance, check_gpa
from gradmatch.scholarships import find_scholarships, qualifies
from gradmatch.search import find_programs
from helpers import make_program, make_scholarship, make_student

# Equivalence partitions and the values on and next to each edge


@pytest.mark.parametrize("gpa", [0.0, 2.0, 4.0])
def test_valid_gpa(gpa):
    check_gpa(gpa)


@pytest.mark.parametrize("gpa", [-0.01, 4.01, -3.0, 9.0])
def test_invalid_gpa(gpa):
    with pytest.raises(ValueError):
        check_gpa(gpa)


@pytest.mark.parametrize("gpa, expected", [(2.99, REACH), (3.0, MATCH), (3.69, MATCH), (3.7, SAFETY)])
def test_gpa_edges_for_chance(gpa, expected):
    assert chance(gpa, 0.40) == expected


@pytest.mark.parametrize("rate, expected", [
    (0.09, REACH), (0.10, REACH), (0.24, REACH), (0.25, MATCH), (0.59, MATCH), (0.60, SAFETY),
])
def test_acceptance_rate_edges(rate, expected):
    assert chance(3.5, rate) == expected


# the program costs $25,000 a year
@pytest.mark.parametrize("budget, found", [(25001, 1), (25000, 1), (24999, 0), (0, 0)])
def test_budget_edges(budget, found):
    assert len(find_programs([make_program()], make_student(budget=budget))) == found


@pytest.mark.parametrize("budget", [-1, -50000])
def test_negative_budget(budget):
    with pytest.raises(ValueError):
        find_programs([make_program()], make_student(budget=budget))


@pytest.mark.parametrize("gpa, expected", [(2.99, False), (3.0, True), (3.01, True)])
def test_scholarship_min_gpa_edge(gpa, expected):
    assert qualifies(make_scholarship(min_gpa=3.0), make_student(gpa=gpa)) == expected


@pytest.mark.parametrize("deadline, days_left, soon", [
    (date(2026, 11, 1), 0, True),
    (date(2026, 11, 15), 14, True),
    (date(2026, 11, 16), 15, False),
])
def test_days_left_edges(deadline, days_left, soon):
    d = upcoming([("Award", deadline)], date(2026, 11, 1))[0]
    assert (d.days_left, d.soon) == (days_left, soon)


def test_deadline_one_day_ago_is_hidden():
    assert upcoming([("Award", date(2026, 10, 31))], date(2026, 11, 1)) == []


def test_no_scholarships_gives_empty_list():
    assert find_scholarships([], make_student()) == []


def test_no_deadlines_gives_empty_list():
    assert upcoming([], date(2026, 11, 1)) == []
