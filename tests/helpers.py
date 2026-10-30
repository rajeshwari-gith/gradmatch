# Made-up programs, scholarships and students, and app helpers for the tests
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "app.py")
DATABASE = ROOT / "data" / "gradmatch.db"


def make_program(**changes):
    values = dict(university="Test University", degree="MS",
                  field="Computer Science", state="MI", tuition_in_state=10000,
                  tuition_out_state=20000, living_cost=15000, acceptance_rate=0.5, deadline="2027-02-01",
                  website="https://example.edu")
    values.update(changes)
    return values


def make_scholarship(**changes):
    values = dict(name="Test Award", amount=5000, degrees="MS;PhD", fields="Any",
                  min_gpa=3.0, open_to="Everyone", deadline="2026-12-01",
                  website="https://example.org")
    values.update(changes)
    return values


def make_student(**changes):
    values = dict(degree="MS", field="Computer Science", gpa=3.5, home_state="MI", budget=40000,
                  states=[])
    values.update(changes)
    return values


def open_app():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    return at


def search(at, degree="MS", field="Computer Science", gpa=3.5, home_state="MI", budget=40000,
           states=(), today=date(2026, 11, 20)):
    at.radio(key="degree").set_value(degree)
    at.selectbox(key="field").set_value(field)
    at.number_input(key="gpa").set_value(gpa)
    at.selectbox(key="home_state").set_value(home_state)
    at.number_input(key="budget").set_value(budget)
    at.multiselect(key="states").set_value(list(states))
    with patch("scholarships.today", Mock(return_value=today)):
        at.button[0].click().run()
    assert not at.exception
    return at


def table(at, title):
    return at.dataframe[["Programs", "Scholarships", "Deadlines"].index(title)].value
