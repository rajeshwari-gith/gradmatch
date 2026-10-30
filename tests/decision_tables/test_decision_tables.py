from tests.helpers import make_scholarship, make_student
from programs import MATCH, REACH, SAFETY, chance
from scholarships import qualifies


def test_decision_tables():
    # REQ-4: table C in TEST_PLAN.md (acceptance rate, GPA -> chance)
    table_c = [(0.05, 4.0, REACH), (0.15, 3.8, MATCH), (0.15, 3.5, REACH), (0.40, 3.8, SAFETY),
               (0.40, 3.5, MATCH), (0.40, 2.5, REACH), (0.80, 3.5, SAFETY), (0.80, 2.5, MATCH)]
    for rate, gpa, expected in table_c:
        assert chance(gpa, rate) == expected

    # REQ-5: table S in TEST_PLAN.md (degree, field, GPA -> shown?)
    table_s = [(make_scholarship(degrees="PhD"), 3.5, False),
               (make_scholarship(fields="Statistics"), 3.5, False),
               (make_scholarship(fields="Computer Science", min_gpa=3.0), 2.5, False),
               (make_scholarship(fields="Any"), 3.5, True)]
    for scholarship, gpa, shown in table_s:
        assert qualifies(scholarship, make_student(gpa=gpa)) == shown
