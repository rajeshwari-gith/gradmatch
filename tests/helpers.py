from datetime import date
from pathlib import Path

from gradmatch.models import Program, Scholarship, Student

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "app" / "streamlit_app.py")
PROGRAMS = ROOT / "data" / "programs.csv"
SCHOLARSHIPS = ROOT / "data" / "scholarships.csv"

PROGRAM_HEADER = ("university,program,degree,field,state,tuition_in_state,tuition_out_state,"
                  "living_cost,acceptance_rate,stipend,avg_gre,deadline,website")
PROGRAM_ROW = "Test University,MS in CS,MS,Computer Science,MI,10000,20000,15000,0.5,,,,https://example.edu"
SCHOLARSHIP_HEADER = "name,amount,degrees,fields,min_gpa,citizenship,deadline,website"
SCHOLARSHIP_ROW = "Test Award,5000,MS;PhD,Any,3.0,US;PR,2026-12-01,https://example.org"


def make_program(**changes):
    values = dict(university="Test University", program="MS in Computer Science", degree="MS",
                  field="Computer Science", state="MI", tuition_in_state=10000,
                  tuition_out_state=20000, living_cost=15000, acceptance_rate=0.5, stipend=None,
                  avg_gre=None, deadline=None,
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
