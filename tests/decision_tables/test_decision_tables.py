import pytest

from gradmatch.fit import MATCH, REACH, SAFETY, chance
from gradmatch.scholarships import qualifies
from helpers import make_scholarship, make_student


# Chance: acceptance rate (rows) x GPA (columns)
@pytest.mark.parametrize("rate, gpa, expected", [
    (0.05, 4.0, REACH), (0.05, 3.5, REACH), (0.05, 2.5, REACH),
    (0.15, 4.0, MATCH), (0.15, 3.5, REACH), (0.15, 2.5, REACH),
    (0.40, 4.0, SAFETY), (0.40, 3.5, MATCH), (0.40, 2.5, REACH),
    (0.80, 4.0, SAFETY), (0.80, 3.5, SAFETY), (0.80, 2.5, MATCH),
])
def test_chance_table(rate, gpa, expected):
    assert chance(gpa, rate) == expected


# Scholarship: degree fits? field fits? GPA high enough? -> shown only if all three are yes
@pytest.mark.parametrize("degree_ok, field_ok, gpa_ok", [
    (True, True, True), (False, True, True), (True, False, True), (True, True, False),
    (False, False, False),
])
def test_scholarship_table(degree_ok, field_ok, gpa_ok):
    scholarship = make_scholarship(degrees=("MS",) if degree_ok else ("PhD",),
                                   fields=("Computer Science",) if field_ok else ("Statistics",),
                                   min_gpa=3.0)
    student = make_student(gpa=3.5 if gpa_ok else 2.5)
    assert qualifies(scholarship, student) == (degree_ok and field_ok and gpa_ok)


def test_any_field_fits_every_field():
    assert qualifies(make_scholarship(fields=("Any",)), make_student(field="Statistics"))
