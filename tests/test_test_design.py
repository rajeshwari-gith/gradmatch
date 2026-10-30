"""Week 3 - Test case design: equivalence partitioning and boundary values.

We split each input into groups (partitions) that should behave the same, test one value
from each group, and then test the values right on and next to each edge (boundaries).
"""
import pytest

from gradmatch.fit import MATCH, REACH, SAFETY, chance, check_gpa
from gradmatch.search import find_programs
from helpers import make_program, make_student

# GPA difference (student GPA - average GPA) has three partitions:
#   diff >= 0.20          -> Safety
#   -0.15 <= diff < 0.20  -> Match
#   diff < -0.15          -> Reach


@pytest.mark.parametrize("gpa, expected", [
    (3.9, SAFETY),   # diff +0.40, inside the Safety partition
    (3.5, MATCH),    # diff  0.00, inside the Match partition
    (3.0, REACH),    # diff -0.50, inside the Reach partition
], ids=["safety", "match", "reach"])
def test_one_value_from_each_chance_partition(gpa, expected):
    assert chance(gpa, 3.5) == expected


@pytest.mark.parametrize("gpa, expected", [
    (3.70, SAFETY),  # diff +0.20, on the Safety edge
    (3.69, MATCH),   # diff +0.19, just under it
    (3.35, MATCH),   # diff -0.15, on the Reach edge (still Match)
    (3.34, REACH),   # diff -0.16, just past it
], ids=["+0.20", "+0.19", "-0.15", "-0.16"])
def test_chance_boundaries(gpa, expected):
    assert chance(gpa, 3.5) == expected


# GPA input has three partitions: below 0 (invalid), 0 to 4 (valid), above 4 (invalid).

@pytest.mark.parametrize("gpa", [0.0, 4.0, 2.0], ids=["lowest", "highest", "middle"])
def test_valid_gpas_are_accepted(gpa):
    check_gpa(gpa)


@pytest.mark.parametrize("gpa", [-0.01, 4.01, -3.0, 9.0], ids=["just-below-0", "just-above-4", "far-below", "far-above"])
def test_invalid_gpas_are_rejected(gpa):
    with pytest.raises(ValueError):
        check_gpa(gpa)


# Budget compared to the yearly cost ($25,000 here) has two partitions:
# budget >= cost (shown) and budget < cost (hidden). Negative budgets are invalid.

@pytest.mark.parametrize("budget, shown", [
    (25000, True),   # exactly the cost
    (25001, True),   # one dollar more
    (24999, False),  # one dollar less
    (0, False),      # smallest valid budget
], ids=["equal", "one-more", "one-less", "zero"])
def test_budget_boundaries(budget, shown):
    results = find_programs([make_program()], make_student(budget=budget))
    assert (len(results) == 1) == shown


@pytest.mark.parametrize("budget", [-1, -50000])
def test_negative_budget_is_rejected(budget):
    with pytest.raises(ValueError):
        find_programs([make_program()], make_student(budget=budget))
