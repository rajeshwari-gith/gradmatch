"""Integration tests on the real data files in data/.

This is the one test file allowed to read the real CSVs. The unit tests use
small fixed data; these tests check that the real data loads, is consistent
across files, and works with the modules that use it. When a data row is
added or changed, these tests catch mistakes the loader cannot see on its
own (a state with no living cost, a duplicate id, a misspelled field).
"""
import time
from collections import Counter
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import make_profile
from gradmatch.api import app
from gradmatch.cost import yearly_cost
from gradmatch.data_loader import load_living_costs, load_programs, load_scholarships
from gradmatch.deadlines import upcoming
from gradmatch.scholarships import eligible_scholarships

pytestmark = pytest.mark.integration

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
from gradmatch.ipeds_import import CIP_FIELDS

# The hand-entered programs use four fields; rows imported from official data use the CIP_FIELDS names.
FIELDS = {"Electrical and Computer Engineering", "Business Analytics", *CIP_FIELDS.values()}
DEGREES = ("BS", "MS", "PhD")
TODAY = date(2026, 10, 24)


# Loading once per module keeps the tests fast. If a file has a bad row,
# every test in this file fails with the DataError message.

@pytest.fixture(scope="module")
def programs():
    return load_programs(DATA_DIR / "programs.csv")


@pytest.fixture(scope="module")
def scholarships():
    return load_scholarships(DATA_DIR / "scholarships.csv")


@pytest.fixture(scope="module")
def living_costs():
    return load_living_costs(DATA_DIR / "living_costs.csv")


# ---- The files load ----

def test_all_three_files_load_without_data_error(programs, scholarships, living_costs):
    assert programs
    assert scholarships
    assert living_costs


# ---- The files agree with each other ----

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


# ---- The modules run on the real data ----

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


# ---- The API on the real data (22,000+ rows) ----

MATCH_SECONDS = 5.0      # generous: about 0.5 s on a laptop, mostly loading the CSV


@pytest.mark.parametrize("body", [
    dict(degree_sought="BS", gpa=3.6, field="Computer Science", home_state="MI",
         citizenship="US", annual_budget=40000, sat=1300, act=28),
    dict(degree_sought="MS", gpa=3.5, field="Computer Science", home_state="MI",
         citizenship="International", annual_budget=60000, toefl=95),
    dict(degree_sought="PhD", gpa=3.8, field="Computer Science", home_state="OH",
         citizenship="PR", annual_budget=0),
], ids=["bs", "ms", "phd"])
def test_match_on_real_data_is_fast_and_does_not_crash(monkeypatch, body):
    monkeypatch.delenv("GRADMATCH_DATA_DIR", raising=False)      # use the real data/ folder
    client = TestClient(app)

    start = time.perf_counter()
    response = client.post("/match", json=body)
    seconds = time.perf_counter() - start

    assert response.status_code == 200
    answer = response.json()
    assert answer["total_programs"] > 0
    assert len(answer["programs"]) == min(answer["total_programs"], 50)
    assert all(p["degree"] == body["degree_sought"] for p in answer["programs"])
    assert seconds < MATCH_SECONDS


def test_programs_on_real_data_is_paged(monkeypatch):
    monkeypatch.delenv("GRADMATCH_DATA_DIR", raising=False)
    client = TestClient(app)

    first = client.get("/programs").json()
    last = client.get("/programs?limit=1000&offset=22000").json()

    assert len(first) == 100
    assert 0 < len(last) <= 1000
