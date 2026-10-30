from fastapi.testclient import TestClient

from gradmatch.api import app

client = TestClient(app)
MS_CS = {"degree": "MS", "field": "Computer Science", "gpa": 3.5, "home_state": "MI"}


def test_programs_within_budget_cheapest_first():
    response = client.get("/programs", params=MS_CS | {"budget": 35000})
    assert response.status_code == 200
    costs = [p["yearly_cost"] for p in response.json()]
    assert costs and costs == sorted(costs) and max(costs) <= 35000


def test_programs_tiny_budget_returns_nothing():
    assert client.get("/programs", params=MS_CS | {"budget": 0}).json() == []


def test_programs_bad_gpa_is_400():
    response = client.get("/programs", params=MS_CS | {"gpa": 5, "budget": 40000})
    assert response.status_code == 400
    assert "GPA" in response.json()["detail"]


def test_programs_missing_value_is_422():
    assert client.get("/programs", params={"degree": "MS"}).status_code == 422


def test_scholarships_for_international_ms_student():
    params = {"degree": "MS", "field": "Computer Science", "gpa": 3.5, "citizenship": "International"}
    names = [s["name"] for s in client.get("/scholarships", params=params).json()]
    assert names == ["GVSU Graduate Assistantship"]


def test_deadlines_on_a_fixed_day():
    found = client.get("/deadlines", params={"today": "2026-11-20"}).json()
    assert found[0] == {"name": "DoD SMART Scholarship", "date": "2026-12-01",
                        "days_left": 11, "soon": True}
    assert all(d["date"] >= "2026-11-20" for d in found)


def test_deadlines_default_to_today():
    assert client.get("/deadlines").status_code == 200
