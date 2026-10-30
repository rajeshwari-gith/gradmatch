from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from gradmatch.models import Program, Scholarship, Student

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "app" / "streamlit_app.py")
PROGRAMS = ROOT / "data" / "programs.csv"
SCHOLARSHIPS = ROOT / "data" / "scholarships.csv"

PROGRAM_HEADER = ("university,program,degree,field,state,tuition_in_state,tuition_out_state,"
                  "living_cost,acceptance_rate,stipend,avg_gre,deadline,website")
PROGRAM_ROW = "Test University,MS in CS,MS,Computer Science,MI,10000,20000,15000,0.5,0,310,2027-02-01,https://example.edu"
SCHOLARSHIP_HEADER = "name,amount,degrees,fields,min_gpa,citizenship,deadline,website"
SCHOLARSHIP_ROW = "Test Award,5000,MS;PhD,Any,3.0,US;PR,2026-12-01,https://example.org"


def make_program(**changes):
    values = dict(university="Test University", program="MS in Computer Science", degree="MS",
                  field="Computer Science", state="MI", tuition_in_state=10000,
                  tuition_out_state=20000, living_cost=15000, acceptance_rate=0.5, stipend=0,
                  avg_gre=310, deadline=date(2027, 2, 1),
                  website="https://example.edu")
    values.update(changes)
    return Program(**values)


def make_scholarship(**changes):
    values = dict(name="Test Award", amount=5000, degrees=("MS", "PhD"), fields=("Any",),
                  min_gpa=3.0, citizenship=("US", "PR"), deadline=date(2026, 12, 1),
                  website="https://example.org")
    values.update(changes)
    return Scholarship(**values)


def make_student(**changes):
    values = dict(degree="MS", field="Computer Science", gpa=3.5, home_state="MI", budget=40000,
                  citizenship="US")
    values.update(changes)
    return Student(**values)


def write_csv(folder, header, *rows):
    path = folder / "data.csv"
    path.write_text(header + "\n" + "".join(row + "\n" for row in rows), encoding="utf-8")
    return path


def open_app():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    return at


def search(at, degree="MS", field="Computer Science", gpa=3.5, home_state="MI", budget=40000,
           citizenship="US citizen", states=(), gre=None, today=date(2026, 11, 20)):
    at.radio(key="degree").set_value(degree)
    at.selectbox(key="field").set_value(field)
    at.number_input(key="gpa").set_value(gpa)
    at.selectbox(key="home_state").set_value(home_state)
    at.number_input(key="budget").set_value(budget)
    at.selectbox(key="citizenship").set_value(citizenship)
    at.multiselect(key="states").set_value(list(states))
    at.number_input(key="gre").set_value(gre)
    with patch("gradmatch.deadlines.today", Mock(return_value=today)):
        at.button[0].click().run()
    assert not at.exception
    return at


def table(at, title):
    return at.dataframe[["Programs", "Scholarships", "Deadlines"].index(title)].value
