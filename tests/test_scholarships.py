import pytest

from gradmatch.scholarships import find_scholarships, qualifies
from helpers import make_scholarship, make_student


def test_student_who_meets_every_rule_qualifies():
    assert qualifies(make_scholarship(), make_student())


# decision table: one rule broken at a time
@pytest.mark.parametrize("scholarship, student", [
    (make_scholarship(degrees=("PhD",)), make_student(degree="MS")),
    (make_scholarship(fields=("Mechanical Engineering",)), make_student()),
    (make_scholarship(citizenship=("US",)), make_student(citizenship="International")),
    (make_scholarship(min_gpa=3.6), make_student(gpa=3.5)),
], ids=["degree", "field", "citizenship", "gpa"])
def test_one_rule_broken(scholarship, student):
    assert not qualifies(scholarship, student)


def test_listed_field_qualifies():
    assert qualifies(make_scholarship(fields=("Computer Science",)), make_student())


def test_any_citizenship_qualifies():
    assert qualifies(make_scholarship(citizenship=("Any",)), make_student(citizenship="International"))


@pytest.mark.parametrize("gpa, expected", [(2.99, False), (3.0, True), (3.01, True)])
def test_gpa_edge(gpa, expected):
    assert qualifies(make_scholarship(min_gpa=3.0), make_student(gpa=gpa)) == expected


def test_biggest_amount_first_and_others_left_out():
    found = find_scholarships([make_scholarship(name="Small", amount=1000),
                               make_scholarship(name="PhD only", degrees=("PhD",)),
                               make_scholarship(name="Big", amount=9000)], make_student())
    assert [s.name for s in found] == ["Big", "Small"]


def test_no_scholarships():
    assert find_scholarships([], make_student()) == []
