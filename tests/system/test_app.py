from datetime import date

from tests.helpers import open_app, search, table


def test_whole_app():
    at = open_app()
    assert at.title[0].value == "GradMatch"
    search(at, states=["OH"], budget=100000, today=date(2026, 12, 2))
    assert set(table(at, "Programs")["State"]) == {"OH"}
    assert "Open to" in table(at, "Scholarships").columns

    search(at, field="Mechanical Engineering", budget=1000, today=date(2027, 3, 1))
    assert [i.value for i in at.info] == ["No programs fit your budget. Try a bigger budget.",
                                          "No upcoming deadlines."]
