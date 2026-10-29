"""Unit tests for apply_scholarship_sheet.py.

Technique: equivalence partitioning on sheet rows (good row, blank cells,
each kind of bad value, unknown scholarship_id, unchecked row) and the
all-or-nothing rule. Every test works on tiny files in tmp_path, never on
the real data/ folder.
"""
# In plain words: these tests run the scholarship sheet tool on two made-up scholarships. They
# prove that checked values are copied, blank cells keep the old value, every mistake is
# reported with its line number, and that one bad row means nothing at all is written.

import csv

import pytest

from gradmatch.apply_scholarship_sheet import SHEET_COLUMNS, SheetError, apply_scholarship_sheet, main
from gradmatch.data_loader import load_scholarships

pytestmark = pytest.mark.unit

SCHOLARSHIPS = """scholarship_id,name,type,amount,degree_levels,fields,min_gpa,citizenship,states,special,deadline,website
S1,First Fellowship,fellowship,30000,MS;PhD,Any,0.0,US,Any,,2026-12-01,https://example.org/s1
S2,Second Scholarship,scholarship,5000,MS,Any,3.0,Any,Any,,2027-02-01,https://example.org/s2
"""

# A program table is there too, so the tests show that program rows are not counted or changed.
SOURCES = """# Program data sources

**Verified: 0 of 1 rows (programs) · Scholarships verified: 0 of 2**

| program_id | University | Program | Status | Source (official page) | Notes |
|---|---|---|---|---|---|
| S1 | Test University | MS | needs lookup |  |  |

## Scholarships (2)

| scholarship_id | Name | Status | Source (official page) | Notes |
|---|---|---|---|---|
| S1 | First Fellowship | needs lookup |  | estimates |
| S2 | Second Scholarship | needs lookup |  | estimates |
"""


@pytest.fixture
def data_dir(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    (folder / "scholarships.csv").write_text(SCHOLARSHIPS)
    (folder / "SOURCES.md").write_text(SOURCES)
    return folder


# A fully filled, valid sheet row for S1. A test changes one cell to make one mistake.
def sheet_row(**values) -> dict:
    row = dict(scholarship_id="S1", name="First Fellowship", official_url="https://example.org/s1/apply",
               amount="32000", deadline="2026-12-05", checked_by="Sai Nishith Jangili",
               checked_on="2026-10-29", notes="amount is per year")
    row.update(values)
    return row


def write_sheet(tmp_path, rows, columns=SHEET_COLUMNS):
    path = tmp_path / "sheet.csv"
    with open(path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def scholarship(data_dir, scholarship_id):
    return next(s for s in load_scholarships(data_dir / "scholarships.csv")
                if s.scholarship_id == scholarship_id)


def files(data_dir):
    return (data_dir / "scholarships.csv").read_text(), (data_dir / "SOURCES.md").read_text()


# ---- Valid class: a good row ----
# Why: the normal case first. Values are copied, the status and the count are updated.

def test_good_row_updates_scholarship_and_sources(tmp_path, data_dir):
    lines = apply_scholarship_sheet(write_sheet(tmp_path, [sheet_row()]), data_dir)

    s1 = scholarship(data_dir, "S1")
    assert (s1.amount, s1.deadline.isoformat(), s1.website) == (32000.0, "2026-12-05",
                                                               "https://example.org/s1/apply")
    sources = (data_dir / "SOURCES.md").read_text()
    assert ("| S1 | First Fellowship | verified by Sai Nishith Jangili on 2026-10-29 | "
            "https://example.org/s1/apply | amount is per year |") in sources
    assert "Scholarships verified: 1 of 2" in sources
    assert "Verified: 0 of 1 rows (programs)" in sources          # the program count is not touched
    assert "| S1 | Test University | MS | needs lookup |  |  |" in sources   # nor the program row
    assert lines == ["1 row(s) applied, 3 value(s) changed",
                     "S1: website https://example.org/s1 -> https://example.org/s1/apply",
                     "S1: amount 30000 -> 32000",
                     "S1: deadline 2026-12-01 -> 2026-12-05"]


def test_other_columns_and_rows_stay_the_same(tmp_path, data_dir):
    apply_scholarship_sheet(write_sheet(tmp_path, [sheet_row()]), data_dir)

    rows = (data_dir / "scholarships.csv").read_text().splitlines()
    assert rows[0] == SCHOLARSHIPS.splitlines()[0]
    assert rows[1] == ("S1,First Fellowship,fellowship,32000,MS;PhD,Any,0.0,US,Any,,2026-12-05,"
                       "https://example.org/s1/apply")
    assert rows[2] == SCHOLARSHIPS.splitlines()[2]


def test_blank_cells_keep_the_old_values(tmp_path, data_dir):
    sheet = write_sheet(tmp_path, [sheet_row(official_url="", amount="", deadline="", notes="")])

    lines = apply_scholarship_sheet(sheet, data_dir)

    s1 = scholarship(data_dir, "S1")
    assert (s1.amount, s1.website) == (30000.0, "https://example.org/s1")
    assert lines == ["1 row(s) applied, 0 value(s) changed"]
    # Still marked verified: the person checked the page; the source cell stays as it was.
    assert "| S1 | First Fellowship | verified by Sai Nishith Jangili on 2026-10-29 |  |  |" in (
        data_dir / "SOURCES.md").read_text()


def test_two_rows_are_both_applied_and_counted(tmp_path, data_dir):
    sheet = write_sheet(tmp_path, [sheet_row(), sheet_row(scholarship_id="S2", amount="0",
                                                          checked_by="Rajeshwari Galugu")])

    apply_scholarship_sheet(sheet, data_dir)

    assert scholarship(data_dir, "S2").amount == 0.0               # boundary: 0 is allowed
    assert "Scholarships verified: 2 of 2" in (data_dir / "SOURCES.md").read_text()


def test_pipe_in_notes_is_changed_so_the_table_stays_whole(tmp_path, data_dir):
    apply_scholarship_sheet(write_sheet(tmp_path, [sheet_row(notes="a | b")]), data_dir)

    assert "| a / b |" in (data_dir / "SOURCES.md").read_text()


def test_changes_from_every_row_are_listed_and_counted(tmp_path, data_dir):
    sheet = write_sheet(tmp_path, [sheet_row(official_url="", deadline=""),
                                   sheet_row(scholarship_id="S2", official_url="", amount="", deadline="2027-02-15")])

    lines = apply_scholarship_sheet(sheet, data_dir)

    assert lines == ["2 row(s) applied, 2 value(s) changed",
                     "S1: amount 30000 -> 32000",
                     "S2: deadline 2027-02-01 -> 2027-02-15"]


def test_written_file_uses_unix_line_endings(tmp_path, data_dir):
    apply_scholarship_sheet(write_sheet(tmp_path, [sheet_row()]), data_dir)

    assert b"\r\n" not in (data_dir / "scholarships.csv").read_bytes()

def test_line_break_inside_quoted_cells_is_kept(tmp_path, data_dir):
    # Both files are read with newline="" as the csv module asks, so a \r\n inside a quoted
    # cell stays exactly as it is instead of becoming \n.
    (data_dir / "scholarships.csv").write_text(
        SCHOLARSHIPS.replace("Second Scholarship", '"Second\r\nScholarship"'), newline="")
    sheet = write_sheet(tmp_path, [sheet_row(notes="first\r\nsecond")])

    apply_scholarship_sheet(sheet, data_dir)

    assert scholarship(data_dir, "S2").name == "Second\r\nScholarship"
    with open(data_dir / "SOURCES.md", newline="", encoding="utf-8") as file:
        assert "| first\r\nsecond |" in file.read()

# ---- Rows that are skipped ----
# Why: an unchecked row must never change data, and an empty sheet must not rewrite the files.

def test_unchecked_rows_are_skipped_even_if_bad(tmp_path, data_dir):
    before = files(data_dir)
    sheet = write_sheet(tmp_path, [sheet_row(checked_by="", amount="lots", scholarship_id="NOPE")])

    assert apply_scholarship_sheet(sheet, data_dir) == ["0 row(s) applied, 0 value(s) changed"]
    assert files(data_dir) == before


def test_an_unchecked_row_before_a_checked_row_does_not_stop_it(tmp_path, data_dir):
    sheet = write_sheet(tmp_path, [sheet_row(scholarship_id="S2", checked_by=""), sheet_row()])

    assert apply_scholarship_sheet(sheet, data_dir)[0] == "1 row(s) applied, 3 value(s) changed"
    assert scholarship(data_dir, "S1").amount == 32000.0

# ---- Invalid classes: one kind of mistake each ----
# Why: each mistake must be reported, and any mistake means nothing is written.

@pytest.mark.parametrize("change, message", [
    (dict(scholarship_id="NOPE"), "unknown scholarship_id 'NOPE'"),
    (dict(official_url="http://example.org"), "official_url must start with https://"),
    (dict(amount="-1"), "amount must be a non-negative number, got '-1'"),
    (dict(amount="about 5k"), "amount must be a non-negative number, got 'about 5k'"),
    (dict(deadline="12/05/2026"), "deadline must be a date in YYYY-MM-DD format"),
    (dict(checked_on=""), "checked_on must be a date in YYYY-MM-DD format"),
    (dict(checked_on="2026-02-30"), "checked_on must be a date in YYYY-MM-DD format"),
])
def test_bad_value_is_reported_and_nothing_is_written(tmp_path, data_dir, change, message):
    before = files(data_dir)

    with pytest.raises(SheetError) as error:
        apply_scholarship_sheet(write_sheet(tmp_path, [sheet_row(**change)]), data_dir)

    assert str(error.value) == f"line 2 ({change.get('scholarship_id', 'S1')}): {message}"
    assert files(data_dir) == before


def test_scholarship_missing_from_sources_is_refused(tmp_path, data_dir):
    (data_dir / "SOURCES.md").write_text(SOURCES.replace("| S2 | Second Scholarship", "| X2 | Second"))

    with pytest.raises(SheetError, match=r"line 2 \(S2\): scholarship_id has no row in SOURCES.md"):
        apply_scholarship_sheet(write_sheet(tmp_path, [sheet_row(scholarship_id="S2")]), data_dir)


def test_every_bad_row_is_listed_and_a_good_row_is_not_applied(tmp_path, data_dir):
    before = files(data_dir)
    sheet = write_sheet(tmp_path, [sheet_row(), sheet_row(amount="x"),
                                   sheet_row(scholarship_id="S2", deadline="soon", checked_on="today")])

    with pytest.raises(SheetError) as error:
        apply_scholarship_sheet(sheet, data_dir)

    assert str(error.value).split("\n") == [
        "line 3 (S1): amount must be a non-negative number, got 'x'",
        "line 4 (S2): deadline must be a date in YYYY-MM-DD format; "
        "checked_on must be a date in YYYY-MM-DD format",
    ]
    assert files(data_dir) == before                      # all or nothing


def test_missing_sheet_columns_are_reported(tmp_path, data_dir):
    sheet = write_sheet(tmp_path, [sheet_row()], columns=["scholarship_id", "amount"])

    with pytest.raises(SheetError, match="missing column\\(s\\): name, official_url, deadline"):
        apply_scholarship_sheet(sheet, data_dir)


def test_result_the_loader_refuses_is_not_written(tmp_path, data_dir, monkeypatch):
    # A scholarships.csv the loader already refuses (bad GPA in S2) stays as it is.
    (data_dir / "scholarships.csv").write_text(SCHOLARSHIPS.replace(",3.0,", ",9.0,"))
    before = files(data_dir)

    with pytest.raises(SheetError, match="the updated scholarships.csv would not load"):
        apply_scholarship_sheet(write_sheet(tmp_path, [sheet_row()]), data_dir)

    assert files(data_dir) == before
    assert not (data_dir / "scholarships.csv.new").exists()      # the temp file is removed


# ---- The command ----
# Why: exit codes let a person or a script see what happened: 0 applied, 1 bad sheet, 2 wrong use.

def test_command_applies_the_sheet(tmp_path, data_dir, capsys):
    assert main(["apply", str(write_sheet(tmp_path, [sheet_row()])), str(data_dir)]) == 0
    assert capsys.readouterr().out.startswith("1 row(s) applied, 3 value(s) changed\n")


def test_command_reports_a_bad_sheet(tmp_path, data_dir, capsys):
    assert main(["apply", str(write_sheet(tmp_path, [sheet_row(amount="x")])), str(data_dir)]) == 1
    assert capsys.readouterr().out.startswith("Nothing was written.\nline 2 (S1): amount")


def test_command_uses_the_data_folder_by_default(tmp_path, data_dir, monkeypatch, capsys):
    sheet = write_sheet(tmp_path, [sheet_row(checked_by="")])
    monkeypatch.chdir(data_dir.parent)

    assert main(["apply", str(sheet)]) == 0
    assert capsys.readouterr().out == "0 row(s) applied, 0 value(s) changed\n"


@pytest.mark.parametrize("argv", [["apply"], ["apply", "a", "b", "c"]])
def test_command_with_wrong_arguments_shows_usage(argv, capsys):
    assert main(argv) == 2
    assert capsys.readouterr().out.startswith("usage:")

