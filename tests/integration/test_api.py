"""Integration tests for the REST API (api.py), using FastAPI's TestClient.

The API runs on the small fixed data from tests/data_fixtures.py (see the
tables there), never on the real data/ folder. These tests check status
codes, the JSON shape, validation errors and ordering, and that the API
gives the same answers as the modules it calls.
"""
import pytest
from fastapi.testclient import TestClient

from data_fixtures import TODAY, write_fixture_data
from gradmatch.api import app

pytestmark = pytest.mark.integration


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(write_fixture_data(tmp_path)))
    return TestClient(app)


def profile(**changes) -> dict:
    """The default fixture student: MS in CS, GPA 3.5, U.S. citizen from MI, $40,000 budget."""
    body = dict(degree_sought="MS", gpa=3.5, field="Computer Science", home_state="MI",
                citizenship="US", annual_budget=40000)
    body.update(changes)
    return body


# ---- GET /health ----

def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---- GET /programs ----

def test_programs_returns_all_programs_in_file_order(client):
    response = client.get("/programs")

    assert response.status_code == 200
    assert [p["program_id"] for p in response.json()] == ["CHEAP", "MID", "PRICEY", "DS1", "PHD1", "PHD2"]


def test_programs_json_shape(client):
    cheap = client.get("/programs").json()[0]

    assert cheap["university"] == "Cheap State University"
    assert cheap["application_deadline"] == "2026-11-05"      # dates as YYYY-MM-DD
    assert cheap["avg_gre"] is None                           # empty cell -> null
    assert cheap["tuition_in_state"] == 10000


@pytest.mark.parametrize("query, expected", [
    ("?field=Data Science", ["DS1"]),
    ("?degree=PhD", ["PHD1", "PHD2"]),
    ("?state=CA", ["PRICEY", "PHD2"]),
    ("?degree=MS&state=MI", ["CHEAP", "MID"]),
    ("?field=Computer Science&degree=PhD&state=MI", ["PHD1"]),
])
def test_programs_filters(client, query, expected):
    assert [p["program_id"] for p in client.get("/programs" + query).json()] == expected


def test_programs_filter_with_no_match_gives_empty_list(client):
    response = client.get("/programs?state=AK")

    assert response.status_code == 200
    assert response.json() == []


# ---- POST /match ----

def test_match_returns_programs_with_cost_fit_and_funding(client):
    response = client.post("/match", json=profile())

    assert response.status_code == 200
    programs = response.json()["programs"]
    # Same order as search_programs: MS results cheapest first; PRICEY is over budget.
    assert [p["program_id"] for p in programs] == ["CHEAP", "MID"]
    assert programs[0]["yearly_cost"] == 25000
    assert programs[0]["total_cost"] == 50000
    assert programs[0]["fit"] == "Safety"
    assert programs[0]["funding"] == "Self-Funded"


def test_match_returns_eligible_scholarships_sorted_by_deadline(client):
    scholarships = client.post("/match", json=profile()).json()["scholarships"]

    # SCH3 is closed but still eligible (the UI hides closed ones); SCH5 is open.
    assert [s["scholarship_id"] for s in scholarships] == ["SCH3", "SCH5"]
    assert scholarships[1]["degree_levels"] == ["MS"]


def test_match_phd_profile_ranks_best_funded_first(client):
    programs = client.post("/match", json=profile(degree_sought="PhD", annual_budget=20000)).json()["programs"]

    assert [(p["program_id"], p["yearly_cost"], p["funding"]) for p in programs] == [
        ("PHD1", 0, "Fully Funded"), ("PHD2", 15000, "Partially Funded")]


def test_match_optional_fields_are_used(client):
    body = profile(special=["first_gen"], preferred_states=["MI"], toefl=100, gre=320)

    response = client.post("/match", json=body)

    assert response.status_code == 200
    assert "SCH2" in [s["scholarship_id"] for s in response.json()["scholarships"]]


def test_match_with_no_programs_gives_empty_list(client):
    response = client.post("/match", json=profile(annual_budget=0))

    assert response.status_code == 200
    assert response.json()["programs"] == []


def test_match_invalid_profile_gives_422_with_validation_messages(client):
    response = client.post("/match", json=profile(gpa=4.5, home_state="XX"))

    assert response.status_code == 422
    assert "GPA must be between 0.0 and 4.0." in response.json()["detail"]
    assert "Home state must be a valid U.S. state code." in response.json()["detail"]


@pytest.mark.parametrize("body", [
    {"gpa": 3.5},                                  # required fields missing
    profile(gpa="high"),                           # wrong type
])
def test_match_malformed_body_gives_422(client, body):
    assert client.post("/match", json=body).status_code == 422


# ---- GET /deadlines ----

def test_deadlines_are_open_items_soonest_first_with_status(client):
    response = client.get(f"/deadlines?today={TODAY}")

    assert response.status_code == 200
    items = response.json()
    assert [i["id"] for i in items] == ["SCH2", "CHEAP", "SCH1", "PHD1", "PHD2", "SCH5", "MID",
                                        "DS1", "SCH4"]
    assert items[0] == {"kind": "scholarship", "id": "SCH2", "name": "First-Gen Grant",
                        "deadline": "2026-11-01", "status": "urgent",
                        "website": "https://example.org/sch2"}
    assert items[1]["kind"] == "program"
    assert items[1]["name"] == "Cheap State University – MS in Computer Science"


def test_deadlines_leave_out_closed_items(client):
    ids = [i["id"] for i in client.get(f"/deadlines?today={TODAY}").json()]

    assert "PRICEY" not in ids and "SCH3" not in ids


def test_deadlines_after_every_deadline_gives_empty_list(client):
    response = client.get("/deadlines?today=2030-01-01")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("bad", ["tomorrow", "2026-13-01", "2027-02-29"])
def test_deadlines_bad_today_gives_422(client, bad):
    assert client.get(f"/deadlines?today={bad}").status_code == 422


def test_deadlines_without_today_uses_the_server_date(client):
    response = client.get("/deadlines")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---- Unknown route ----

def test_unknown_route_gives_404(client):
    assert client.get("/nothing-here").status_code == 404


# ---- Values that are not published (CONTRIBUTING.md) ----
# A second data folder: the fixture data plus one imported-style row with
# blanks, and a `source` column. The extra row is in a field no other test
# searches, so POST /match never has to cost it.

UNPUBLISHED_ROW = ("IPEDS1,Imported University,MS in Business Analytics,Business Analytics,MS,OH,"
                   "11000,22000,2,,,,,,,https://example.edu/ipeds1,ipeds")


@pytest.fixture
def client_with_blanks(tmp_path, monkeypatch):
    folder = write_fixture_data(tmp_path)
    lines = (folder / "programs.csv").read_text().strip().split("\n")
    lines = [lines[0] + ",source"] + [line + "," for line in lines[1:]] + [UNPUBLISHED_ROW]
    (folder / "programs.csv").write_text("\n".join(lines) + "\n")
    (folder / "living_costs.csv").write_text((folder / "living_costs.csv").read_text() + "OH,15000\n")
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(folder))
    return TestClient(app)


def test_programs_include_source(client):
    sources = {p["source"] for p in client.get("/programs").json()}

    assert sources == {"estimate"}          # no source column -> estimate


def test_programs_unpublished_values_are_null(client_with_blanks):
    [row] = client_with_blanks.get("/programs?field=Business Analytics").json()

    assert row["source"] == "ipeds"
    assert row["tuition_in_state"] == 11000
    for name in ("avg_gpa", "avg_gre", "acceptance_rate", "stipend", "min_toefl",
                 "application_deadline"):
        assert row[name] is None, name


def test_programs_blank_source_cell_is_estimate(client_with_blanks):
    sources = {p["program_id"]: p["source"] for p in client_with_blanks.get("/programs").json()}

    assert sources["CHEAP"] == "estimate"
    assert sources["IPEDS1"] == "ipeds"


def test_deadlines_leave_out_unpublished_deadline(client_with_blanks):
    ids = [i["id"] for i in client_with_blanks.get(f"/deadlines?today={TODAY}").json()]

    assert "IPEDS1" not in ids
    assert ids[:2] == ["SCH2", "CHEAP"]      # the rest is unchanged


def test_match_program_items_include_source(client_with_blanks):
    programs = client_with_blanks.post("/match", json=profile()).json()["programs"]

    assert [(p["program_id"], p["source"]) for p in programs] == [("CHEAP", "estimate"),
                                                                    ("MID", "estimate")]


def test_match_gives_unknown_fit_and_funding_for_unpublished_values(client_with_blanks):
    body = profile(field="Business Analytics", annual_budget=100000)
    [program] = client_with_blanks.post("/match", json=body).json()["programs"]

    assert program["program_id"] == "IPEDS1"
    assert (program["fit"], program["funding"]) == ("Unknown", "Funding unknown")
    assert program["yearly_cost"] == 22000 + 15000    # Michigan student at an Ohio school: out-of-state tuition + OH living cost; unknown stipend counts as 0


def test_match_uses_sat_and_act_from_the_request(tmp_path, monkeypatch):
    folder = write_fixture_data(tmp_path)
    lines = (folder / "programs.csv").read_text().strip().split("\n")
    lines = [lines[0] + ",sat_25,sat_75"] + [line + "," for line in lines[1:]]
    lines[1] = lines[1] + "1000,1200"            # the CHEAP college
    (folder / "programs.csv").write_text("\n".join(lines) + "\n")
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(folder))
    client = TestClient(app)
    fits = {p["program_id"]: p["fit"] for p in client.post("/match", json=profile(sat=1250)).json()["programs"]}
    assert fits["CHEAP"] == "Safety"
    assert client.post("/match", json=profile(sat=100)).status_code == 422
