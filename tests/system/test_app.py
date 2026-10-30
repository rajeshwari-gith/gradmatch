from datetime import date
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from helpers import APP, make_program, open_app, search, table


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
    with patch("gradmatch.database.get_programs", loader):
        at = search(open_app())
    assert "Test University (MS in Computer Science) is due in 5 days" in at.warning[0].value


def test_small_budget_shows_message():
    at = search(open_app(), budget=1000)
    assert "No programs fit your budget" in at.info[0].value


def test_nothing_matches_shows_messages():
    at = search(open_app(), field="Mechanical Engineering", budget=1000, today=date(2027, 3, 1))
    assert [i.value for i in at.info] == ["No programs fit your budget. Try a bigger budget.",
                                          "No upcoming deadlines."]


def test_scholarships_show_who_can_apply():
    scholarships = table(search(open_app()), "Scholarships")
    open_to = dict(zip(scholarships["Name"], scholarships["Open to"]))
    assert open_to["DoD SMART Scholarship"] == "US citizens"
    assert open_to["GVSU Graduate Assistantship"] == "Everyone"


def test_no_scholarships_message():
    with patch("gradmatch.database.get_scholarships", Mock(return_value=[])):
        at = search(open_app())
    assert "No scholarships match your degree, field and GPA." in [i.value for i in at.info]


def test_app_reads_programs_from_the_database():
    loader = Mock(return_value=[make_program(university="Mock University")])
    with patch("gradmatch.database.get_programs", loader):
        at = open_app()
        at.button[0].click().run()
    loader.assert_called()
    assert list(table(at, "Programs")["University"]) == ["Mock University"]


def test_empty_database_shows_error():
    with patch("gradmatch.database.get_programs", Mock(return_value=[])):
        at = AppTest.from_file(APP, default_timeout=30).run()
    assert at.error[0].value == "No programs found in the database."
    assert len(at.button) == 0
