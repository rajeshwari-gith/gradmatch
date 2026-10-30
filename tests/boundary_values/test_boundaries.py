from datetime import date

import pytest

from programs import chance, check_gpa, find_programs
from scholarships import qualifies, upcoming
from tests.helpers import make_program, make_scholarship, make_student


def test_boundary_values():
    # REQ-7: GPA must be 0 to 4
    check_gpa(0.0)
    check_gpa(4.0)
    for bad in [-0.01, 4.01]:
        with pytest.raises(ValueError):
            check_gpa(bad)

    # REQ-4: chance changes at GPA 3.0 / 3.7 and acceptance rate 10% / 25% / 60%
    assert [chance(gpa, 0.40) for gpa in [2.99, 3.0, 3.69, 3.7]] == ["Reach", "Match", "Match", "Safety"]
    assert [chance(3.5, rate) for rate in [0.09, 0.10, 0.25, 0.60]] == ["Reach", "Reach", "Match", "Safety"]

    # REQ-2: the program costs $25,000, so a budget of $24,999 is too small
    assert [len(find_programs([make_program()], make_student(budget=b))) for b in [24999, 25000]] == [0, 1]

    # REQ-5: scholarship minimum GPA of 3.0
    assert [qualifies(make_scholarship(min_gpa=3.0), make_student(gpa=g)) for g in [2.99, 3.0]] == [False, True]

    # REQ-6: warning at 14 days, not at 15; a passed deadline is hidden
    found = upcoming([("14", "2026-11-15"), ("15", "2026-11-16"),
                      ("passed", "2026-10-31")], date(2026, 11, 1))
    assert [(d["days_left"], d["soon"]) for d in found] == [(14, True), (15, False)]
