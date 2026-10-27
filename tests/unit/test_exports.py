"""Unit tests for exports.py.

Techniques: equivalence partitioning on the input list (empty, one item,
several items) and on the text in names (plain, with commas, quotes,
semicolons, backslashes and newlines); boundary-value analysis on line
length (75 bytes is the folding limit) and on the date (leap day 2028-02-29).
"""
import csv
import io
import time
from datetime import date, datetime, timedelta, timezone

import pytest

from conftest import make_program
from gradmatch.exports import CSV_COLUMNS, to_csv, to_ics
from gradmatch.models import Scholarship
from gradmatch.search import ProgramResult

pytestmark = pytest.mark.unit

STAMP = datetime(2026, 10, 24, 15, 0, 0)


def make_result(**program_changes) -> ProgramResult:
    return ProgramResult(program=make_program(**program_changes), yearly_cost=32600.0,
                         total_cost=65200.0, fit="Match", funding="Self-Funded")


def make_scholarship(**changes) -> Scholarship:
    values = dict(scholarship_id="S1", name="Test Fellowship", type="fellowship",
                  amount=1000.0, degree_levels=("MS",), fields=("Any",), min_gpa=0.0,
                  citizenship=("Any",), states=("Any",), special=(),
                  deadline=date(2026, 12, 1), website="https://example.org/s1")
    values.update(changes)
    return Scholarship(**values)


def read_csv(text: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(text)))


def unfold(ics: str) -> list[str]:
    """Undo line folding (CRLF + space) and split into lines."""
    return ics.replace("\r\n ", "").split("\r\n")


# =====================================================================
# to_csv
# =====================================================================

def test_csv_empty_list_has_only_the_header():
    assert read_csv(to_csv([])) == [CSV_COLUMNS]


def test_csv_one_result_has_all_columns_in_order():
    rows = read_csv(to_csv([make_result()]))

    assert rows[1] == ["Test University", "MS in Computer Science", "MS", "MI",
                       "32600.00", "65200.00", "Match", "Self-Funded", "2027-01-15",
                       "https://example.edu/ms-cs"]


def test_csv_several_results_keep_their_order():
    results = [make_result(university="A"), make_result(university="B"),
               make_result(university="C")]

    rows = read_csv(to_csv(results))

    assert [row[0] for row in rows[1:]] == ["A", "B", "C"]


@pytest.mark.parametrize("name", [
    "Computer Science, Data Track",     # comma
    'The "Best" Program',               # double quotes
    "Data; Science",                    # semicolon
    "Line one\nLine two",               # newline
])
def test_csv_special_characters_stay_in_one_cell(name):
    rows = read_csv(to_csv([make_result(program_name=name)]))

    assert len(rows) == 2
    assert rows[1][1] == name
    assert len(rows[1]) == len(CSV_COLUMNS)


# =====================================================================
# to_ics
# =====================================================================

def test_ics_empty_list_is_a_valid_calendar_with_no_events():
    lines = unfold(to_ics([], STAMP))

    assert lines[:3] == ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//GradMatch//Deadlines//EN"]
    assert lines[-2:] == ["END:VCALENDAR", ""]      # ends with CRLF
    assert "BEGIN:VEVENT" not in lines


def test_ics_uses_crlf_line_endings_only():
    ics = to_ics([make_program(), make_scholarship()], STAMP)

    assert "\n" not in ics.replace("\r\n", "")
    assert ics.endswith("\r\n")


def test_ics_one_program_gives_one_all_day_event():
    lines = unfold(to_ics([make_program()], STAMP))

    assert lines.count("BEGIN:VEVENT") == 1
    assert "UID:program-P1@gradmatch" in lines
    assert "DTSTAMP:20261024T150000Z" in lines
    assert "DTSTART;VALUE=DATE:20270115" in lines
    assert "SUMMARY:Application deadline: Test University – MS in Computer Science" in lines
    assert "URL:https://example.edu/ms-cs" in lines


def test_ics_several_items_mix_programs_and_scholarships():
    items = [make_program(program_id="P1"), make_program(program_id="P2"),
             make_scholarship(scholarship_id="S1")]

    lines = unfold(to_ics(items, STAMP))

    assert lines.count("BEGIN:VEVENT") == 3
    assert [line for line in lines if line.startswith("UID:")] == [
        "UID:program-P1@gradmatch", "UID:program-P2@gradmatch", "UID:scholarship-S1@gradmatch"]
    assert "SUMMARY:Scholarship deadline: Test Fellowship" in lines


def test_ics_uid_is_stable_between_exports():
    first = to_ics([make_program()], STAMP)
    second = to_ics([make_program()], STAMP + timedelta(days=3))

    uids = [[line for line in unfold(text) if line.startswith("UID:")] for text in (first, second)]
    assert uids[0] == uids[1]


def test_ics_stamp_with_time_zone_is_converted_to_utc():
    eastern = timezone(timedelta(hours=-4))
    lines = unfold(to_ics([make_program()], datetime(2026, 10, 24, 11, 0, tzinfo=eastern)))

    assert "DTSTAMP:20261024T150000Z" in lines


@pytest.mark.parametrize("name, escaped", [
    ("Data, Science", "Data\\, Science"),
    ("Data; Science", "Data\\; Science"),
    ("Line one\nLine two", "Line one\\nLine two"),
    ("Back\\slash", "Back\\\\slash"),
    ('The "Best" Fellowship', 'The "Best" Fellowship'),    # quotes need no escaping
])
def test_ics_summary_escapes_special_characters(name, escaped):
    lines = unfold(to_ics([make_scholarship(name=name)], STAMP))

    assert f"SUMMARY:Scholarship deadline: {escaped}" in lines


def test_ics_leap_day_deadline():
    lines = unfold(to_ics([make_scholarship(deadline=date(2028, 2, 29))], STAMP))

    assert "DTSTART;VALUE=DATE:20280229" in lines


# ---- Line folding: boundary at 75 bytes ----

def raw_lines(ics: str) -> list[str]:
    return ics.split("\r\n")[:-1]


def test_ics_long_name_is_folded_and_unfolds_to_the_original():
    name = "Graduate Fellowship for Advanced Research in Computer and Data Science " * 3
    ics = to_ics([make_scholarship(name=name.strip())], STAMP)

    assert all(len(line.encode("utf-8")) <= 75 for line in raw_lines(ics))
    assert any(line.startswith(" ") for line in raw_lines(ics))
    assert f"SUMMARY:Scholarship deadline: {name.strip()}" in unfold(ics)


@pytest.mark.parametrize("extra, folded", [(0, False), (1, True)])
def test_ics_fold_boundary_at_75_bytes(extra, folded):
    # "SUMMARY:Scholarship deadline: " is 30 bytes, so a 45-byte name makes a
    # line of exactly 75 bytes (not folded); one more byte must fold it.
    name = "x" * (45 + extra)
    lines = raw_lines(to_ics([make_scholarship(name=name)], STAMP))

    summary_index = next(i for i, line in enumerate(lines) if line.startswith("SUMMARY:"))
    assert len(lines[summary_index].encode("utf-8")) <= 75
    assert lines[summary_index + 1].startswith(" ") is folded


def test_ics_folding_never_splits_a_multibyte_character():
    name = "é" * 60      # 2 bytes each in UTF-8
    ics = to_ics([make_scholarship(name=name)], STAMP)

    for line in raw_lines(ics):
        assert len(line.encode("utf-8")) <= 75
        line.encode("utf-8").decode("utf-8")     # would fail if a character were cut
    assert f"SUMMARY:Scholarship deadline: {name}" in unfold(ics)


# ---- Tests added after mutation testing (see docs/mutation-testing.md) ----

def test_ics_calendar_header_and_every_event_is_closed():
    lines = unfold(to_ics([make_program(program_id="P1"), make_program(program_id="P2")], STAMP))

    assert lines[3] == "CALSCALE:GREGORIAN"
    assert lines.count("BEGIN:VEVENT") == lines.count("END:VEVENT") == 2


def test_ics_windows_line_break_in_a_name_is_escaped_once():
    lines = unfold(to_ics([make_scholarship(name="Line one\r\nLine two")], STAMP))

    assert "SUMMARY:Scholarship deadline: Line one\\nLine two" in lines


def test_ics_stamp_is_utc_whatever_the_server_time_zone(monkeypatch):
    # The result must not depend on the computer's time zone setting.
    monkeypatch.setenv("TZ", "America/Los_Angeles")
    time.tzset()
    try:
        eastern = timezone(timedelta(hours=-4))
        lines = unfold(to_ics([make_program()], datetime(2026, 10, 24, 11, 0, tzinfo=eastern)))
    finally:
        monkeypatch.undo()
        time.tzset()

    assert "DTSTAMP:20261024T150000Z" in lines


def test_ics_folded_lines_are_filled_to_75_bytes():
    name = "x" * 200
    lines = raw_lines(to_ics([make_scholarship(name=name)], STAMP))

    start = next(i for i, line in enumerate(lines) if line.startswith("SUMMARY:"))
    summary_lines = [lines[start]]
    for line in lines[start + 1:]:
        if not line.startswith(" "):
            break
        summary_lines.append(line)
    # Every part except the last is full: 75 bytes, counting the leading space.
    assert [len(line) for line in summary_lines[:-1]] == [75] * (len(summary_lines) - 1)


# ---- Values that are not published (None) ----

def test_csv_unpublished_deadline_is_an_empty_cell():
    rows = read_csv(to_csv([make_result(application_deadline=None)]))

    assert rows[1][CSV_COLUMNS.index("deadline")] == ""
    assert len(rows[1]) == len(CSV_COLUMNS)


def test_csv_unknown_costs_are_empty_cells():
    result = ProgramResult(program=make_program(), yearly_cost=None, total_cost=None,
                           fit="Unknown", funding="Funding unknown")

    row = read_csv(to_csv([result]))[1]

    assert row[CSV_COLUMNS.index("yearly_cost")] == ""
    assert row[CSV_COLUMNS.index("total_cost")] == ""
    assert row[CSV_COLUMNS.index("fit")] == "Unknown"


def test_csv_zero_cost_is_written_not_left_empty():
    # Boundary: 0 is a real value, only None is empty.
    result = ProgramResult(program=make_program(), yearly_cost=0.0, total_cost=0.0,
                           fit="Match", funding="Fully Funded")

    row = read_csv(to_csv([result]))[1]

    assert row[CSV_COLUMNS.index("yearly_cost")] == "0.00"


def test_ics_leaves_out_programs_without_a_deadline():
    items = [make_program(program_id="UNKNOWN", application_deadline=None),
             make_program(program_id="KNOWN"), make_scholarship()]

    lines = unfold(to_ics(items, STAMP))

    assert lines.count("BEGIN:VEVENT") == 2
    assert "UID:program-UNKNOWN@gradmatch" not in lines
    assert "UID:program-KNOWN@gradmatch" in lines


def test_ics_only_unpublished_deadlines_gives_a_calendar_with_no_events():
    lines = unfold(to_ics([make_program(application_deadline=None)], STAMP))

    assert "BEGIN:VEVENT" not in lines
    assert lines[-2:] == ["END:VCALENDAR", ""]
