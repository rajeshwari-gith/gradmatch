"""Week 10 - System testing.

These tests run the whole app (web page + real data) with Streamlit's AppTest tool.
"""
from streamlit.testing.v1 import AppTest

from helpers import APP


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


def test_app_opens_with_title_and_form():
    at = open_app()
    assert at.title[0].value == "GradMatch"
    assert at.button[0].label == "Find programs"
    assert at.dataframe.len == 0  # no results before searching


def test_field_list_comes_from_the_data():
    at = open_app()
    assert at.selectbox(key="field").options == ["Computer Science", "Data Science"]


def test_search_shows_a_table_of_results():
    at = search(open_app())
    table = at.dataframe[0].value
    assert list(table.columns) == ["University", "Program", "State", "Yearly cost", "Chance", "Website"]
    assert list(table["Yearly cost"]) == ["$32,600", "$38,200"]
    assert "2 programs found" in at.success[0].value


def test_search_with_tiny_budget_shows_a_message():
    at = search(open_app(), budget=1000)
    assert at.dataframe.len == 0
    assert "No programs fit your budget" in at.info[0].value


def test_changing_the_home_state_changes_the_cost():
    at = search(open_app(), field="Data Science", home_state="IN", budget=32000)
    table = at.dataframe[0].value
    assert list(table["University"]) == ["Indiana University Bloomington"]
    assert list(table["Yearly cost"]) == ["$31,000"]
