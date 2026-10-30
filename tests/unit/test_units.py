from datetime import date

import pytest

from gradmatch.cost import tuition_for, yearly_cost
from gradmatch.deadlines import today, upcoming
from gradmatch.fit import MATCH, chance, check_gpa
from gradmatch.scholarships import find_scholarships, qualifies
from gradmatch.search import find_programs
from helpers import make_program, make_scholarship, make_student


def test_in_state_tuition():
    assert tuition_for(make_program(state="MI"), "MI") == 10000


def test_out_of_state_tuition():
    assert tuition_for(make_program(state="MI"), "OH") == 20000


def test_yearly_cost_is_tuition_plus_living_cost():
    assert yearly_cost(make_program(), "MI") == 10000 + 15000


def test_chance():
    assert chance(3.5, 0.40) == MATCH


def test_check_gpa():
    check_gpa(3.5)
    with pytest.raises(ValueError):
        check_gpa(5.0)


def test_find_programs():
    result = find_programs([make_program()], make_student())[0]
    assert (result.program.university, result.cost, result.chance) == ("Test University", 25000, MATCH)


def test_qualifies():
    assert qualifies(make_scholarship(), make_student())


def test_find_scholarships_biggest_first():
    found = find_scholarships([make_scholarship(name="Small", amount=1000),
                               make_scholarship(name="Big", amount=9000)], make_student())
    assert [s.name for s in found] == ["Big", "Small"]


def test_find_scholarships_same_amount_by_name():
    found = find_scholarships([make_scholarship(name="Zeta"), make_scholarship(name="Alpha")],
                              make_student())
    assert [s.name for s in found] == ["Alpha", "Zeta"]


def test_upcoming_sorted_by_date():
    found = upcoming([("B", date(2027, 1, 5)), ("A", date(2026, 11, 20))], date(2026, 11, 1))
    assert [d.name for d in found] == ["A", "B"]


def test_today_is_the_real_date():
    assert today() == date.today()
