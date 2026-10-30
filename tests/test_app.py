from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from gradmatch.data_loader import DataError
from helpers import APP, DATA, make_program


def open_app():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    return at


def search(at, field="Computer Science", gpa=3.5, home_state="MI", budget=40000):
    at.selectbox(key="field").set_value(field)
    at.number_input(key="gpa").set_value(gpa)
    at.selectbox(key="home_state").set_value(home_state)
    at.number_input(key="budget").set_value(budget)
    at.button[0].click().run()
    assert not at.exception
    return at


def test_page_opens():
    at = open_app()
    assert at.title[0].value == "GradMatch"
    assert at.selectbox(key="field").options == ["Computer Science", "Data Science"]
    assert at.dataframe.len == 0


def test_michigan_student_finds_cs_programs():
    at = search(open_app())
    table = at.dataframe[0].value
    assert list(table.columns) == ["University", "Program", "State", "Yearly cost", "Chance", "Website"]
    assert list(table["University"]) == ["Grand Valley State University", "Wayne State University"]
    assert list(table["Yearly cost"]) == ["$32,600", "$38,200"]
    assert "2 programs found" in at.success[0].value


def test_student_sees_chance():
    table = search(open_app(), budget=100000).dataframe[0].value
    chances = dict(zip(table["University"], table["Chance"]))
    assert chances["Grand Valley State University"] == "Safety"
    assert chances["Ohio State University"] == "Match"
    assert chances["Stanford University"] == "Reach"


def test_home_state_changes_cost():
    table = search(open_app(), field="Data Science", home_state="IN", budget=32000).dataframe[0].value
    assert list(table["University"]) == ["Indiana University Bloomington"]
    assert list(table["Yearly cost"]) == ["$31,000"]


def test_small_budget_shows_message():
    at = search(open_app(), budget=10000)
    assert at.dataframe.len == 0
    assert "Try a bigger budget" in at.info[0].value


def test_app_uses_the_loader():
    loader = Mock(return_value=[make_program(university="Mock University")])
    with patch("gradmatch.data_loader.load_programs", loader):
        at = open_app()
        at.button[0].click().run()
    loader.assert_called_with(DATA)
    assert list(at.dataframe[0].value["University"]) == ["Mock University"]


def test_bad_data_shows_error():
    with patch("gradmatch.data_loader.load_programs", Mock(side_effect=DataError("line 3: bad number"))):
        at = AppTest.from_file(APP, default_timeout=30).run()
    assert "line 3: bad number" in at.error[0].value
    assert len(at.button) == 0
