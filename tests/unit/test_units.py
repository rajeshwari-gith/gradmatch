from datetime import date

from gradmatch.cost import tuition_for, yearly_cost
from gradmatch.deadlines import today, upcoming
from gradmatch.fit import MATCH
from gradmatch.scholarships import find_scholarships
from gradmatch.search import find_programs
from helpers import make_program, make_scholarship, make_student


def test_tuition():
    assert tuition_for(make_program(state="MI"), "MI") == 10000
    assert tuition_for(make_program(state="MI"), "OH") == 20000


def test_yearly_cost():
    assert yearly_cost(make_program(), "MI") == 10000 + 15000


def test_find_programs():
    result = find_programs([make_program()], make_student())[0]
    assert (result.program.university, result.cost, result.chance) == ("Test University", 25000, MATCH)


def test_find_scholarships():
    found = find_scholarships([make_scholarship(name="Small", amount=1000),
                               make_scholarship(name="Big", amount=9000)], make_student())
    assert [s.name for s in found] == ["Big", "Small"]


def test_upcoming():
    found = upcoming([("B", date(2027, 1, 5)), ("A", date(2026, 11, 20))], date(2026, 11, 1))
    assert [d.name for d in found] == ["A", "B"]
    assert today() == date.today()
