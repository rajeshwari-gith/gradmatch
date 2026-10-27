"""GradMatch REST API (FastAPI).

This file only turns HTTP requests into calls to the existing modules and
their results into JSON. It has no business rules of its own.

Run it with:  PYTHONPATH=src uvicorn gradmatch.api:app --reload

The data folder is GRADMATCH_DATA_DIR if it is set, otherwise data/.
"""
# In plain words: the same search as the website, but for other programs to call over HTTP
# and get JSON back (for example a phone app). This file has no rules of its own: it only
# reads the request, calls the same functions the website uses, and turns the answer into
# JSON. Keeping the rules in one place means the website and the API can never disagree.

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

# The real data folder, found from this file's own location so it works from any folder.
# Tests point GRADMATCH_DATA_DIR at a tiny made-up folder instead.
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# programs.csv has over 22,000 rows, so list answers are paged.
# Why paging: without a limit, GET /programs would send all 45,000 rows (over 10 MB) at once.
# The caller asks for a page with limit and offset instead. The maximum stops one request
# from asking for everything.
PROGRAMS_LIMIT, MATCH_LIMIT, MAX_LIMIT = 100, 50, 1000

app = FastAPI(title="GradMatch", description="Graduate programs, scholarships and deadlines.")


# The shape of the JSON a caller sends to POST /match. FastAPI checks the types for us (a GPA
# written as "high" gives a 422 error before our code runs); our own validate_profile then
# checks the values (a GPA of 5 is a number, but not a valid GPA).
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

# A tiny "are you alive?" check that a server or a test can call without loading any data.
@app.get("/health")
def health():
    return {"status": "ok"}


# List programs, optionally filtered by field, degree and state, one page at a time.
# Query(..., ge=1, le=1000) makes FastAPI answer 422 for a limit of 0 or 5000 without our code
# having to check it. The filters run first, then the page is cut, so paging works on the results.
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


# The main search: send a student profile, get matching programs (with cost, fit and funding)
# and scholarships. A bad profile gives 422 with the same messages the website shows.
# total_programs tells the caller how many matched, even when only the first `limit` are sent.
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


# Open deadlines, soonest first, each with its closed/urgent/soon/later label. `today` can be
# sent by the caller (handy for tests and demos); only when it is missing do we read the clock,
# here at the edge of the program, so the logic in deadlines.py stays free of date.today().
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

# Which data folder to read, read on every request so a test can switch it with an environment variable.
def data_dir() -> Path:
    return Path(os.environ.get("GRADMATCH_DATA_DIR", DEFAULT_DATA_DIR))


# One program as JSON: all its own fields plus what the search worked out for this student.
# asdict() turns None into null, so "not published" stays clear in the JSON too.
def program_result_json(result: ProgramResult) -> dict:
    """The program's fields plus what the search worked out for this student."""
    return {**asdict(result.program), "yearly_cost": result.yearly_cost,
            "total_cost": result.total_cost, "fit": result.fit, "funding": result.funding}


# One deadline as JSON. "kind" says if it is a program or a scholarship, because both are in one list.
def deadline_json(item: Program | Scholarship, today: date) -> dict:
    if isinstance(item, Program):
        kind, item_id, name = "program", item.program_id, f"{item.university} – {item.program_name}"
    else:
        kind, item_id, name = "scholarship", item.scholarship_id, item.name
    deadline = deadline_of(item)
    return {"kind": kind, "id": item_id, "name": name, "deadline": deadline,
            "status": deadline_status(deadline, today), "website": item.website}
