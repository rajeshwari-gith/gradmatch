# Data-flow test: values through find_programs
from programs import find_programs
from tests.helpers import make_program, make_student


def test_values_flow_through_find_programs():
    # REQ-3: home_state -> cost (in-state $25,000, out-of-state $35,000)
    assert find_programs([make_program()], make_student(home_state="OH"))[0]["cost"] == 35000

    # REQ-4: gpa -> chance
    assert find_programs([make_program()], make_student(gpa=3.9))[0]["chance"] == "Safety"

    # REQ-2: cost -> sort, cheapest first, same cost A-Z
    programs = [make_program(university="C", living_cost=20000),
                make_program(university="B"), make_program(university="A")]
    assert [r["program"]["university"] for r in find_programs(programs, make_student())] == ["A", "B", "C"]
