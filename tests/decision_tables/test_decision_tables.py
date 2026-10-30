from gradmatch.fit import MATCH, REACH, SAFETY, chance
from gradmatch.scholarships import qualifies
from helpers import make_scholarship, make_student


def test_chance_table():
    # acceptance rate: GPA 4.0, GPA 3.5, GPA 2.5
    table = {
        0.05: [REACH, REACH, REACH],
        0.15: [MATCH, REACH, REACH],
        0.40: [SAFETY, MATCH, REACH],
        0.80: [SAFETY, SAFETY, MATCH],
    }
    for rate, expected in table.items():
        assert [chance(gpa, rate) for gpa in [4.0, 3.5, 2.5]] == expected


def test_scholarship_table():
    # degree fits, field fits, GPA high enough -> shown
    table = [
        (True, True, True, True),
        (False, True, True, False),
        (True, False, True, False),
        (True, True, False, False),
    ]
    for degree_ok, field_ok, gpa_ok, shown in table:
        scholarship = make_scholarship(degrees=("MS",) if degree_ok else ("PhD",),
                                       fields=("Computer Science",) if field_ok else ("Statistics",),
                                       min_gpa=3.0)
        assert qualifies(scholarship, make_student(gpa=3.5 if gpa_ok else 2.5)) == shown
    assert qualifies(make_scholarship(fields=("Any",)), make_student(field="Statistics"))
