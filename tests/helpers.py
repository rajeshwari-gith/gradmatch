"""Small helpers the tests share."""
from pathlib import Path

from gradmatch.models import Program, Student

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "app" / "streamlit_app.py")
DATA = ROOT / "data" / "programs.csv"
HEADER = "university,program,field,state,tuition_in_state,tuition_out_state,living_cost,avg_gpa,website\n"


def make_program(**changes) -> Program:
    """A made-up program. Pass only the values a test cares about."""
    values = dict(university="Test University", program="MS in Computer Science",
                  field="Computer Science", state="MI", tuition_in_state=10000,
                  tuition_out_state=20000, living_cost=15000, avg_gpa=3.5,
                  website="https://example.edu")
    values.update(changes)
    return Program(**values)


def make_student(**changes) -> Student:
    values = dict(gpa=3.5, field="Computer Science", home_state="MI", budget=40000)
    values.update(changes)
    return Student(**values)


def write_csv(folder, *rows: str) -> Path:
    """Write a small programs file with the given data lines."""
    path = folder / "programs.csv"
    path.write_text(HEADER + "".join(row + "\n" for row in rows), encoding="utf-8")
    return path


GOOD_ROW = "Test University,MS in CS,Computer Science,MI,10000,20000,15000,3.5,https://example.edu"
