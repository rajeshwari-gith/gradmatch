# Decision table tests for chance and scholarships
from programs import chance
from scholarships import qualifies
from tests.helpers import make_scholarship, make_student


def test_decision_tables():
    # REQ-4: table C in TEST_PLAN.md (acceptance rate, GPA -> chance)
    table_c = [(0.05, 4.0, "Reach"), (0.15, 3.8, "Match"), (0.15, 3.5, "Reach"), (0.40, 3.8, "Safety"),
               (0.40, 3.5, "Match"), (0.40, 2.5, "Reach"), (0.80, 3.5, "Safety"), (0.80, 2.5, "Match")]
    for rate, gpa, expected in table_c:
        assert chance(gpa, rate) == expected

    # REQ-5: table S in TEST_PLAN.md (degree, field, GPA -> shown?)
    table_s = [(make_scholarship(degrees="PhD"), 3.5, False),
               (make_scholarship(fields="Statistics"), 3.5, False),
               (make_scholarship(fields="Computer Science", min_gpa=3.0), 2.5, False),
               (make_scholarship(fields="Any"), 3.5, True)]
    for scholarship, gpa, shown in table_s:
        assert qualifies(scholarship, make_student(gpa=gpa)) == shown
