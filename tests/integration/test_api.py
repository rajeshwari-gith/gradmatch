"""Integration tests for the REST API (api.py), using FastAPI's TestClient.

The API runs on the small fixed data from tests/data_fixtures.py (see the
tables there), never on the real data/ folder. These tests check status
codes, the JSON shape, validation errors and ordering, and that the API
gives the same answers as the modules it calls.
"""
# In plain words: these tests call the REST API the way another program would, through FastAPI's
# TestClient, but on a tiny made-up data folder. They check the status codes (200, 404, 422),
# the shape of the JSON, the order of the results and the paging limits.

import pytest
from fastapi.testclient import TestClient

from data_fixtures import TODAY, write_fixture_data
from gradmatch import api
from gradmatch.api import app

pytestmark = pytest.mark.integration


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(write_fixture_data(tmp_path)))
    return TestClient(app)


# A valid student profile as JSON. A test changes one field to make it invalid or different.
def profile(**changes) -> dict:
    """The default fixture student: MS in CS, GPA 3.5, U.S. citizen from MI, $40,000 budget."""
    body = dict(degree_sought="MS", gpa=3.5, field="Computer Science", home_state="MI",
                citizenship="US", annual_budget=40000)
    body.update(changes)
    return body


# ---- GET /health ----
# Why: the simplest call; if this fails, the app itself did not start.

def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---- GET /programs ----
# Why: filters must match exactly, keep the file order, and an empty result is [] (not an error).

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
# Why: the main feature. Same order and numbers as the website, and a bad profile gives 422 with clear messages.

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
# Why: soonest first, closed ones left out, and a bad `today` (like 2027-02-29) gives 422.

def test_deadlines_are_open_items_soonest_first_with_status(client):
    response = client.get(f"/deadlines?today={TODAY}")

    assert response.status_code == 200
    items = response.json()["deadlines"]
    assert [i["id"] for i in items] == ["SCH2", "CHEAP", "SCH1", "PHD1", "PHD2", "SCH5", "MID",
                                        "DS1", "SCH4"]
    assert items[0] == {"kind": "scholarship", "id": "SCH2", "name": "First-Gen Grant",
                        "deadline": "2026-11-01", "status": "urgent",
                        "website": "https://example.org/sch2"}
    assert items[1]["kind"] == "program"
    assert items[1]["name"] == "Cheap State University – MS in Computer Science"


def test_deadlines_leave_out_closed_items(client):
    ids = [i["id"] for i in client.get(f"/deadlines?today={TODAY}").json()["deadlines"]]

    assert "PRICEY" not in ids and "SCH3" not in ids


def test_deadlines_after_every_deadline_gives_empty_list(client):
    response = client.get("/deadlines?today=2030-01-01")

    assert response.status_code == 200
    assert response.json()["deadlines"] == []
    assert response.json()["glance"] == {"within_window": 0, "within_90": 0, "later": 0, "passed": 11}


@pytest.mark.parametrize("bad", ["tomorrow", "2026-13-01", "2027-02-29"])
def test_deadlines_bad_today_gives_422(client, bad):
    assert client.get(f"/deadlines?today={bad}").status_code == 422


def test_deadlines_without_today_uses_the_server_date(client):
    response = client.get("/deadlines")

    assert response.status_code == 200
    assert isinstance(response.json()["deadlines"], list)



# ---- GET /deadlines: the warning window and the glance counts ----
# Why (boundary values on urgent_days): the default, a smaller and a larger window, the edges
# 0 and 90, and one past each edge (422). The fixture deadlines are 8, 12, 42, 52, 73, 78, 83,
# 100 and 128 days away, and two have passed.

def test_deadlines_glance_counts_with_the_default_window(client):
    answer = client.get(f"/deadlines?today={TODAY}").json()

    assert answer["urgent_days"] == 14
    assert answer["glance"] == {"within_window": 2, "within_90": 7, "later": 2, "passed": 2}


@pytest.mark.parametrize("urgent_days, within_window, sch2, sch1", [
    (0, 0, "soon", "later"), (7, 0, "soon", "later"), (8, 1, "urgent", "later"),
    (45, 3, "urgent", "urgent"), (90, 7, "urgent", "urgent"),
])
def test_deadlines_window_changes_status_and_count(client, urgent_days, within_window, sch2, sch1):
    answer = client.get(f"/deadlines?today={TODAY}&urgent_days={urgent_days}").json()
    status = {i["id"]: i["status"] for i in answer["deadlines"]}

    assert answer["glance"] == {"within_window": within_window, "within_90": 7, "later": 2, "passed": 2}
    assert (status["SCH2"], status["SCH1"]) == (sch2, sch1)


@pytest.mark.parametrize("bad", ["-1", "91", "two", "7.5"])
def test_deadlines_bad_urgent_days_gives_422(client, bad):
    assert client.get(f"/deadlines?today={TODAY}&urgent_days={bad}").status_code == 422



@pytest.mark.parametrize("bad, limit", [("91", "less than or equal to 90"), ("-1", "greater than or equal to 0")])
def test_deadlines_urgent_days_out_of_range_names_the_parameter(client, bad, limit):
    response = client.get(f"/deadlines?today={TODAY}&urgent_days={bad}")

    assert response.status_code == 422
    [error] = response.json()["detail"]
    assert error["loc"] == ["query", "urgent_days"]
    assert limit in error["msg"]


def test_api_docs_show_deadlines_as_an_object(client):
    # The /docs page is built from this description; it must say the answer is an object.
    spec = client.get("/openapi.json").json()
    answer = spec["paths"]["/deadlines"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    model = spec["components"]["schemas"][answer["$ref"].split("/")[-1]]

    assert model["type"] == "object"
    assert set(model["properties"]) == {"urgent_days", "glance", "deadlines"}
    assert set(spec["components"]["schemas"]["GlanceOut"]["properties"]) == {
        "within_window", "within_90", "later", "passed"}

# ---- /starred ----
# Why: stars are added, listed sorted, removed, and a repeated add or remove is harmless.
# A bad key gives 422. The stars live in the server's memory, so each test starts empty.

@pytest.fixture
def starred_client(client, monkeypatch):
    monkeypatch.setattr(api, "_starred", frozenset())
    return client


def test_starred_starts_empty(starred_client):
    assert starred_client.get("/starred").json() == []


def test_star_add_list_and_remove(starred_client):
    assert starred_client.post("/starred", json={"key": "scholarship:SCH1"}).json() == ["scholarship:SCH1"]
    assert starred_client.post("/starred", json={"key": "program:CHEAP"}).json() == [
        "program:CHEAP", "scholarship:SCH1"]
    assert starred_client.post("/starred", json={"key": "program:CHEAP"}).json() == [
        "program:CHEAP", "scholarship:SCH1"]                       # adding again changes nothing
    assert starred_client.get("/starred").json() == ["program:CHEAP", "scholarship:SCH1"]

    assert starred_client.delete("/starred?key=program:CHEAP").json() == ["scholarship:SCH1"]
    assert starred_client.delete("/starred?key=program:CHEAP").json() == ["scholarship:SCH1"]
    assert starred_client.get("/starred").json() == ["scholarship:SCH1"]


def test_star_a_custom_deadline_by_name(starred_client):
    response = starred_client.post("/starred", json={"key": "deadline:Rec letters"})

    assert response.json() == ["deadline:Rec letters"]


@pytest.mark.parametrize("key", ["", "program:", "progam:CHEAP", "CHEAP"])
def test_star_bad_key_gives_422_and_changes_nothing(starred_client, key):
    post = starred_client.post("/starred", json={"key": key})
    delete = starred_client.delete("/starred", params={"key": key})

    assert (post.status_code, delete.status_code) == (422, 422)
    assert post.json()["detail"] == ["key must be program:<id>, scholarship:<id> or deadline:<name>"]
    assert starred_client.get("/starred").json() == []


@pytest.mark.parametrize("call", ["post_without_body", "delete_without_key"])
def test_star_missing_key_gives_422(starred_client, call):
    if call == "post_without_body":
        response = starred_client.post("/starred", json={})
    else:
        response = starred_client.delete("/starred")
    assert response.status_code == 422

# ---- Unknown route ----
# Why: a wrong address must give 404, not crash.

def test_unknown_route_gives_404(client):
    assert client.get("/nothing-here").status_code == 404


# ---- Values that are not published (CONTRIBUTING.md) ----
# Why: missing values must reach the caller as null, never as 0 or as a made-up number.
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
    ids = [i["id"] for i in client_with_blanks.get(f"/deadlines?today={TODAY}").json()["deadlines"]]

    assert "IPEDS1" not in ids
    assert ids[:2] == ["SCH2", "CHEAP"]      # the rest is unchanged


def test_match_program_items_include_source(client_with_blanks):
    programs = client_with_blanks.post("/match", json=profile()).json()["programs"]

    assert [(p["program_id"], p["source"]) for p in programs] == [("CHEAP", "estimate"),
                                                                    ("MID", "estimate")]


def test_match_leaves_out_a_program_with_no_chance_at_all(client_with_blanks):
    body = profile(field="Business Analytics", annual_budget=100000)
    assert client_with_blanks.post("/match", json=body).json()["programs"] == []


def test_match_estimates_the_chance_from_the_universitys_rate(tmp_path, monkeypatch):
    folder = write_fixture_data(tmp_path)
    lines = (folder / "programs.csv").read_text().strip().split("\n")
    college = ("UG1,Imported University,BS in Business,Business,BS,OH,9000,20000,4,,,0.70,0,,,"
               "https://example.edu/ug1,ipeds")
    lines = [lines[0] + ",source"] + [line + "," for line in lines[1:]] + [UNPUBLISHED_ROW, college]
    (folder / "programs.csv").write_text("\n".join(lines) + "\n")
    (folder / "living_costs.csv").write_text((folder / "living_costs.csv").read_text() + "OH,15000\n")
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(folder))
    body = profile(field="Business Analytics", annual_budget=100000)
    [program] = TestClient(app).post("/match", json=body).json()["programs"]

    assert program["program_id"] == "IPEDS1"
    assert (program["fit"], program["funding"]) == ("Safety", "Funding unknown")   # 70% accepted
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


# ---- Paging: limit and offset (programs.csv has over 22,000 rows) ----
# Boundary values: limit 0 / 1 / 1000 / 1001, offset -1 / 0 / last / past the end.
# Why: with 45,000 rows the API must hand out pages; the edges of each allowed range are tested.

BULK_ROWS = 150


@pytest.fixture
def big_client(tmp_path, monkeypatch):
    """The fixture data plus 150 cheap MS CS programs in MI, so the defaults matter."""
    folder = write_fixture_data(tmp_path)
    bulk = [f"BULK{i:03},Bulk University {i:03},MS in Computer Science,Computer Science,MS,MI,"
            f"1000,2000,2,3.40,,0.40,0,80,2027-01-15,https://example.edu/bulk{i}"
            for i in range(BULK_ROWS)]
    with open(folder / "programs.csv", "a") as file:
        file.write("\n".join(bulk) + "\n")
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(folder))
    return TestClient(app)


def ids(response):
    return [p["program_id"] for p in response.json()]


@pytest.mark.parametrize("query, expected", [
    ("?limit=1", ["CHEAP"]),
    ("?limit=2", ["CHEAP", "MID"]),
    ("?limit=2&offset=2", ["PRICEY", "DS1"]),
    ("?offset=5", ["PHD2"]),                     # last row
    ("?offset=6", []),                           # just past the end
    ("?offset=1000", []),
    ("?degree=MS&limit=1&offset=1", ["MID"]),    # paging applies after the filters
])
def test_programs_limit_and_offset(client, query, expected):
    response = client.get("/programs" + query)

    assert response.status_code == 200
    assert ids(response) == expected


def test_programs_default_limit_is_100(big_client):
    result = ids(big_client.get("/programs"))

    assert len(result) == 100
    assert result[:2] == ["CHEAP", "MID"]


def test_programs_maximum_limit_returns_everything_up_to_1000(big_client):
    assert len(ids(big_client.get("/programs?limit=1000"))) == 6 + BULK_ROWS


def test_programs_pages_do_not_overlap(big_client):
    first = ids(big_client.get("/programs?limit=100"))
    second = ids(big_client.get("/programs?limit=100&offset=100"))

    assert len(second) == 6 + BULK_ROWS - 100
    assert set(first).isdisjoint(second)


@pytest.mark.parametrize("query", ["?limit=0", "?limit=1001", "?limit=-1", "?limit=many",
                                   "?offset=-1", "?offset=first"])
def test_programs_bad_limit_or_offset_gives_422(client, query):
    assert client.get("/programs" + query).status_code == 422


def test_match_reports_total_programs(client):
    answer = client.post("/match", json=profile()).json()

    assert answer["total_programs"] == 2
    assert len(answer["programs"]) == 2


def test_match_limit_keeps_the_best_results(client):
    answer = client.post("/match?limit=1", json=profile()).json()

    assert answer["total_programs"] == 2
    assert [p["program_id"] for p in answer["programs"]] == ["CHEAP"]   # cheapest first


def test_match_default_limit_is_50(big_client):
    answer = big_client.post("/match", json=profile()).json()

    assert answer["total_programs"] == BULK_ROWS + 2      # 150 bulk + CHEAP + MID
    assert len(answer["programs"]) == 50


def test_match_maximum_limit_is_1000(big_client):
    answer = big_client.post("/match?limit=1000", json=profile()).json()

    assert len(answer["programs"]) == answer["total_programs"] == BULK_ROWS + 2


def test_match_with_no_programs_has_total_zero(client):
    answer = client.post("/match", json=profile(annual_budget=0)).json()

    assert (answer["total_programs"], answer["programs"]) == (0, [])


@pytest.mark.parametrize("limit", ["0", "1001", "-5", "all"])
def test_match_bad_limit_gives_422(client, limit):
    assert client.post(f"/match?limit={limit}", json=profile()).status_code == 422
