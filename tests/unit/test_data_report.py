"""Unit tests for data_report.py."""
# In plain words: these tests build tiny data folders on purpose (a few rows, some with problems)
# and check every number of the report, the printed text and the exit code. They never read the
# real data, so the expected numbers stay the same when the real data changes.
# Techniques: equivalence classes (no problem / duplicate ids / non-https links, SOURCES.md with
# and without the counts) and boundary values (no imported rows at all, so no division by zero).

import csv
from collections import Counter

import pytest

from gradmatch.data_report import build_report, format_report, has_problems, main

pytestmark = pytest.mark.unit

PROGRAM_COLUMNS = ["program_id", "field", "degree", "acceptance_rate", "stipend", "website", "source"]


def write(path, columns, rows):
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def program(program_id, source="ipeds", **changes):
    row = dict(program_id=program_id, field="Computer Science", degree="BS", acceptance_rate="0.5",
               stipend="0", website=f"https://example.edu/{program_id}", source=source)
    row.update(changes)
    return row


@pytest.fixture
def data_dir(tmp_path):
    """Three imported rows (one with blanks), one hand-entered row with a blank source, one checked row."""
    write(tmp_path / "programs.csv", PROGRAM_COLUMNS, [
        program("I1"),
        program("I2", acceptance_rate="", degree="MS"),
        program("I3", acceptance_rate="", stipend="", field="Data Science", degree="PhD"),
        program("HAND1", source=""),
        program("CHECKED1", source="official-page", degree="MS"),
    ])
    write(tmp_path / "scholarships.csv", ["scholarship_id", "website"],
          [{"scholarship_id": "S1", "website": "https://example.org/s1"}])
    (tmp_path / "SOURCES.md").write_text(
        "# Program data sources\n\n**Verified: 2 of 5 rows (programs) · Scholarships verified: 1 of 13**\n")
    return tmp_path


# ---- The numbers ----
# Why: the report is only useful if every count is right, so each count is checked on its own.

def test_counts_by_source_degree_and_field(data_dir):
    report = build_report(data_dir)

    assert (report["programs"], report["scholarships"], report["imported"]) == (5, 1, 3)
    assert report["by_source"] == {"ipeds": 3, "estimate": 1, "official-page": 1}   # blank = estimate
    assert report["by_degree"] == {"BS": 2, "MS": 2, "PhD": 1}
    assert report["by_field"] == {"Computer Science": 4, "Data Science": 1}


def test_blank_cells_are_counted_only_in_imported_rows(data_dir):
    blanks = build_report(data_dir)["blank_in_imported"]

    assert blanks["acceptance_rate"] == 2      # I2 and I3
    assert blanks["stipend"] == 1              # I3
    assert blanks["website"] == 0              # every column is listed, also with 0 blanks
    assert list(blanks) == PROGRAM_COLUMNS


def test_a_file_without_a_source_column_counts_every_row_as_an_estimate(tmp_path):
    write(tmp_path / "programs.csv", ["program_id", "website"],
          [{"program_id": "P1", "website": "https://a.edu"}])
    write(tmp_path / "scholarships.csv", ["scholarship_id", "website"], [])

    report = build_report(tmp_path)

    assert report["by_source"] == {"estimate": 1}
    assert (report["imported"], report["blank_in_imported"]) == (0, {})


def test_verified_counts_are_read_from_sources(data_dir):
    assert build_report(data_dir)["verified"] == {"programs": (2, 5), "scholarships": (1, 13)}


@pytest.mark.parametrize("sources_text", [None, "# Program data sources\n\nNo counts here.\n"])
def test_missing_sources_file_or_line_gives_none(data_dir, sources_text):
    if sources_text is None:
        (data_dir / "SOURCES.md").unlink()
    else:
        (data_dir / "SOURCES.md").write_text(sources_text)

    assert build_report(data_dir)["verified"] == {"programs": None, "scholarships": None}


# ---- Problems: duplicate ids and non-https links ----
# Why (equivalence classes): one test per kind of problem, plus the clean case.

def test_clean_data_has_no_problems(data_dir):
    report = build_report(data_dir)

    assert (report["duplicate_program_ids"], report["duplicate_scholarship_ids"],
            report["non_https"]) == ([], [], [])
    assert has_problems(report) is False


def test_duplicate_program_ids_are_listed_once_and_sorted(data_dir):
    write(data_dir / "programs.csv", PROGRAM_COLUMNS,
          [program("B"), program("A"), program("B"), program("A"), program("B"), program("C")])

    report = build_report(data_dir)

    assert report["duplicate_program_ids"] == ["A", "B"]
    assert has_problems(report) is True


def test_duplicate_scholarship_ids_are_a_problem(data_dir):
    write(data_dir / "scholarships.csv", ["scholarship_id", "website"],
          [{"scholarship_id": "S1", "website": "https://a.org"}] * 2)

    report = build_report(data_dir)

    assert report["duplicate_scholarship_ids"] == ["S1"]
    assert has_problems(report) is True


def test_non_https_websites_from_both_files_are_listed(data_dir):
    write(data_dir / "programs.csv", PROGRAM_COLUMNS,
          [program("P1", website="http://a.edu"), program("P2", website=""), program("P3")])
    write(data_dir / "scholarships.csv", ["scholarship_id", "website"],
          [{"scholarship_id": "S9", "website": "www.b.org"}])

    report = build_report(data_dir)

    assert report["non_https"] == ["P1", "P2", "S9"]
    assert has_problems(report) is True


# ---- The printed text ----
# Why: people read this text, so the key lines must be there and the numbers must be formatted.

def test_printed_report(data_dir):
    text = format_report(build_report(data_dir))

    assert text.startswith("Programs: 5    Scholarships: 1")
    assert "Programs by field (2 fields):" in text
    assert "Blank cells in the 3 imported (ipeds) rows (blank = not published):" in text
    assert "  acceptance_rate              2  67%" in text
    assert "Duplicate program ids: none" in text
    assert "Websites not starting with https://: none" in text
    assert "  programs:     2 of 5 hand-entered rows" in text
    assert "  scholarships: 1 of 13" in text


def test_printed_report_with_problems_blank_field_and_no_counts(tmp_path):
    write(tmp_path / "programs.csv", PROGRAM_COLUMNS,
          [program("P1", source="", field="", website="http://a.edu"), program("P1", source="")])
    write(tmp_path / "scholarships.csv", ["scholarship_id", "website"], [])

    text = format_report(build_report(tmp_path))

    assert "  (blank)" in text                                 # a blank field is shown, not hidden
    assert "Blank cells in the 0 imported (ipeds) rows" in text   # boundary: no imported rows
    assert "Duplicate program ids: P1" in text
    assert "Websites not starting with https://: P1" in text
    assert "  programs:     not found hand-entered rows" in text


def test_percent_with_no_imported_rows_is_a_dash():
    # Boundary: 0 imported rows must not divide by zero.
    report = {"programs": 0, "scholarships": 0, "by_source": Counter(), "by_degree": Counter(),
              "by_field": Counter(), "imported": 0, "blank_in_imported": {"stipend": 0},
              "duplicate_program_ids": [], "duplicate_scholarship_ids": [], "non_https": [],
              "verified": {"programs": None, "scholarships": None}}

    assert "  stipend                      0  -" in format_report(report)


# ---- The command ----
# Why: the exit code lets a script or CI notice problems; 2 means it was called the wrong way.

def test_command_exit_0_when_clean(data_dir, capsys):
    assert main(["data_report", str(data_dir)]) == 0
    assert "Programs: 5" in capsys.readouterr().out


def test_command_exit_1_when_there_are_problems(data_dir, capsys):
    write(data_dir / "programs.csv", PROGRAM_COLUMNS, [program("X"), program("X")])

    assert main(["data_report", str(data_dir)]) == 1
    assert "Duplicate program ids: X" in capsys.readouterr().out


def test_command_uses_the_data_folder_by_default(data_dir, monkeypatch, capsys):
    folder = data_dir.parent / "work"
    (folder / "data").mkdir(parents=True)
    for name in ("programs.csv", "scholarships.csv", "SOURCES.md"):
        (folder / "data" / name).write_bytes((data_dir / name).read_bytes())
    monkeypatch.chdir(folder)

    assert main(["data_report"]) == 0
    assert "Programs: 5" in capsys.readouterr().out


def test_command_with_too_many_arguments_shows_usage(capsys):
    assert main(["data_report", "a", "b"]) == 2
    assert capsys.readouterr().out == "usage: python -m gradmatch.data_report [data_dir]\n"


# ---- Tests added after mutation testing (see docs/mutation-testing.md) ----
# Why (mutation testing): small changes to the titles, blank lines, separators and default values
# went unnoticed, because the tests above only looked for parts of the text. These check the whole
# printed report, files with missing columns, a single imported row (boundary) and line breaks.

EXPECTED_REPORT = """Programs: 5    Scholarships: 1

Programs by source:
  ipeds                                          3
  estimate                                       1
  official-page                                  1

Programs by degree:
  BS                                             2
  MS                                             2
  PhD                                            1

Programs by field (2 fields):
  Computer Science                               4
  Data Science                                   1

Blank cells in the 3 imported (ipeds) rows (blank = not published):
  program_id                   0  0%
  field                        0  0%
  degree                       0  0%
  acceptance_rate              2  67%
  stipend                      1  33%
  website                      0  0%
  source                       0  0%

Duplicate program ids: none
Duplicate scholarship ids: none
Websites not starting with https://: none

Checked by hand on official pages (from SOURCES.md):
  programs:     2 of 5 hand-entered rows
  scholarships: 1 of 13"""


def test_whole_printed_report_is_exact(data_dir):
    assert format_report(build_report(data_dir)) == EXPECTED_REPORT


def test_files_with_missing_columns_still_get_a_report(tmp_path):
    # Only program_id/scholarship_id are missing in one file, and degree, field and website in
    # the other: every missing cell counts as blank, so nothing crashes and nothing is invented.
    write(tmp_path / "programs.csv", ["source"], [{"source": "ipeds"}, {"source": "ipeds"}])
    write(tmp_path / "scholarships.csv", ["name"], [{"name": "A"}, {"name": "B"}])

    report = build_report(tmp_path)

    assert report["by_degree"] == {"": 2} and report["by_field"] == {"": 2}
    assert report["duplicate_program_ids"] == [""]           # both rows have no id
    assert report["duplicate_scholarship_ids"] == [""]
    assert report["non_https"] == ["", "", "", ""]            # no website column at all
    assert "  (blank)                                        2" in format_report(report)


def test_a_single_imported_row_is_counted(tmp_path):
    # Boundary value: exactly one imported row.
    write(tmp_path / "programs.csv", PROGRAM_COLUMNS, [program("ONLY", stipend="")])
    write(tmp_path / "scholarships.csv", ["scholarship_id", "website"], [])

    assert build_report(tmp_path)["blank_in_imported"]["stipend"] == 1


def test_a_line_break_inside_a_quoted_cell_stays_in_that_cell(tmp_path):
    write(tmp_path / "programs.csv", PROGRAM_COLUMNS, [program("P1", field="Data\r\nScience")])
    write(tmp_path / "scholarships.csv", ["scholarship_id", "website"], [])

    assert build_report(tmp_path)["by_field"] == {"Data\r\nScience": 1}


def test_two_duplicate_scholarship_ids_are_printed_with_comma_and_space(data_dir):
    write(data_dir / "scholarships.csv", ["scholarship_id", "website"],
          [{"scholarship_id": s, "website": "https://a.org"} for s in ("S2", "S1", "S2", "S1")])

    assert "Duplicate scholarship ids: S1, S2\n" in format_report(build_report(data_dir))
