from datetime import date

from fastapi.testclient import TestClient

from gradmatch import api
from gradmatch.api import app
from helpers import make_program

client = TestClient(app)
MS_CS = {"degree": "MS", "field": "Computer Science", "gpa": 3.5, "home_state": "MI"}


def test_programs_within_budget_cheapest_first():
    response = client.get("/programs", params=MS_CS | {"budget": 35000})
    assert response.status_code == 200
    costs = [p["yearly_cost"] for p in response.json()]
    assert costs and costs == sorted(costs) and max(costs) <= 35000


def test_programs_in_chosen_states():
    found = client.get("/programs", params=MS_CS | {"budget": 100000, "states": ["OH", "IN"]}).json()
    assert found and {p["state"] for p in found} <= {"OH", "IN"}


def test_programs_bad_gre_is_400():
    response = client.get("/programs", params=MS_CS | {"budget": 40000, "gre": 400})
    assert response.status_code == 400


def test_programs_tiny_budget_returns_nothing():
    assert client.get("/programs", params=MS_CS | {"budget": 0}).json() == []


def test_programs_bad_gpa_is_400():
    response = client.get("/programs", params=MS_CS | {"gpa": 5, "budget": 40000})
    assert response.status_code == 400
    assert "GPA" in response.json()["detail"]


def test_programs_missing_value_is_422():
    assert client.get("/programs", params={"degree": "MS"}).status_code == 422


def test_scholarships_for_ms_student():
    params = {"degree": "MS", "field": "Computer Science", "gpa": 3.5}
    found = client.get("/scholarships", params=params).json()
    assert [s["name"] for s in found] == ["NSF Graduate Research Fellowship Program",
                                          "DoD SMART Scholarship", "GVSU Graduate Assistantship"]
    assert found[0]["open_to"] == "US citizens and permanent residents"



def test_scholarships_bad_gpa_is_400():
    params = {"degree": "MS", "field": "Computer Science", "gpa": 5}
    response = client.get("/scholarships", params=params)
    assert response.status_code == 400
    assert "GPA" in response.json()["detail"]

def test_deadlines_on_a_fixed_day():
    found = client.get("/deadlines", params={"today": "2026-11-20"}).json()
    assert found[0] == {"name": "DoD SMART Scholarship", "date": "2026-12-01",
                        "days_left": 11, "soon": True}
    assert all(d["date"] >= "2026-11-20" for d in found)


def test_program_deadlines_are_included(monkeypatch):
    monkeypatch.setattr(api, "PROGRAMS", [make_program(deadline=date(2026, 12, 15))])
    found = client.get("/deadlines", params={"today": "2026-12-10"}).json()
    assert found[0] == {"name": "Test University (MS in Computer Science)", "date": "2026-12-15",
                        "days_left": 5, "soon": True}


def test_deadlines_default_to_today():
    assert client.get("/deadlines").status_code == 200
