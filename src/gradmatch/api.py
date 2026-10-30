from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

from gradmatch.database import connect, get_programs, get_scholarships
from gradmatch.deadlines import upcoming
from gradmatch.fit import check_gpa
from gradmatch.models import Student
from gradmatch.scholarships import find_scholarships
from gradmatch.search import find_programs

connection = connect(Path(__file__).resolve().parents[2] / "data" / "gradmatch.db")
PROGRAMS = get_programs(connection)
SCHOLARSHIPS = get_scholarships(connection)
connection.close()

app = FastAPI(title="GradMatch")


@app.get("/programs")
def programs(degree: str, field: str, gpa: float, home_state: str, budget: int,
             states: list[str] = Query([]), gre: int | None = None):
    student = Student(degree, field, gpa, home_state, budget, tuple(states), gre)
    try:
        results = find_programs(PROGRAMS, student)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return [{"university": r.program.university, "program": r.program.program,
             "state": r.program.state, "yearly_cost": r.cost, "chance": r.chance,
             "funding": r.funding}
            for r in results]


@app.get("/scholarships")
def scholarships(degree: str, field: str, gpa: float):
    try:
        check_gpa(gpa)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    student = Student(degree, field, gpa, "", 0)
    return [{"name": s.name, "amount": s.amount, "open_to": s.open_to,
             "deadline": s.deadline.isoformat()}
            for s in find_scholarships(SCHOLARSHIPS, student)]


@app.get("/deadlines")
def deadlines(today: date | None = None):
    return [{"name": d.name, "date": d.date.isoformat(), "days_left": d.days_left, "soon": d.soon}
            for d in upcoming(deadline_list(), today or date.today())]


def deadline_list():
    dates = [(s.name, s.deadline) for s in SCHOLARSHIPS]
    dates += [(f"{p.university} ({p.program})", p.deadline) for p in PROGRAMS]
    return dates
