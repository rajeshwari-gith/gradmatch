"""GradMatch REST API (FastAPI).

This file only turns HTTP requests into calls to the existing modules and
their results into JSON. It has no business rules of its own.

Run it with:  PYTHONPATH=src uvicorn gradmatch.api:app --reload

The data folder is GRADMATCH_DATA_DIR if it is set, otherwise data/.

The starred items (/starred) are kept in this server's memory only: they are
shared by everyone using the server and are lost when it restarts.
"""
# In plain words: the same search as the website, but for other programs to call over HTTP
# and get JSON back (for example a phone app). This file has no rules of its own: it only
# reads the request, calls the same functions the website uses, and turns the answer into
# JSON. Keeping the rules in one place means the website and the API can never disagree.

import os
import threading
from dataclasses import asdict
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from gradmatch.data_loader import load_living_costs, load_programs, load_scholarships
from gradmatch.deadlines import (GLANCE_DAYS, URGENT_MAX_DAYS, deadline_of, deadline_status, glance_counts,
                                 upcoming)
from gradmatch.models import Program, Scholarship, StudentProfile
from gradmatch.scholarships import eligible_scholarships
from gradmatch.search import ProgramResult, search_programs
from gradmatch.starred import is_star_key
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

# The starred keys, in memory. The lock makes "read the set, change it, store it" one step, so two
# requests at the same moment cannot lose each other's star (uvicorn runs requests in threads).
_starred: frozenset = frozenset()
_starred_lock = threading.Lock()


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


# The shape of the GET /deadlines answer. FastAPI shows it on the /docs page, so a reader can see
# that the answer is an object with the window, the four counts and the list, not a plain list.
class GlanceOut(BaseModel):
    within_window: int
    within_90: int
    later: int
    passed: int


class DeadlineOut(BaseModel):
    kind: str                     # "program" or "scholarship"
    id: str
    name: str
    deadline: date
    status: str                   # "urgent", "soon" or "later" (closed ones are left out)
    website: str


class DeadlinesOut(BaseModel):
    urgent_days: int
    glance: GlanceOut
    deadlines: list[DeadlineOut]


# The JSON body of POST /starred, e.g. {"key": "program:GVSU-MS-CS"}.
class StarIn(BaseModel):
    key: str


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
    `total_programs` says how many matched in all. Each program's `fit` is Safety, Match
    or Reach. Without a published average GPA it is estimated from the acceptance rate
    (the program's own, or its university's); a program with neither is left out.
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


# Open deadlines, soonest first, each with its closed/urgent/soon/later label, plus the four
# "at a glance" counts. `today` can be sent by the caller (handy for tests and demos); only when
# it is missing do we read the clock, here at the edge of the program, so the logic in
# deadlines.py stays free of date.today(). `urgent_days` is the student's warning window.
@app.get("/deadlines", response_model=DeadlinesOut)
def deadlines(today: date | None = None,
              urgent_days: int = Query(URGENT_MAX_DAYS, ge=0, le=GLANCE_DAYS)):
    """Open program and scholarship deadlines, soonest first, and the glance counts.

    `today` is a query parameter (YYYY-MM-DD); FastAPI answers 422 if it is not a date.
    Only when it is left out does the API use the server's date: this is the edge of
    the program, like the UI, so the logic modules still never call date.today().
    `urgent_days` (0-90, default 14) sets the warning window for the status and the counts.
    """
    today = today or date.today()
    folder = data_dir()
    items = load_programs(folder / "programs.csv") + load_scholarships(folder / "scholarships.csv")
    return {"urgent_days": urgent_days,
            "glance": glance_counts(items, today, urgent_days),
            "deadlines": [deadline_json(item, today, urgent_days) for item in upcoming(items, today)]}


# The starred keys, sorted so the answer is the same every time.
@app.get("/starred")
def get_starred():
    return sorted(_starred)


# Star one item. Starring it again changes nothing (so a repeated request is harmless).
# The key must look like "program:<id>", "scholarship:<id>" or "deadline:<name>"; the API does
# not check that the id exists, because a custom deadline only exists on the student's screen.
@app.post("/starred")
def add_starred(body: StarIn):
    global _starred
    _check_star_key(body.key)
    with _starred_lock:
        _starred = _starred | {body.key}
        return sorted(_starred)


# Take the star away from one item: DELETE /starred?key=program:GVSU-MS-CS. Removing a key that
# is not starred is not an error, for the same reason as above.
@app.delete("/starred")
def remove_starred(key: str):
    global _starred
    _check_star_key(key)
    with _starred_lock:
        _starred = _starred - {key}
        return sorted(_starred)


def _check_star_key(key: str):
    if not is_star_key(key):
        raise HTTPException(status_code=422,
                            detail=["key must be program:<id>, scholarship:<id> or deadline:<name>"])


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
def deadline_json(item: Program | Scholarship, today: date, urgent_days: int = URGENT_MAX_DAYS) -> dict:
    if isinstance(item, Program):
        kind, item_id, name = "program", item.program_id, f"{item.university} – {item.program_name}"
    else:
        kind, item_id, name = "scholarship", item.scholarship_id, item.name
    deadline = deadline_of(item)
    return {"kind": kind, "id": item_id, "name": name, "deadline": deadline,
            "status": deadline_status(deadline, today, urgent_days), "website": item.website}
