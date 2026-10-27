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
    assert ms1.source == "official-page"
    assert summary[0] == "1 row(s) applied, 6 value(s) changed"
    assert "MS1: tuition_in_state 15000 -> 16000" in summary
    assert "MS1: source (empty) -> official-page" in summary


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


# ---- The `source` column ----

def test_source_column_is_added_when_missing(tmp_path, data_dir):
    # The fixture programs.csv has no source column.
    apply_lookup(write_sheet(tmp_path, [sheet_row()]), data_dir)

    header = (data_dir / "programs.csv").read_text().splitlines()[0]
    assert header.endswith(",website,source")
    assert program(data_dir, "MS1").source == "official-page"
    assert program(data_dir, "PHD1").source == "estimate"     # blank = estimate


def test_existing_source_column_is_kept_and_updated(tmp_path, data_dir):
    lines = PROGRAMS.strip().split("\n")
    with_source = "\n".join([lines[0] + ",source", lines[1] + ",estimate",
                             lines[2] + ",ipeds"]) + "\n"
    (data_dir / "programs.csv").write_text(with_source)

    apply_lookup(write_sheet(tmp_path, [sheet_row()]), data_dir)

    header = (data_dir / "programs.csv").read_text().splitlines()[0]
    assert header.count("source") == 1
    assert program(data_dir, "MS1").source == "official-page"
    assert program(data_dir, "PHD1").source == "ipeds"


def test_unpublished_values_in_programs_csv_stay_blank_when_sheet_is_blank(tmp_path, data_dir):
    (data_dir / "programs.csv").write_text(PROGRAMS.replace(",0.10,40000,90,2026-12-15,",
                                                            ",,,90,,"))
    row = phd_row(tuition_in_state="31000", stipend="", phd_tuition_waiver="",
                  application_deadline="")

    summary = apply_lookup(write_sheet(tmp_path, [row]), data_dir)

    phd1 = program(data_dir, "PHD1")
    assert (phd1.acceptance_rate, phd1.stipend, phd1.application_deadline) == (None, None, None)
    assert phd1.tuition_in_state == 31000
    assert "PHD1: tuition_in_state 30000 -> 31000" in summary


def test_waiver_yes_fills_an_unpublished_stipend(tmp_path, data_dir):
    (data_dir / "programs.csv").write_text(PROGRAMS.replace(",0.10,40000,", ",0.10,,"))

    summary = apply_lookup(write_sheet(tmp_path, [phd_row(stipend="38000",
                                                          phd_tuition_waiver="yes")]), data_dir)

    assert program(data_dir, "PHD1").stipend == 38000
    assert "PHD1: stipend (empty) -> 38000" in summary


# ---- Tests added after mutation testing (see docs/mutation-testing.md) ----

def test_error_message_is_exact_for_a_row_with_several_problems(tmp_path, data_dir):
    row = sheet_row(official_url="http://x", application_deadline="soon", checked_on="today",
                    phd_tuition_waiver="maybe")

    with pytest.raises(SheetError) as error:
        apply_lookup(write_sheet(tmp_path, [row, sheet_row(program_id="NOPE")]), data_dir)

    assert str(error.value) == (
        "line 2 (MS1): official_url must start with https://; "
        "application_deadline must be a date in YYYY-MM-DD format; "
        "checked_on must be a date in YYYY-MM-DD format; "
        "phd_tuition_waiver must be yes, no or na\n"
        "line 3 (NOPE): unknown program_id 'NOPE'")


@pytest.mark.parametrize("row, message", [
    (dict(phd_tuition_waiver="no"), "phd_tuition_waiver must be na or blank for an MS program"),
    (dict(program_id="PHD1", degree="PhD", stipend="", phd_tuition_waiver="yes"),
     "phd_tuition_waiver is yes, so stipend must be greater than 0"),
    (dict(program_id="PHD1", degree="PhD", stipend="0.5", phd_tuition_waiver="no"),
     "phd_tuition_waiver is no, so stipend must be blank or 0"),
])
def test_waiver_messages_are_exact(tmp_path, data_dir, row, message):
    with pytest.raises(SheetError) as error:
        apply_lookup(write_sheet(tmp_path, [sheet_row(**row)]), data_dir)

    assert str(error.value).endswith("): " + message)


def test_program_missing_from_sources_message_is_exact(tmp_path, data_dir):
    (data_dir / "SOURCES.md").write_text(SOURCES.replace("| MS1 |", "| OTHER |"))

    with pytest.raises(SheetError) as error:
        apply_lookup(write_sheet(tmp_path, [sheet_row()]), data_dir)

    assert str(error.value) == "line 2 (MS1): program_id has no row in SOURCES.md"


def test_missing_sheet_columns_are_listed_with_comma_and_space(tmp_path, data_dir):
    columns = [c for c in SHEET_COLUMNS if c not in ("checked_by", "checked_on")]

    with pytest.raises(SheetError, match=r"missing column\(s\): checked_by, checked_on$"):
        apply_lookup(write_sheet(tmp_path, [sheet_row()], columns), data_dir)


def test_waiver_yes_with_stipend_just_above_zero_is_accepted(tmp_path, data_dir):
    # Boundary: "greater than 0", so 0.5 is allowed.
    row = sheet_row(program_id="PHD1", degree="PhD", stipend="0.5", phd_tuition_waiver="yes")

    apply_lookup(write_sheet(tmp_path, [row]), data_dir)

    assert program(data_dir, "PHD1").stipend == 0.5


def test_unchecked_row_before_a_checked_row_does_not_stop_the_sheet(tmp_path, data_dir):
    rows = [sheet_row(checked_by=""), sheet_row(program_id="PHD1", degree="PhD",
                                                stipend="45000", phd_tuition_waiver="yes")]

    summary = apply_lookup(write_sheet(tmp_path, rows), data_dir)

    assert summary[0].startswith("1 row(s) applied")
    assert program(data_dir, "PHD1").stipend == 45000


def test_changes_from_every_row_are_listed(tmp_path, data_dir):
    rows = [sheet_row(), sheet_row(program_id="PHD1", degree="PhD", stipend="45000",
                                   phd_tuition_waiver="yes")]

    summary = apply_lookup(write_sheet(tmp_path, rows), data_dir)

    assert summary[0] == "2 row(s) applied, 13 value(s) changed"   # 6 for MS1, 7 for PHD1
    assert "MS1: tuition_in_state 15000 -> 16000" in summary
    assert "PHD1: stipend 40000 -> 45000" in summary


def test_programs_csv_keeps_unix_line_endings(tmp_path, data_dir):
    apply_lookup(write_sheet(tmp_path, [sheet_row()]), data_dir)

    assert "\r" not in (data_dir / "programs.csv").read_bytes().decode("utf-8")


def test_line_break_inside_quoted_notes_and_cells_is_kept(tmp_path, data_dir):
    # Both files are read with newline="" as the csv module requires.
    (data_dir / "programs.csv").write_text(PROGRAMS.replace("MS in Computer Science,Computer",
                                                            '"MS in\r\nComputer Science",Computer'),
                                           newline="")
    apply_lookup(write_sheet(tmp_path, [sheet_row(notes="first\r\nsecond")]), data_dir)

    assert program(data_dir, "MS1").program_name == "MS in\r\nComputer Science"
    with open(data_dir / "SOURCES.md", newline="", encoding="utf-8") as file:
        assert "| first\r\nsecond |" in file.read()


def test_pipe_in_notes_is_replaced_so_the_table_stays_intact(tmp_path, data_dir):
    apply_lookup(write_sheet(tmp_path, [sheet_row(notes="fees | extra")]), data_dir)

    assert "| fees / extra |" in (data_dir / "SOURCES.md").read_text()


def test_command_prints_every_change_on_its_own_line(tmp_path, data_dir, capsys):
    main(["apply_lookup", str(write_sheet(tmp_path, [sheet_row()])), str(data_dir)])

    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "1 row(s) applied, 6 value(s) changed"
    assert "MS1: min_toefl 80 -> 84" in lines


def test_command_with_only_a_sheet_uses_the_data_folder(tmp_path, data_dir, monkeypatch, capsys):
    monkeypatch.chdir(data_dir.parent)          # data_dir is <tmp>/data
    sheet = write_sheet(tmp_path, [sheet_row()])

    assert main(["apply_lookup", str(sheet)]) == 0
    assert program(data_dir, "MS1").source == "official-page"


def test_command_usage_text_is_exact(capsys):
    main(["apply_lookup", "a", "b", "c"])

    assert capsys.readouterr().out == "usage: python -m gradmatch.apply_lookup <sheet.csv> [data_dir]\n"
