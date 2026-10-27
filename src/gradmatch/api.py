"""GradMatch REST API (FastAPI).

This file only turns HTTP requests into calls to the existing modules and
their results into JSON. It has no business rules of its own.

Run it with:  PYTHONPATH=src uvicorn gradmatch.api:app --reload

The data folder is GRADMATCH_DATA_DIR if it is set, otherwise data/.
"""
import os
from dataclasses import asdict
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from gradmatch.data_loader import load_living_costs, load_programs, load_scholarships
from gradmatch.deadlines import deadline_of, deadline_status, upcoming
from gradmatch.models import Program, Scholarship, StudentProfile
from gradmatch.scholarships import eligible_scholarships
from gradmatch.search import ProgramResult, search_programs
from gradmatch.validation import validate_profile

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# programs.csv has over 22,000 rows, so list answers are paged.
PROGRAMS_LIMIT, MATCH_LIMIT, MAX_LIMIT = 100, 50, 1000

app = FastAPI(title="GradMatch", description="Graduate programs, scholarships and deadlines.")


class ProfileIn(BaseModel):
    """The JSON body of POST /match. Field names match StudentProfile."""
    degree_sought: str
    gpa: float
    field: str
    home_state: str
    citizenship: str
    annual_budget: float
    preferred_states: list[str] = []
    gre: int | None = None
    toefl: int | None = None
    sat: int | None = None
    act: int | None = None
    special: list[str] = []


# ---- Endpoints ----

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/programs")
def programs(field: str | None = None, degree: str | None = None, state: str | None = None,
             limit: int = Query(PROGRAMS_LIMIT, ge=1, le=MAX_LIMIT),
             offset: int = Query(0, ge=0)):
    """Programs in file order, optionally filtered by exact field, degree and state.

    Returns at most `limit` programs (1-1000, default 100), starting after the first
    `offset` matches. FastAPI answers 422 for a limit or offset outside those ranges.
    """
    result = load_programs(data_dir() / "programs.csv")
    if field is not None:
        result = [p for p in result if p.field == field]
    if degree is not None:
        result = [p for p in result if p.degree == degree]
    if state is not None:
        result = [p for p in result if p.state == state]
    return [asdict(p) for p in result[offset:offset + limit]]


@app.post("/match")
def match(body: ProfileIn, limit: int = Query(MATCH_LIMIT, ge=1, le=MAX_LIMIT)):
    """Programs and scholarships for a student; 422 with the validation messages if invalid.

    `programs` holds the first `limit` results in the search's order (default 50) and
    `total_programs` says how many matched in all.
    """
    profile = StudentProfile(
        degree_sought=body.degree_sought,
        gpa=body.gpa,
        field=body.field,
        home_state=body.home_state,
        citizenship=body.citizenship,
        annual_budget=body.annual_budget,
        preferred_states=tuple(body.preferred_states),
        gre=body.gre,
        toefl=body.toefl,
        special=tuple(body.special),
        sat=body.sat,
        act=body.act,
    )
    errors = validate_profile(profile)
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    folder = data_dir()
    results = search_programs(profile, load_programs(folder / "programs.csv"),
                              load_living_costs(folder / "living_costs.csv"))
    scholarships = eligible_scholarships(profile, load_scholarships(folder / "scholarships.csv"))
    return {"total_programs": len(results),
            "programs": [program_result_json(r) for r in results[:limit]],
            "scholarships": [asdict(s) for s in scholarships]}


@app.get("/deadlines")
def deadlines(today: date | None = None):
    """Open program and scholarship deadlines, soonest first.

    `today` is a query parameter (YYYY-MM-DD); FastAPI answers 422 if it is not a date.
    Only when it is left out does the API use the server's date: this is the edge of
    the program, like the UI, so the logic modules still never call date.today().
    """
    today = today or date.today()
    folder = data_dir()
    items = load_programs(folder / "programs.csv") + load_scholarships(folder / "scholarships.csv")
    return [deadline_json(item, today) for item in upcoming(items, today)]


# ---- Helpers ----

def data_dir() -> Path:
    return Path(os.environ.get("GRADMATCH_DATA_DIR", DEFAULT_DATA_DIR))


def program_result_json(result: ProgramResult) -> dict:
    """The program's fields plus what the search worked out for this student."""
    return {**asdict(result.program), "yearly_cost": result.yearly_cost,
            "total_cost": result.total_cost, "fit": result.fit, "funding": result.funding}


def deadline_json(item: Program | Scholarship, today: date) -> dict:
    if isinstance(item, Program):
        kind, item_id, name = "program", item.program_id, f"{item.university} – {item.program_name}"
    else:
        kind, item_id, name = "scholarship", item.scholarship_id, item.name
    deadline = deadline_of(item)
    return {"kind": kind, "id": item_id, "name": name, "deadline": deadline,
            "status": deadline_status(deadline, today), "website": item.website}
