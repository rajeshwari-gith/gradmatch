"""System tests for the profile form in app/streamlit_app.py.

Each test starts the real app with Streamlit's AppTest, fills in the form
the way a student would, presses "Find programs" and checks what is shown.

Techniques: equivalence partitioning (valid / invalid inputs) and
boundary-value analysis (GPA and GRE on and just outside their limits).
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

pytestmark = pytest.mark.system

# In plain words: system tests open the whole app (the real Streamlit page) without a browser,
# fill in the form, press the button and read what the page shows. These ones cover the form:
# what is accepted, what shows an error, and that every problem is listed at once.

APP = str(Path(__file__).resolve().parents[2] / "app" / "streamlit_app.py")


@pytest.fixture
def app():
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception
    return at


def submit(at):
    at.button[0].click().run()
    assert not at.exception
    return at


def accepted(at) -> bool:
    """The profile was saved (so the results are shown) and no error is on the page."""
    return "profile" in at.session_state and not at.error


def error_text(at):
    return " ".join(m.value for m in at.markdown) + " ".join(e.value for e in at.error)


# ---- The page loads ----

def test_page_shows_title_and_form(app):
    assert any('class="gm-serif">GradMatch<' in m.value for m in app.markdown)
    assert app.button[0].label == "Find programs"
    assert not app.error and "profile" not in app.session_state


def test_field_list_comes_from_the_data(app):
    assert set(app.selectbox(key="field").options) == {"Computer Science", "Data Science"}


def test_default_form_values(app):
    assert app.radio(key="degree").value == "MS"
    assert app.number_input(key="gpa").value == 3.5
    assert app.number_input(key="budget").value == 40_000
    assert app.number_input(key="gre").value is None
    assert app.selectbox(key="home_state").value == "MI"


# ---- Valid input ----

def test_default_profile_is_accepted(app):
    submit(app)
    assert accepted(app)


def test_accepted_profile_is_saved_with_the_entered_values(app):
    app.radio(key="degree").set_value("PhD")
    app.selectbox(key="field").set_value("Data Science")
    app.number_input(key="gpa").set_value(3.8)
    app.number_input(key="gre").set_value(320)
    app.multiselect(key="preferred_states").set_value(["CA", "TX"])
    submit(app)
    profile = app.session_state["profile"]
    assert profile.degree_sought == "PhD"
    assert profile.field == "Data Science"
    assert profile.gpa == 3.8
    assert profile.gre == 320
    assert profile.toefl is None
    assert profile.preferred_states == ("CA", "TX")


def test_summary_is_shown_after_success(app):
    app.number_input(key="budget").set_value(25_000)
    submit(app)
    summary = " ".join(m.value for m in app.markdown)
    assert "in Computer Science within $25,000 / year · any state" in summary


# ---- Boundary-value analysis on GPA (limit 4.0) ----

@pytest.mark.parametrize("gpa", [0.0, 4.0])
def test_gpa_on_the_limit_is_accepted(app, gpa):
    app.number_input(key="gpa").set_value(gpa)
    submit(app)
    assert accepted(app)


def test_gpa_just_over_the_limit_shows_an_error(app):
    app.number_input(key="gpa").set_value(4.05)
    submit(app)
    assert "GPA must be between 0.0 and 4.0." in error_text(app)
    assert "profile" not in app.session_state


# ---- Boundary-value analysis on GRE (limits 260 and 340) ----

@pytest.mark.parametrize("gre", [260, 340])
def test_gre_on_the_limit_is_accepted(app, gre):
    app.number_input(key="gre").set_value(gre)
    submit(app)
    assert accepted(app)


@pytest.mark.parametrize("gre", [259, 341])
def test_gre_just_outside_the_limit_shows_an_error(app, gre):
    app.number_input(key="gre").set_value(gre)
    submit(app)
    assert "GRE score must be between 260 and 340." in error_text(app)


# ---- Decision table: TOEFL for international students ----
# citizenship   | TOEFL entered | result
# International | no            | error
# International | yes           | accepted
# U.S. citizen  | no            | accepted

def test_international_student_without_toefl_gets_an_error(app):
    app.selectbox(key="citizenship").set_value("International")
    submit(app)
    assert "TOEFL score is required for international students." in error_text(app)
    assert "profile" not in app.session_state


def test_international_student_with_toefl_is_accepted(app):
    app.selectbox(key="citizenship").set_value("International")
    app.number_input(key="toefl").set_value(95)
    submit(app)
    assert accepted(app)


def test_us_citizen_without_toefl_is_accepted(app):
    app.selectbox(key="citizenship").set_value("US")
    submit(app)
    assert accepted(app)


# ---- Several problems at once are all shown ----

def test_every_problem_is_listed_together(app):
    app.number_input(key="gpa").set_value(6.0)
    app.number_input(key="gre").set_value(200)
    app.selectbox(key="citizenship").set_value("International")
    submit(app)
    text = error_text(app)
    assert "GPA must be between 0.0 and 4.0." in text
    assert "GRE score must be between 260 and 340." in text
    assert "TOEFL score is required for international students." in text


def test_error_goes_away_after_the_student_fixes_it(app):
    app.number_input(key="gpa").set_value(6.0)
    submit(app)
    assert app.error
    app.number_input(key="gpa").set_value(3.2)
    submit(app)
    assert accepted(app)
