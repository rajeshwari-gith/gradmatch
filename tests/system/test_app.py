from datetime import date

from helpers import open_app, search, table


def test_page_opens():
    at = open_app()
    assert at.title[0].value == "GradMatch"
    assert at.selectbox(key="field").options == [
        "Computer Science", "Electrical Engineering", "Mechanical Engineering", "Statistics"]
    assert at.dataframe.len == 0


def test_only_chosen_states_are_shown():
    programs = table(search(open_app(), states=["OH"], budget=100000), "Programs")
    assert set(programs["State"]) == {"OH"}


def test_scholarships_show_who_can_apply():
    scholarships = table(search(open_app()), "Scholarships")
    open_to = dict(zip(scholarships["Name"], scholarships["Open to"]))
    assert open_to["DoD SMART Scholarship"] == "US citizens"
    assert open_to["GVSU Graduate Assistantship"] == "Everyone"


def test_no_warning_when_nothing_is_close():
    assert search(open_app(), today=date(2026, 12, 2)).warning.len == 0


def test_nothing_matches_shows_messages():
    at = search(open_app(), field="Mechanical Engineering", budget=1000, today=date(2027, 3, 1))
    assert [i.value for i in at.info] == ["No programs fit your budget. Try a bigger budget.",
                                          "No upcoming deadlines."]
