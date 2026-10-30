from fit import MATCH
from search import find_programs
from helpers import make_program, make_student


def test_find_programs():
    result = find_programs([make_program()], make_student())[0]
    assert (result.program.university, result.cost, result.chance) == ("Test University", 25000, MATCH)
