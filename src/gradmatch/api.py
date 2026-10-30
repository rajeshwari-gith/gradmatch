from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

from gradmatch.data_loader import load_programs, load_scholarships
from gradmatch.database import create_database, get_programs
from gradmatch.deadlines import upcoming
from gradmatch.models import Student
from gradmatch.scholarships import find_scholarships
from gradmatch.search import find_programs

DATA = Path(__file__).resolve().parents[2] / "data"
DATABASE = create_database(load_programs(DATA / "programs.csv"))
SCHOLARSHIPS = load_scholarships(DATA / "scholarships.csv")

app = FastAPI(title="GradMatch")


@app.get("/programs")
def programs(degree: str, field: str, gpa: float, home_state: str, budget: int,
             states: list[str] = Query([])):
    student = Student(degree, field, gpa, home_state, budget, "US", tuple(states))
    try:
        results = find_programs(get_programs(DATABASE, degree, field), student)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return [{"university": r.program.university, "program": r.program.program,
             "state": r.program.state, "yearly_cost": r.cost, "chance": r.chance, "funding": r.funding}
            for r in results]


@app.get("/scholarships")
def scholarships(degree: str, field: str, gpa: float, citizenship: str):
    student = Student(degree, field, gpa, "", 0, citizenship)
    return [{"name": s.name, "amount": s.amount, "deadline": s.deadline.isoformat()}
            for s in find_scholarships(SCHOLARSHIPS, student)]


@app.get("/deadlines")
def deadlines(today: date | None = None):
    return [{"name": d.name, "date": d.date.isoformat(), "days_left": d.days_left, "soon": d.soon}
            for d in upcoming(SCHOLARSHIPS, today or date.today())]
