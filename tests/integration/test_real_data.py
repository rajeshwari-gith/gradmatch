"""Integration tests on the real data files in data/.

This is the one test file allowed to read the real CSVs. The unit tests use
small fixed data; these tests check that the real data loads, is consistent
across files, and works with the modules that use it. When a data row is
added or changed, these tests catch mistakes the loader cannot see on its
own (a state with no living cost, a duplicate id, a misspelled field).
"""
# In plain words: the other tests use tiny made-up data. These tests read the REAL files in
# data/ (45,000+ programs) and check that every row follows the rules: unique ids, a living
# cost for every state, https links, allowed fields and degrees, score ranges in order. They
# also run the search and the API on the real data, so a bad row added later is caught here.

import csv
import time
from collections import Counter
from datetime import date

import pytest
from fastapi.testclient import TestClient

from conftest import make_profile
from gradmatch.cost import yearly_cost
from gradmatch.deadlines import upcoming
from gradmatch.fit import UNKNOWN
from gradmatch.scholarships import eligible_scholarships, kind_of
from gradmatch.search import search_programs

pytestmark = pytest.mark.integration

from gradmatch.ipeds_import import CIP_FIELDS
from gradmatch.requirements import COLUMNS as REQUIREMENT_COLUMNS, load_requirements

# The hand-entered programs use four fields; rows imported from official data use the CIP_FIELDS names.
FIELDS = {"Electrical and Computer Engineering", "Business Analytics", *CIP_FIELDS.values()}
DEGREES = ("BS", "MS", "PhD")
TODAY = date(2026, 10, 24)


# The files are loaded once for the whole test run (see tests/integration/conftest.py), which
# keeps the tests fast. If a file has a bad row, every test in this file fails with the
# DataError message.

@pytest.fixture
def programs(real_programs):
    return real_programs


@pytest.fixture
def scholarships(real_scholarships):
    return real_scholarships


@pytest.fixture
def living_costs(real_living_costs):
    return real_living_costs


# ---- The files load ----
# Why: if any row breaks a loader rule, nothing else can work, so this is checked first.

def test_all_three_files_load_without_data_error(programs, scholarships, living_costs):
    assert programs
    assert scholarships
    assert living_costs


# ---- The files agree with each other ----
# Why: each file can be fine on its own but disagree with another (a program in a state with no living cost).

def test_every_program_state_has_a_living_cost(programs, living_costs):
    missing = sorted({p.state for p in programs if p.state not in living_costs})
    assert missing == []


def test_program_ids_are_unique(programs):
    counts = Counter(p.program_id for p in programs)       # Counter: fast on 22,000+ rows
    duplicates = sorted(i for i, n in counts.items() if n > 1)
    assert duplicates == []


def test_scholarship_ids_are_unique(scholarships):
    counts = Counter(s.scholarship_id for s in scholarships)
    duplicates = sorted(i for i, n in counts.items() if n > 1)
    assert duplicates == []


# ---- Every row follows the data rules ----
# Why: the loader checks one row at a time; these check rules across the whole file.

def test_every_website_uses_https(programs, scholarships):
    bad = [p.program_id for p in programs if not p.website.startswith("https://")]
    bad += [s.scholarship_id for s in scholarships if not s.website.startswith("https://")]
    assert bad == []


def test_every_field_is_an_allowed_value(programs):
    bad = [(p.program_id, p.field) for p in programs if p.field not in FIELDS]
    assert bad == []


def test_every_degree_is_bs_ms_or_phd(programs):
    bad = [(p.program_id, p.degree) for p in programs if p.degree not in DEGREES]
    assert bad == []


def test_every_source_is_an_allowed_value(programs):
    bad = [(p.program_id, p.source) for p in programs
           if p.source not in ("estimate", "official-page", "ipeds")]
    assert bad == []


def test_unpublished_values_are_none_not_zero_or_text(programs):
    # Blank cells must load as None; a value that is there must be a number or date.
    for program in programs:
        for value in (program.avg_gpa, program.acceptance_rate, program.stipend):
            assert value is None or isinstance(value, float), program.program_id
        assert program.application_deadline is None or isinstance(program.application_deadline, date)


def test_programs_without_deadline_are_left_out_of_upcoming(programs):
    undated = {p.program_id for p in programs if p.application_deadline is None}
    listed = {p.program_id for p in upcoming(programs, TODAY)}
    assert undated.isdisjoint(listed)


def test_at_least_one_ms_and_one_phd_program(programs):
    degrees = {p.degree for p in programs}
    assert degrees == {"BS", "MS", "PhD"}


def test_imported_rows_follow_the_official_data_rules(programs):
    imported = [p for p in programs if p.source == "ipeds"]
    assert len(imported) > 1000
    bad = [p.program_id for p in imported
           if p.application_deadline is not None or p.avg_gpa is not None
           or (p.degree == "BS") != (p.stipend == 0) and p.stipend is not None
           or (p.degree == "BS") != (p.duration_years == 4)]
    assert bad == []


def test_imported_program_ids_are_unique(programs):
    ids = [p.program_id for p in programs]
    assert len(ids) == len(set(ids))



def test_every_scholarship_type_has_a_kind(scholarships):
    # kind_of raises for a type it does not know, so a typo in the type column fails here.
    assert {kind_of(s) for s in scholarships} <= {"Scholarship", "Fellowship", "Assistantship"}

# ---- The modules run on the real data ----
# Why: real data has cases our small tests may not think of; the code must not crash on any of them.

@pytest.mark.parametrize("profile", [
    make_profile(),
    make_profile(degree_sought="PhD", gpa=3.9, citizenship="PR"),
    make_profile(field="Data Science", citizenship="International", home_state="CA",
                 special=("women_stem",)),
], ids=["ms-cs-us", "phd-cs-pr", "ms-ds-international"])
def test_eligible_scholarships_runs_on_real_data(scholarships, profile):
    result = eligible_scholarships(profile, scholarships)
    assert all(s in scholarships for s in result)


def test_upcoming_runs_on_real_programs_and_scholarships(programs, scholarships):
    result = upcoming(programs + scholarships, TODAY)
    assert len(result) <= len(programs) + len(scholarships)


# ---- Guard against defect D-001 coming back ----
# Why: D-001 was a real bug (funded PhDs showed a cost). This test keeps it from coming back unnoticed.

def test_fully_funded_phd_costs_nothing_in_or_out_of_state(programs, living_costs):
    # For every PhD whose stipend covers living costs, an in-state and an
    # out-of-state student must both pay $0 a year (tuition is waived).
    # A state with no living cost is reported by the living-cost test above.
    wrong = []
    for program in programs:
        if program.degree != "PhD" or program.state not in living_costs:
            continue
        living = living_costs[program.state]
        if program.stipend is None or program.stipend < living:
            continue                       # not published, or not fully funded
        out_of_state = "OH" if program.state != "OH" else "MI"
        for home_state in (program.state, out_of_state):
            cost = yearly_cost(program, home_state, living)
            if cost != 0:
                wrong.append((program.program_id, home_state, cost))
    assert wrong == []


# ---- Test scores and bachelor's rows (official data import) ----
# Why: a reversed SAT range or a bachelor's row with a stipend would give wrong labels and costs.

def test_sat_and_act_ranges_are_in_order(programs):
    bad = [p.program_id for p in programs
           if (p.sat_25 is not None and p.sat_75 is not None and p.sat_25 > p.sat_75)
           or (p.act_25 is not None and p.act_75 is not None and p.act_25 > p.act_75)]
    assert bad == []


def test_score_ranges_have_both_ends_or_neither(programs):
    bad = [p.program_id for p in programs
           if (p.sat_25 is None) != (p.sat_75 is None) or (p.act_25 is None) != (p.act_75 is None)]
    assert bad == []


def test_bachelors_rows_are_four_years_with_no_stipend(programs):
    bad = [(p.program_id, p.duration_years, p.stipend) for p in programs
           if p.degree == "BS" and (p.duration_years != 4 or p.stipend != 0)]
    assert bad == []


# ---- Essay and statement requirements ----
# Why: every requirement must belong to a real program, and the blank sheet must list real
# programs with exactly the columns of requirements.csv (plus two to help the reader).

def test_every_requirement_belongs_to_a_program(programs):
    ids = {p.program_id for p in programs}
    requirements = load_requirements("data/requirements.csv")
    assert [r.program_id for r in requirements if r.program_id not in ids] == []


def test_requirements_sheet_lists_real_programs_unchecked(programs):
    by_id = {p.program_id: p for p in programs}
    with open("data/requirements_sheet.csv", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    assert reader.fieldnames == ["program_id", "university", "program_name", *REQUIREMENT_COLUMNS[1:], "notes"]
    assert len(rows) == 10
    for row in rows:
        program = by_id[row["program_id"]]
        assert (row["university"], row["program_name"]) == (program.university, program.program_name)
        assert all(row[name] == "" for name in REQUIREMENT_COLUMNS[1:])     # nothing filled in yet



# ---- The fit rule on the real data ----
# Why: most imported programs publish no average GPA, so their chance is estimated from the
# acceptance rate (their own or their university's). A program with neither is left out of the
# search, so the default search must never show "Unknown".

def test_default_ms_computer_science_search_has_no_unknown_fits(programs, living_costs):
    profile = make_profile()                 # MS, Computer Science, GPA 3.5, MI, $40,000

    results = search_programs(profile, programs, living_costs)

    assert results                           # the search still finds programs
    assert [r.program.program_id for r in results if r.fit == UNKNOWN] == []
    # Programs with no published average GPA are still shown, with a chance from a rate.
    assert any(r.program.avg_gpa is None for r in results)

# ---- The API on the real data (45,000+ rows) ----
# Why: the API must stay fast with the full file; 5 seconds is a generous limit for a search.
# The test once failed when the computer was busy with other work, although the code was fine.
# So it times only the search (the CSV is already loaded, see conftest.py) and keeps the best
# of three tries: one slow try caused by a busy computer no longer fails the test, but a search
# that is always slow still does.

MATCH_SECONDS = 5.0      # generous: the search itself takes well under a second
TRIES = 3


@pytest.mark.parametrize("body", [
    dict(degree_sought="BS", gpa=3.6, field="Computer Science", home_state="MI",
         citizenship="US", annual_budget=40000, sat=1300, act=28),
    dict(degree_sought="MS", gpa=3.5, field="Computer Science", home_state="MI",
         citizenship="International", annual_budget=60000, toefl=95),
    dict(degree_sought="PhD", gpa=3.8, field="Computer Science", home_state="OH",
         citizenship="PR", annual_budget=0),
], ids=["bs", "ms", "phd"])
def test_match_on_real_data_is_fast_and_does_not_crash(real_data_api, body):
    client = TestClient(real_data_api)
    client.post("/match", json=body)          # warm-up: the first request sets up FastAPI

    seconds = []
    for _ in range(TRIES):
        start = time.perf_counter()
        response = client.post("/match", json=body)
        seconds.append(time.perf_counter() - start)

    assert response.status_code == 200
    answer = response.json()
    assert answer["total_programs"] > 0
    assert len(answer["programs"]) == min(answer["total_programs"], 50)
    assert all(p["degree"] == body["degree_sought"] for p in answer["programs"])
    assert min(seconds) < MATCH_SECONDS


def test_programs_on_real_data_is_paged(real_data_api):
    client = TestClient(real_data_api)

    first = client.get("/programs").json()
    last = client.get("/programs?limit=1000&offset=22000").json()

    assert len(first) == 100
    assert 0 < len(last) <= 1000
