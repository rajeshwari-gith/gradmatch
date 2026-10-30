"""System tests for undergraduate (bachelor's) search through the real app.

Two bachelor's programs are added to the fixed data (living cost MI 15,000, CA 25,000):
  UGMI  Michigan Public College   BS CS  MI  tuition 8,000 in-state / 20,000 out  -> $23,000/yr, 4 yr total $92,000
  UGCA  California State College  BS CS  CA  tuition 9,000 / 25,000               -> $50,000/yr for a Michigan student (out-of-state + 25,000 living)
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app_pages import DEADLINES, PHD, SCHOLARSHIPS, chances, go, metrics, row_names, rows, yearly_costs

from data_fixtures import PROGRAM_HEADER, write_fixture_data

pytestmark = pytest.mark.system

APP = str(Path(__file__).resolve().parents[2] / "app" / "streamlit_app.py")
BS_ROWS = [
    "UGMI,Michigan Public College,BS in Computer Science,Computer Science,BS,MI,8000,20000,4,3.20,,0.55,0,,2026-12-01,https://example.edu/ugmi",
    "UGCA,California State College,BS in Computer Science,Computer Science,BS,CA,9000,25000,4,3.60,,0.30,0,,2027-01-05,https://example.edu/ugca",
]


@pytest.fixture
def bachelors_app(monkeypatch, tmp_path_factory):
    folder = write_fixture_data(tmp_path_factory.mktemp("bachelors"))
    (folder / "programs.csv").write_text(PROGRAM_HEADER + "\n".join(BS_ROWS) + "\n")
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(folder))
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    at.radio(key="degree").set_value("BS")
    at.number_input(key="budget").set_value(60000)
    at.button[0].click().run()
    assert not at.exception
    return at


def test_the_degree_choice_offers_a_bachelors_degree():
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert list(at.radio(key="degree").options) == ["Bachelor's (BS)", "Master's (MS)", "PhD"]
    assert at.radio(key="degree").value == "MS"


def test_a_bachelors_student_sees_only_bachelors_programs_cheapest_first(bachelors_app):
    assert row_names(bachelors_app) == ["Michigan Public College – BS in Computer Science",
                      "California State College – BS in Computer Science"]


def test_bachelors_costs_use_in_state_and_out_of_state_tuition(bachelors_app):
    assert yearly_costs(bachelors_app) == [23000, 50000]     # MI college in-state, CA college out-of-state
    assert metrics(bachelors_app)["Total for 4 years"] == "$92,000"
    bachelors_app.selectbox(key="cost_choice").set_value(1).run()
    assert metrics(bachelors_app)["Total for 4 years"] == "$200,000"


def test_bachelors_rows_show_a_fit_and_no_stipend(bachelors_app):
    assert "Unknown" not in chances(bachelors_app)         # these two rows publish a GPA, so the fit is known
    assert metrics(bachelors_app)["Stipend per year"] == "$0"   # no stipend, as for any bachelor's


def test_a_bachelors_student_can_still_open_the_other_screens(bachelors_app):
    for page in (PHD, SCHOLARSHIPS, DEADLINES):
        go(bachelors_app, page)


def test_only_the_first_60_matches_are_drawn_but_all_can_be_downloaded(monkeypatch, tmp_path_factory):
    folder = write_fixture_data(tmp_path_factory.mktemp("many"))
    many = [f"UG{i:03d},College {i:03d},BS in Computer Science,Computer Science,BS,MI,{8000 + i},20000,4,3.20,,0.55,0,,2026-12-01,https://example.edu/{i}"
            for i in range(75)]
    (folder / "programs.csv").write_text(PROGRAM_HEADER + "\n".join(many) + "\n")
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(folder))
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    at.radio(key="degree").set_value("BS")
    at.button[0].click().run()
    assert not at.exception
    assert len(rows(at)) == 60
    assert any("Showing the first 60 of 75 matches" in c.value for c in at.caption)
    assert list(at.radio(key="chance").options)[0] == "All 75"     # the filter still counts every match
    assert at.get("download_button")[0].label == "Download all results (.csv)"
