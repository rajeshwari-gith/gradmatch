import pytest

from tests.helpers import make_program, make_student
from programs import find_programs


def test_every_branch_of_find_programs():
    # REQ-7: bad GPA and negative budget stop the search
    for student in [make_student(gpa=4.2), make_student(budget=-1)]:
        with pytest.raises(ValueError):
            find_programs([make_program()], student)

    # REQ-1, REQ-2: wrong degree, wrong field, state not chosen and too expensive are skipped
    programs = [make_program(degree="PhD"), make_program(field="Statistics"),
                make_program(state="WI"), make_program(living_cost=90000),
                make_program(university="Kept")]
    found = find_programs(programs, make_student(states=["MI"]))
    assert [r["program"]["university"] for r in found] == ["Kept"]
