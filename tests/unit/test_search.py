from helpers import make_program, make_student
from programs import MATCH, find_programs


def test_find_programs():
    result = find_programs([make_program()], make_student())[0]
    assert (result.program.university, result.cost, result.chance) == ("Test University", 25000, MATCH)
