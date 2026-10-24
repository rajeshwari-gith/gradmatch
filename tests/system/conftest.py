"""Fixed data for the system tests.

The app is pointed at a tiny data folder built here and at a fixed "today",
so the tests never depend on the real CSV files or on the day they run.

Fixed "today": 2026-10-24. A student from MI with a $40,000 budget sees:
  CHEAP  MI  MS CS   $25,000/yr  Safety  (GPA diff +0.20)   deadline 12 days away -> urgent
  MID    MI  MS CS   $35,000/yr  Match                      deadline Jan 15, 2027
  PRICEY CA  MS CS   $65,000/yr  Reach                       deadline already closed
  DS1    TX  MS Data Science (out-of-state: $38,000/yr)
  PHD1   MI  PhD CS  tuition waived, stipend covers living costs -> $0, Fully Funded
  PHD2   CA  PhD CS  tuition waived, stipend 10,000 of 25,000 living cost -> $15,000, Partially Funded
"""
import pytest

TODAY = "2026-10-24"

PROGRAM_HEADER = ("program_id,university,program_name,field,degree,state,tuition_in_state,"
                  "tuition_out_state,duration_years,avg_gpa,avg_gre,acceptance_rate,stipend,"
                  "min_toefl,application_deadline,website\n")
PROGRAM_ROWS = [
    "CHEAP,Cheap State University,MS in Computer Science,Computer Science,MS,MI,10000,20000,2,3.30,,0.60,0,80,2026-11-05,https://example.edu/cheap",
    "MID,Middle University,MS in Computer Science,Computer Science,MS,MI,20000,30000,2,3.50,310,0.40,0,85,2027-01-15,https://example.edu/mid",
    "PRICEY,Pricey Tech,MS in Computer Science,Computer Science,MS,CA,30000,40000,2,3.90,325,0.15,0,100,2026-10-01,https://example.edu/pricey",
    "DS1,Texas Data Institute,MS in Data Science,Data Science,MS,TX,12000,24000,2,3.40,,0.50,0,80,2027-02-01,https://example.edu/ds",
    "PHD1,Funded University,PhD in Computer Science,Computer Science,PhD,MI,30000,30000,5,3.80,320,0.10,30000,90,2026-12-15,https://example.edu/phd1",
    "PHD2,Partly Funded Institute,PhD in Computer Science,Computer Science,PhD,CA,50000,50000,5,3.70,318,0.12,10000,90,2027-01-05,https://example.edu/phd2",
]
LIVING_COSTS = "state,annual_living_cost\nMI,15000\nCA,25000\nTX,14000\n"
SCHOLARSHIP_HEADER = ("scholarship_id,name,type,amount,degree_levels,fields,min_gpa,citizenship,"
                      "states,special,deadline,website\n")


@pytest.fixture(scope="session")
def data_dir(tmp_path_factory):
    folder = tmp_path_factory.mktemp("system_test_data")
    (folder / "programs.csv").write_text(PROGRAM_HEADER + "\n".join(PROGRAM_ROWS) + "\n")
    (folder / "living_costs.csv").write_text(LIVING_COSTS)
    (folder / "scholarships.csv").write_text(SCHOLARSHIP_HEADER)
    return folder


@pytest.fixture(autouse=True)
def fixed_app_environment(monkeypatch, data_dir):
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(data_dir))
    monkeypatch.setenv("GRADMATCH_TODAY", TODAY)
