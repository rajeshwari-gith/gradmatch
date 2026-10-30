from datetime import date
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from gradmatch.data_loader import DataError
from helpers import APP, PROGRAMS, make_program


def open_app():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    return at


def search(at, degree="MS", field="Computer Science", gpa=3.5, home_state="MI", budget=40000,
           citizenship="US citizen", states=(), today=date(2026, 11, 20)):
    at.radio(key="degree").set_value(degree)
    at.selectbox(key="field").set_value(field)
    at.number_input(key="gpa").set_value(gpa)
    at.selectbox(key="home_state").set_value(home_state)
    at.number_input(key="budget").set_value(budget)
    at.selectbox(key="citizenship").set_value(citizenship)
    at.multiselect(key="states").set_value(list(states))
    with patch("gradmatch.deadlines.today", Mock(return_value=today)):
        at.button[0].click().run()
    assert not at.exception
    return at


def table(at, title):
    return at.dataframe[["Programs", "Scholarships", "Deadlines"].index(title)].value


def test_page_opens():
    at = open_app()
    assert at.title[0].value == "GradMatch"
    assert at.selectbox(key="field").options == [
        "Computer Science", "Electrical Engineering", "Mechanical Engineering", "Statistics"]
    assert at.dataframe.len == 0


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
    assert "Funding" in programs.columns
    names = list(table(at, "Scholarships")["Name"])
    assert names[0] == "DoD National Defense Science and Engineering Graduate Fellowship"
    assert "GVSU Graduate Assistantship" not in names


def test_story_3_student_is_warned_about_a_close_deadline():
    at = search(open_app(), today=date(2026, 11, 20))
    assert "DoD SMART Scholarship is due in 11 days" in at.warning[0].value
    deadlines = table(at, "Deadlines")
    assert list(deadlines["Date"]) == sorted(deadlines["Date"])


def test_no_warning_when_nothing_is_close():
    at = search(open_app(), today=date(2026, 12, 2))
    assert at.warning.len == 0


def test_ms_table_has_no_funding_column():
    assert "Funding" not in table(search(open_app()), "Programs").columns


def test_only_chosen_states_are_shown():
    programs = table(search(open_app(), states=["OH"], budget=100000), "Programs")
    assert set(programs["State"]) == {"OH"}


def test_small_budget_shows_message():
    at = search(open_app(), budget=1000)
    assert "No programs fit your budget" in at.info[0].value


def test_nothing_matches_shows_messages():
    at = search(open_app(), field="Mechanical Engineering", citizenship="International",
                budget=1000, today=date(2027, 3, 1))
    assert [i.value for i in at.info] == ["No programs fit your budget. Try a bigger budget.",
                                          "No upcoming deadlines."]


def test_international_student_gets_no_us_only_awards():
    at = search(open_app(), citizenship="International")
    assert list(table(at, "Scholarships")["Name"]) == ["GVSU Graduate Assistantship"]


def test_no_scholarships_message():
    at = search(open_app(), degree="PhD", field="Mechanical Engineering",
                citizenship="International")
    assert "No scholarships match you." in [i.value for i in at.info]


def test_app_uses_the_loader():
    loader = Mock(return_value=[make_program(university="Mock University")])
    with patch("gradmatch.data_loader.load_programs", loader):
        at = open_app()
        at.button[0].click().run()
    loader.assert_called_with(PROGRAMS)
    assert list(table(at, "Programs")["University"]) == ["Mock University"]


def test_bad_data_shows_error():
    with patch("gradmatch.data_loader.load_programs", Mock(side_effect=DataError("line 3: bad"))):
        at = AppTest.from_file(APP, default_timeout=30).run()
    assert "line 3: bad" in at.error[0].value
    assert len(at.button) == 0
