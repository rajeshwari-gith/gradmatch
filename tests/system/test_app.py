from datetime import date
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from gradmatch.data_loader import DataError
from helpers import APP, PROGRAMS, make_program, open_app, search, table


def test_page_opens():
    at = open_app()
    assert at.title[0].value == "GradMatch"
    assert at.selectbox(key="field").options == [
        "Computer Science", "Electrical Engineering", "Mechanical Engineering", "Statistics"]
    assert at.dataframe.len == 0


def test_no_warning_when_nothing_is_close():
    at = search(open_app(), today=date(2026, 12, 2))
    assert at.warning.len == 0


def test_ms_table_has_no_funding_column():
    assert "Funding" not in table(search(open_app()), "Programs").columns


def test_only_chosen_states_are_shown():
    programs = table(search(open_app(), states=["OH"], budget=100000), "Programs")
    assert set(programs["State"]) == {"OH"}


def test_gre_is_accepted():
    assert len(table(search(open_app(), gre=320), "Programs")) > 0


def test_program_deadline_is_tracked():
    loader = Mock(return_value=[make_program(deadline=date(2026, 11, 25))])
    with patch("gradmatch.data_loader.load_programs", loader):
        at = search(open_app())
    assert "Test University (MS in Computer Science) is due in 5 days" in at.warning[0].value


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
