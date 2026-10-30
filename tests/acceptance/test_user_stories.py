from datetime import date

from helpers import open_app, search, table


def test_story_1_student_finds_ms_programs_they_can_afford():
    at = search(open_app(), budget=35000)
    programs = table(at, "Programs")
    costs = [int(c.strip("$").replace(",", "")) for c in programs["Yearly cost"]]
    assert len(costs) > 0
    assert costs == sorted(costs) and max(costs) <= 35000
    assert set(programs["Chance"]) <= {"Safety", "Match", "Reach"}


def test_story_2_student_finds_phd_programs_and_fellowships():
    at = search(open_app(), degree="PhD", budget=100000)
    programs = table(at, "Programs")
    assert len(programs) == 8
    names = list(table(at, "Scholarships")["Name"])
    assert names[0] == "DoD National Defense Science and Engineering Graduate Fellowship"
    assert "GVSU Graduate Assistantship" not in names


def test_story_3_student_is_warned_about_a_close_deadline():
    at = search(open_app(), today=date(2026, 11, 20))
    assert "DoD SMART Scholarship is due in 11 days" in at.warning[0].value
    deadlines = table(at, "Deadlines")
    assert list(deadlines["Date"]) == sorted(deadlines["Date"])
