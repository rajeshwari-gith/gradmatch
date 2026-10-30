import pytest

from helpers import make_program, make_student
from programs import find_programs

# covers every branch of find_programs() in search.py


def test_req7_bad_input_stops_the_search():
    for student in [make_student(gpa=4.2), make_student(budget=-1)]:
        with pytest.raises(ValueError):
            find_programs([make_program()], student)


def test_req1_req2_each_skip_branch_and_the_kept_branch():
    programs = [make_program(degree="PhD"), make_program(field="Statistics"),
                make_program(state="WI"), make_program(living_cost=90000),
                make_program(university="Kept")]
    found = find_programs(programs, make_student(states=("MI",)))
    assert [r.program.university for r in found] == ["Kept"]
