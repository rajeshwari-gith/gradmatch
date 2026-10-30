"""Integration tests: the modules working together, from CSV files to results.

Each test writes the small fixed dataset (tests/data_fixtures.py) to a temporary
folder, loads it with the real loaders and sends it through search, scholarship
matching, deadlines, presentation and exports. No Streamlit and no real data.

Techniques: equivalence partitioning on the path through the system (MS
search, funded PhD, scholarships, exports, broken data), and checks that two
modules agree with each other (for example the deadline row and the deadline
status).
"""
import csv
import io
import re
from datetime import date, datetime

import pytest

from conftest import make_profile
from data_fixtures import write_fixture_data
from gradmatch.data_loader import DataError, load_living_costs, load_programs, load_scholarships
from gradmatch.deadlines import CLOSED, URGENT, deadline_of, deadline_status, upcoming
from gradmatch.exports import to_csv, to_ics
from gradmatch.components import URGENT_BG
from gradmatch.fit import REACH
from gradmatch.screens import deadline_face, deadline_row_html, program_row_html, scholarship_amount_html, scholarship_info_html
from gradmatch.scholarships import eligible_scholarships
from gradmatch.search import search_programs

pytestmark = pytest.mark.integration

TODAY = date(2026, 10, 24)


@pytest.fixture
def data(tmp_path):
    folder = write_fixture_data(tmp_path)
    return (load_programs(folder / "programs.csv"),
            load_living_costs(folder / "living_costs.csv"),
            load_scholarships(folder / "scholarships.csv"))


def names(results):
    return [r.program.program_id for r in results]


# ---- Loading ----
# Why: if the files cannot be read, nothing else works, so this is checked first.

def test_the_loaders_read_every_row(data):
    programs, living, scholarships = data
    assert len(programs) == 6 and len(scholarships) == 5
    assert living == {"MI": 15000.0, "CA": 25000.0, "TX": 14000.0}


# ---- CSV -> search ----

def test_ms_search_on_loaded_data_finds_the_affordable_programs_cheapest_first(data):
    programs, living, _ = data
    results = search_programs(make_profile(annual_budget=40000), programs, living)
    assert names(results) == ["CHEAP", "MID"]
    assert [r.yearly_cost for r in results] == [25000, 35000]
    assert [r.fit for r in results] == ["Safety", "Match"]


def test_out_of_state_student_pays_out_of_state_tuition_from_the_loaded_data(data):
    programs, living, _ = data
    results = search_programs(make_profile(home_state="OH", annual_budget=100000), programs, living)
    cheap = next(r for r in results if r.program.program_id == "CHEAP")
    assert cheap.yearly_cost == 20000 + 15000          # out-of-state tuition + MI living cost


def test_funded_phd_from_loaded_data_costs_nothing(data):
    """Regression for D-001, checked across loader, cost, funding and search."""
    programs, living, _ = data
    profile = make_profile(degree_sought="PhD", gpa=3.9, annual_budget=0)
    results = search_programs(profile, programs, living)
    assert names(results) == ["PHD1"]
    assert results[0].yearly_cost == 0 and results[0].funding == "Fully Funded"


def test_missing_living_cost_stops_the_search_with_a_clear_message(data):
    programs, living, _ = data
    del living["CA"]
    with pytest.raises(ValueError, match="No living cost found for state CA"):
        search_programs(make_profile(annual_budget=100000), programs, living)


# ---- CSV -> scholarships -> deadlines ----

def test_scholarships_for_the_default_student_include_the_expired_one_until_deadlines_filter_it(data):
    _, _, scholarships = data
    eligible = eligible_scholarships(make_profile(), scholarships)
    assert [s.scholarship_id for s in eligible] == ["SCH3", "SCH5"]          # SCH3 is expired
    assert [s.scholarship_id for s in upcoming(eligible, TODAY)] == ["SCH5"]


def test_special_group_changes_which_scholarships_are_eligible(data):
    _, _, scholarships = data
    profile = make_profile(special=("first_gen",))
    eligible = eligible_scholarships(profile, scholarships)
    assert [s.scholarship_id for s in eligible] == ["SCH3", "SCH2", "SCH5"]  # sorted by deadline


def test_programs_and_scholarships_are_ordered_together_by_deadline(data):
    programs, living, scholarships = data
    results = search_programs(make_profile(annual_budget=100000), programs, living)
    mixed = [r.program for r in results] + eligible_scholarships(make_profile(), scholarships)
    ordered = upcoming(mixed, TODAY)
    assert [deadline_of(i) for i in ordered] == sorted(deadline_of(i) for i in ordered)
    assert all(deadline_status(deadline_of(i), TODAY) != CLOSED for i in ordered)


# ---- Search results -> rows: two modules must agree ----
# Why: the deadline face comes from screens.py but the deadline status comes from deadlines.py.

def test_deadline_rows_agree_with_the_deadline_status(data):
    programs, living, _ = data
    for result in search_programs(make_profile(annual_budget=100000), programs, living):
        day = result.program.application_deadline
        urgent = deadline_status(day, TODAY) == URGENT
        html = deadline_row_html(result.program, TODAY)
        assert (URGENT_BG in html) is urgent
        assert (deadline_face((day - TODAY).days) == REACH) is urgent


def test_a_loaded_program_becomes_a_row_with_its_cost(data):
    programs, living, _ = data
    cheap = search_programs(make_profile(), programs, living)[0]
    html = program_row_html(cheap, "MI", living["MI"])
    assert "Cheap State University" in html and 'gm-money" data-label="Est. yearly">$25,000<' in html
    assert 'href="https://example.edu/cheap"' in html


def test_loaded_scholarship_becomes_a_card(data):
    _, _, scholarships = data
    sch5 = next(s for s in scholarships if s.scholarship_id == "SCH5")
    html = scholarship_info_html(sch5, True) + scholarship_amount_html(sch5, TODAY)
    assert "Michigan Fee Waiver" in html and "Non-monetary" in html and "Residents of MI" in html


# ---- Exports ----

def test_csv_export_matches_the_search_results(data):
    programs, living, _ = data
    results = search_programs(make_profile(annual_budget=100000), programs, living)
    rows = list(csv.DictReader(io.StringIO(to_csv(results))))
    assert [r["university"] for r in rows] == [x.program.university for x in results]
    assert [float(r["yearly_cost"]) for r in rows] == [x.yearly_cost for x in results]
    assert [r["fit"] for r in rows] == [x.fit for x in results]
    assert rows[0]["deadline"] == results[0].program.application_deadline.isoformat()


def test_calendar_export_has_one_event_per_open_deadline_in_date_order(data):
    programs, living, scholarships = data
    results = search_programs(make_profile(annual_budget=100000), programs, living)
    items = upcoming([r.program for r in results] + eligible_scholarships(make_profile(), scholarships), TODAY)
    calendar = to_ics(items, datetime(2026, 10, 24, 0, 0))
    assert calendar.count("BEGIN:VEVENT") == len(items) == 3
    assert "\r\n" in calendar and "\n" not in calendar.replace("\r\n", "")
    dates = re.findall(r"DTSTART;VALUE=DATE:(\d{8})", calendar)
    assert dates == ["20261105", "20270110", "20270115"]
    assert "UID:program-CHEAP@gradmatch" in calendar and "UID:scholarship-SCH5@gradmatch" in calendar


# ---- Broken data stops early with a useful message ----
# Why: a typo in a CSV should give a clear error, not a strange crash in the middle of the page.

def test_bad_row_is_rejected_by_the_loader_before_any_search(tmp_path):
    folder = write_fixture_data(tmp_path)
    text = (folder / "programs.csv").read_text().replace(",0.60,0,80,", ",1.60,0,80,")   # acceptance rate 160%
    (folder / "programs.csv").write_text(text)
    with pytest.raises(DataError) as error:
        load_programs(folder / "programs.csv")
    assert "programs.csv" in str(error.value) and "line 2" in str(error.value)
