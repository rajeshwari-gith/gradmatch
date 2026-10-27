"""Unit tests for apply_lookup.py.

Technique: equivalence partitioning on sheet rows (good row, blank cells,
each kind of bad value, unknown program_id, unchecked row) and a decision
table for the PhD tuition-waiver rule. Every test works on copies of tiny
data files in tmp_path, never on the real data/ folder.
"""
import csv

import pytest

from gradmatch.apply_lookup import SHEET_COLUMNS, SheetError, apply_lookup, main
from gradmatch.data_loader import load_programs

pytestmark = pytest.mark.unit

PROGRAMS = """program_id,university,program_name,field,degree,state,tuition_in_state,tuition_out_state,duration_years,avg_gpa,avg_gre,acceptance_rate,stipend,min_toefl,application_deadline,website
MS1,Test University,MS in Computer Science,Computer Science,MS,MI,15000,30000,2,3.40,,0.40,0,80,2027-01-15,https://example.edu/dept
PHD1,Test University,PhD in Computer Science,Computer Science,PhD,MI,30000,60000,5,3.80,,0.10,40000,90,2026-12-15,https://example.edu/dept
"""

SOURCES = """# Program data sources

**Verified: 0 of 2 rows (programs) · Scholarships verified: 0 of 13**

| program_id | University | Program | Status | Source (official page) | Notes |
|---|---|---|---|---|---|
| MS1 | Test University | MS in Computer Science | needs lookup |  | website is the department home page |
| PHD1 | Test University | PhD in Computer Science | needs lookup |  | website is the department home page |
"""


@pytest.fixture
def data_dir(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    (folder / "programs.csv").write_text(PROGRAMS)
    (folder / "SOURCES.md").write_text(SOURCES)
    return folder


def sheet_row(**values) -> dict:
    """A checked sheet row for MS1 with every value filled in."""
    row = dict(program_id="MS1", university="Test University",
               program_name="MS in Computer Science", degree="MS",
               official_url="https://example.edu/ms-cs", tuition_in_state="16000",
               tuition_out_state="32000", application_deadline="2027-01-10", stipend="",
               phd_tuition_waiver="na", min_toefl="84", checked_by="Rajeshwari Galugu",
               checked_on="2026-10-26", notes="")
    row.update(values)
    return row


def write_sheet(tmp_path, rows, columns=SHEET_COLUMNS):
    path = tmp_path / "sheet.csv"
    with open(path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def program(data_dir, program_id):
    return next(p for p in load_programs(data_dir / "programs.csv") if p.program_id == program_id)


def files(data_dir):
    return (data_dir / "programs.csv").read_text(), (data_dir / "SOURCES.md").read_text()


# ---- Valid class: a good row ----

def test_good_row_updates_program_and_sources(tmp_path, data_dir):
    sheet = write_sheet(tmp_path, [sheet_row(notes="Fees not included")])

    summary = apply_lookup(sheet, data_dir)

    ms1 = program(data_dir, "MS1")
    assert ms1.website == "https://example.edu/ms-cs"
    assert (ms1.tuition_in_state, ms1.tuition_out_state) == (16000, 32000)
    assert str(ms1.application_deadline) == "2027-01-10"
    assert ms1.min_toefl == 84
    sources = (data_dir / "SOURCES.md").read_text()
    assert ("| MS1 | Test University | MS in Computer Science | verified by Rajeshwari Galugu "
            "on 2026-10-26 | https://example.edu/ms-cs | Fees not included |") in sources
    assert summary[0] == "1 row(s) applied, 5 value(s) changed"
    assert "MS1: tuition_in_state 15000 -> 16000" in summary


def test_status_line_counts_verified_rows(tmp_path, data_dir):
    apply_lookup(write_sheet(tmp_path, [sheet_row()]), data_dir)
    assert "**Verified: 1 of 2 rows (programs) · Scholarships verified: 0 of 13**" in files(data_dir)[1]

    phd = sheet_row(program_id="PHD1", degree="PhD", stipend="45000", phd_tuition_waiver="yes")
    apply_lookup(write_sheet(tmp_path, [phd]), data_dir)
    assert "**Verified: 2 of 2 rows (programs)" in files(data_dir)[1]


def test_blank_cells_keep_the_old_values(tmp_path, data_dir):
    row = sheet_row(official_url="", tuition_out_state="", application_deadline="", min_toefl="")

    apply_lookup(write_sheet(tmp_path, [row]), data_dir)

    ms1 = program(data_dir, "MS1")
    assert ms1.website == "https://example.edu/dept"
    assert ms1.tuition_out_state == 30000
    assert str(ms1.application_deadline) == "2027-01-15"
    assert ms1.min_toefl == 80
    assert ms1.tuition_in_state == 16000          # the one filled value changed


def test_row_without_checked_by_is_skipped(tmp_path, data_dir):
    before = files(data_dir)

    summary = apply_lookup(write_sheet(tmp_path, [sheet_row(checked_by="")]), data_dir)

    assert summary == ["0 row(s) applied, 0 value(s) changed"]
    assert files(data_dir) == before


def test_other_columns_and_rows_are_left_alone(tmp_path, data_dir):
    apply_lookup(write_sheet(tmp_path, [sheet_row()]), data_dir)

    phd1 = program(data_dir, "PHD1")
    assert (phd1.tuition_in_state, phd1.stipend, phd1.avg_gpa) == (30000, 40000, 3.80)
    assert program(data_dir, "MS1").avg_gpa == 3.40


# ---- Invalid classes: each kind of bad value ----

@pytest.mark.parametrize("changes, message", [
    ({"program_id": "NOPE"}, "unknown program_id 'NOPE'"),
    ({"official_url": "http://example.edu"}, "official_url must start with https://"),
    ({"tuition_in_state": "-1"}, "tuition_in_state must be a non-negative number"),
    ({"tuition_out_state": "free"}, "tuition_out_state must be a non-negative number"),
    ({"application_deadline": "01/15/2027"}, "application_deadline must be a date"),
    ({"application_deadline": "2027-02-29"}, "application_deadline must be a date"),
    ({"stipend": "lots"}, "stipend must be a non-negative number"),
    ({"phd_tuition_waiver": "maybe"}, "phd_tuition_waiver must be yes, no or na"),
    ({"min_toefl": "121"}, "min_toefl must be a whole number from 0 to 120"),
    ({"min_toefl": "80.5"}, "min_toefl must be a whole number from 0 to 120"),
    ({"checked_on": "yesterday"}, "checked_on must be a date"),
    ({"phd_tuition_waiver": "yes"}, "must be na or blank for an MS program"),
])
def test_bad_value_is_rejected_with_line_number(tmp_path, data_dir, changes, message):
    sheet = write_sheet(tmp_path, [sheet_row(**changes)])

    with pytest.raises(SheetError, match=message) as error:
        apply_lookup(sheet, data_dir)
    assert "line 2" in str(error.value)


def test_toefl_boundaries_are_accepted(tmp_path, data_dir):
    apply_lookup(write_sheet(tmp_path, [sheet_row(min_toefl="0")]), data_dir)
    assert program(data_dir, "MS1").min_toefl == 0
    apply_lookup(write_sheet(tmp_path, [sheet_row(min_toefl="120")]), data_dir)
    assert program(data_dir, "MS1").min_toefl == 120


def test_nothing_is_written_when_one_row_is_bad(tmp_path, data_dir):
    before = files(data_dir)
    good = sheet_row()
    bad = sheet_row(program_id="PHD1", degree="PhD", tuition_in_state="-5")

    with pytest.raises(SheetError, match="line 3 \\(PHD1\\)"):
        apply_lookup(write_sheet(tmp_path, [good, bad]), data_dir)
    assert files(data_dir) == before


def test_every_bad_row_is_listed(tmp_path, data_dir):
    rows = [sheet_row(min_toefl="999"), sheet_row(program_id="NOPE")]

    with pytest.raises(SheetError) as error:
        apply_lookup(write_sheet(tmp_path, rows), data_dir)
    assert "line 2 (MS1)" in str(error.value)
    assert "line 3 (NOPE)" in str(error.value)


def test_missing_sheet_column_is_rejected(tmp_path, data_dir):
    columns = [c for c in SHEET_COLUMNS if c != "checked_on"]

    with pytest.raises(SheetError, match="missing column.*checked_on"):
        apply_lookup(write_sheet(tmp_path, [sheet_row()], columns), data_dir)


def test_program_missing_from_sources_is_rejected(tmp_path, data_dir):
    (data_dir / "SOURCES.md").write_text(SOURCES.replace("| PHD1 |", "| OTHER |"))
    row = sheet_row(program_id="PHD1", degree="PhD", stipend="45000", phd_tuition_waiver="yes")

    with pytest.raises(SheetError, match="no row in SOURCES.md"):
        apply_lookup(write_sheet(tmp_path, [row]), data_dir)


# ---- Decision table: PhD tuition waiver ----
# waiver | stipend in sheet | result
# yes    | > 0              | stipend copied
# yes    | blank or 0       | error (a waiver needs a stipend)
# no     | blank or 0       | stipend set to 0
# no     | > 0              | error (would silently drop the value)
# blank  | blank            | stipend kept

def phd_row(**changes):
    return sheet_row(program_id="PHD1", degree="PhD", program_name="PhD in Computer Science",
                     **changes)


def test_waiver_yes_with_stipend_copies_it(tmp_path, data_dir):
    apply_lookup(write_sheet(tmp_path, [phd_row(stipend="45000", phd_tuition_waiver="yes")]), data_dir)
    assert program(data_dir, "PHD1").stipend == 45000


@pytest.mark.parametrize("stipend", ["", "0"])
def test_waiver_yes_without_stipend_is_rejected(tmp_path, data_dir, stipend):
    with pytest.raises(SheetError, match="stipend must be greater than 0"):
        apply_lookup(write_sheet(tmp_path, [phd_row(stipend=stipend, phd_tuition_waiver="yes")]),
                     data_dir)


@pytest.mark.parametrize("stipend", ["", "0"])
def test_waiver_no_sets_stipend_to_zero(tmp_path, data_dir, stipend):
    summary = apply_lookup(write_sheet(tmp_path, [phd_row(stipend=stipend, phd_tuition_waiver="no")]),
                           data_dir)
    assert program(data_dir, "PHD1").stipend == 0
    assert "PHD1: stipend 40000 -> 0" in summary


def test_waiver_no_with_stipend_is_rejected(tmp_path, data_dir):
    with pytest.raises(SheetError, match="stipend must be blank or 0"):
        apply_lookup(write_sheet(tmp_path, [phd_row(stipend="30000", phd_tuition_waiver="no")]),
                     data_dir)


def test_waiver_blank_keeps_the_stipend(tmp_path, data_dir):
    apply_lookup(write_sheet(tmp_path, [phd_row(stipend="", phd_tuition_waiver="")]), data_dir)
    assert program(data_dir, "PHD1").stipend == 40000


# ---- The command ----

def test_command_prints_summary(tmp_path, data_dir, capsys):
    code = main(["apply_lookup", str(write_sheet(tmp_path, [sheet_row()])), str(data_dir)])

    assert code == 0
    assert "1 row(s) applied" in capsys.readouterr().out


def test_command_reports_bad_sheet_and_writes_nothing(tmp_path, data_dir, capsys):
    before = files(data_dir)

    code = main(["apply_lookup", str(write_sheet(tmp_path, [sheet_row(min_toefl="999")])),
                 str(data_dir)])

    assert code == 1
    assert "Nothing was written." in capsys.readouterr().out
    assert files(data_dir) == before


def test_command_without_arguments_shows_usage(capsys):
    assert main(["apply_lookup"]) == 2
    assert "usage" in capsys.readouterr().out


def test_existing_bad_row_stops_the_update_and_writes_nothing(tmp_path, data_dir):
    # Another row in programs.csv is already broken (degree MBA). The updated
    # file is checked with the loader before anything is written.
    (data_dir / "programs.csv").write_text(PROGRAMS.replace(",PhD,MI,", ",MBA,MI,"))
    before = files(data_dir)

    with pytest.raises(SheetError, match="would not load.*degree must be MS or PhD"):
        apply_lookup(write_sheet(tmp_path, [sheet_row()]), data_dir)
    assert files(data_dir) == before
    assert not (data_dir / "programs.csv.new").exists()
