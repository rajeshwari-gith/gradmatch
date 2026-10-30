import pytest

from fit import MATCH, REACH, SAFETY, chance
from scholarships import qualifies
from helpers import make_scholarship, make_student


# REQ-4 chance table from TEST_PLAN.md, one test per rule
@pytest.mark.parametrize("rate, gpa, expected", [
    pytest.param(0.05, 4.0, REACH, id="C1-under-10%"),
    pytest.param(0.15, 3.8, MATCH, id="C2-10-24%-strong-gpa"),
    pytest.param(0.15, 3.5, REACH, id="C3-10-24%-other-gpa"),
    pytest.param(0.40, 3.8, SAFETY, id="C4-25-59%-strong-gpa"),
    pytest.param(0.40, 3.5, MATCH, id="C5-25-59%-middle-gpa"),
    pytest.param(0.40, 2.5, REACH, id="C6-25-59%-weak-gpa"),
    pytest.param(0.80, 3.5, SAFETY, id="C7-60%-up-gpa-3-or-more"),
    pytest.param(0.80, 2.5, MATCH, id="C8-60%-up-weak-gpa"),
])
def test_req4_chance_table(rate, gpa, expected):
    assert chance(gpa, rate) == expected


# REQ-5 scholarship table from TEST_PLAN.md, one test per rule
@pytest.mark.parametrize("scholarship, gpa, shown", [
    pytest.param(make_scholarship(degrees=("PhD",)), 3.5, False, id="S1-wrong-degree"),
    pytest.param(make_scholarship(fields=("Statistics",)), 3.5, False, id="S2-wrong-field"),
    pytest.param(make_scholarship(fields=("Computer Science",), min_gpa=3.0), 2.5, False,
                 id="S3-gpa-too-low"),
    pytest.param(make_scholarship(fields=("Any",)), 3.5, True, id="S4-all-fit-any-field"),
])
def test_req5_scholarship_table(scholarship, gpa, shown):
    assert qualifies(scholarship, make_student(gpa=gpa)) == shown
