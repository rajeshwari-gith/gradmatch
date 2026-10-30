from datetime import date

from helpers import open_app, search, table


def test_page_opens():
    at = open_app()
    assert at.title[0].value == "GradMatch"
    assert at.selectbox(key="field").options == [
        "Computer Science", "Electrical Engineering", "Mechanical Engineering", "Statistics"]


def test_search_shows_programs_and_scholarships():
    at = search(open_app(), states=["OH"], budget=100000, today=date(2026, 12, 2))
    assert set(table(at, "Programs")["State"]) == {"OH"}
    scholarships = table(at, "Scholarships")
    assert dict(zip(scholarships["Name"], scholarships["Open to"]))["DoD SMART Scholarship"] == "US citizens"
    assert at.warning.len == 0


def test_nothing_matches_shows_messages():
    at = search(open_app(), field="Mechanical Engineering", budget=1000, today=date(2027, 3, 1))
    assert [i.value for i in at.info] == ["No programs fit your budget. Try a bigger budget.",
                                          "No upcoming deadlines."]
