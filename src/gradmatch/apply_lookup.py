"""Apply a filled lookup sheet to data/programs.csv and data/SOURCES.md.

A person opens each official program page and fills one sheet row. Only
rows with a name in `checked_by` are applied. For each one:
- every value is checked first; if any row is bad, nothing is written,
- a blank cell means "not stated on the page" and keeps the current value,
- the program row is updated, and its status in SOURCES.md becomes
  "verified by <checked_by> on <checked_on>",
- the "Verified: N of M rows (programs)" line is counted again.

Run it with:  PYTHONPATH=src python -m gradmatch.apply_lookup <sheet.csv> [data_dir]
"""
import csv
import io
import re
import sys
from datetime import datetime
from pathlib import Path

from gradmatch.data_loader import DataError, load_programs

SHEET_COLUMNS = ["program_id", "university", "program_name", "degree", "official_url",
                 "tuition_in_state", "tuition_out_state", "application_deadline", "stipend",
                 "phd_tuition_waiver", "min_toefl", "checked_by", "checked_on", "notes"]
WAIVER_VALUES = ("yes", "no", "na")
TOEFL_MIN, TOEFL_MAX = 0, 120
DATE_FORMAT = "%Y-%m-%d"

# Sheet column -> programs.csv column, for the values copied as they are.
COPIED = {
    "official_url": "website",
    "tuition_in_state": "tuition_in_state",
    "tuition_out_state": "tuition_out_state",
    "application_deadline": "application_deadline",
    "stipend": "stipend",
    "min_toefl": "min_toefl",
}
STATUS_LINE = re.compile(r"Verified: \d+ of \d+ rows \(programs\)")


class SheetError(ValueError):
    """Raised when the lookup sheet has a bad row; nothing has been written."""


# ---- Public function and command ----

def apply_lookup(sheet_path, data_dir) -> list[str]:
    """Apply the sheet and return one line per changed value."""
    programs_path = Path(data_dir) / "programs.csv"
    sources_path = Path(data_dir) / "SOURCES.md"

    header, programs = _read_programs(programs_path)
    by_id = {row["program_id"]: row for row in programs}
    sources = sources_path.read_text(encoding="utf-8")

    checked = _read_sheet(sheet_path, by_id, sources)     # raises SheetError

    changes = []
    for sheet_row in checked:
        changes += _update_program(by_id[sheet_row["program_id"]], sheet_row)
        sources = _set_status(sources, sheet_row)
    sources = _count_verified(sources, [row["program_id"] for row in programs])

    new_programs = _programs_text(header, programs)
    _check_with_loader(new_programs, programs_path)        # raises SheetError
    programs_path.write_text(new_programs, encoding="utf-8")
    sources_path.write_text(sources, encoding="utf-8")
    return [f"{len(checked)} row(s) applied, {len(changes)} value(s) changed"] + changes


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3):
        print("usage: python -m gradmatch.apply_lookup <sheet.csv> [data_dir]")
        return 2
    data_dir = argv[2] if len(argv) == 3 else "data"
    try:
        lines = apply_lookup(argv[1], data_dir)
    except SheetError as error:
        print(f"Nothing was written.\n{error}")
        return 1
    print("\n".join(lines))
    return 0


# ---- Reading and checking the sheet ----

def _read_sheet(sheet_path, by_id: dict, sources: str) -> list[dict]:
    """Return the checked rows. Raise SheetError listing every bad row."""
    errors = []
    checked = []
    with open(sheet_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing = [name for name in SHEET_COLUMNS if name not in (reader.fieldnames or [])]
        if missing:
            raise SheetError(f"{sheet_path}: missing column(s): {', '.join(missing)}")
        for row in reader:
            row = {name: (row[name] or "").strip() for name in SHEET_COLUMNS}
            if not row["checked_by"]:
                continue                     # not checked yet: skip
            problems = _row_problems(row, by_id, sources)
            if problems:
                errors.append(f"line {reader.line_num} ({row['program_id']}): " + "; ".join(problems))
            else:
                checked.append(row)
    if errors:
        raise SheetError("\n".join(errors))
    return checked


def _row_problems(row: dict, by_id: dict, sources: str) -> list[str]:
    program = by_id.get(row["program_id"])
    if program is None:
        return [f"unknown program_id '{row['program_id']}'"]

    problems = []
    if f"| {row['program_id']} |" not in sources:
        problems.append("program_id has no row in SOURCES.md")
    if row["official_url"] and not row["official_url"].startswith("https://"):
        problems.append("official_url must start with https://")
    for name in ("tuition_in_state", "tuition_out_state", "stipend"):
        if row[name] and not _is_non_negative_number(row[name]):
            problems.append(f"{name} must be a non-negative number, got '{row[name]}'")
    if row["application_deadline"] and not _is_date(row["application_deadline"]):
        problems.append("application_deadline must be a date in YYYY-MM-DD format")
    if row["min_toefl"] and not _is_toefl(row["min_toefl"]):
        problems.append(f"min_toefl must be a whole number from 0 to 120, got '{row['min_toefl']}'")
    if not _is_date(row["checked_on"]):
        problems.append("checked_on must be a date in YYYY-MM-DD format")
    problems += _waiver_problems(row, program["degree"])
    return problems


def _waiver_problems(row: dict, degree: str) -> list[str]:
    waiver = row["phd_tuition_waiver"]
    if waiver and waiver not in WAIVER_VALUES:
        return ["phd_tuition_waiver must be yes, no or na"]
    if degree != "PhD":
        if waiver in ("yes", "no"):
            return ["phd_tuition_waiver must be na or blank for an MS program"]
        return []
    stipend_given = _is_non_negative_number(row["stipend"])
    if waiver == "yes" and not (stipend_given and float(row["stipend"]) > 0):
        return ["phd_tuition_waiver is yes, so stipend must be greater than 0"]
    if waiver == "no" and stipend_given and float(row["stipend"]) > 0:
        # The rule sets the stipend to 0; refuse rather than silently drop a value.
        return ["phd_tuition_waiver is no, so stipend must be blank or 0"]
    return []


def _is_non_negative_number(text: str) -> bool:
    try:
        return float(text) >= 0
    except ValueError:
        return False


def _is_date(text: str) -> bool:
    try:
        datetime.strptime(text, DATE_FORMAT)
        return True
    except ValueError:
        return False


def _is_toefl(text: str) -> bool:
    return text.isdigit() and TOEFL_MIN <= int(text) <= TOEFL_MAX


# ---- Updating programs.csv ----

def _read_programs(path) -> tuple[list[str], list[dict]]:
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames), list(reader)


def _update_program(program: dict, sheet_row: dict) -> list[str]:
    """Copy every non-blank value into the program row; return what changed."""
    new_values = {COPIED[name]: sheet_row[name] for name in COPIED if sheet_row[name]}
    if program["degree"] == "PhD" and sheet_row["phd_tuition_waiver"] == "no":
        new_values["stipend"] = "0"          # no waiver: tuition is charged, no stipend counted

    changes = []
    for column, value in new_values.items():
        if program[column] != value:
            changes.append(f"{program['program_id']}: {column} {program[column] or '(empty)'} -> {value}")
            program[column] = value
    return changes


def _programs_text(header: list[str], programs: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(programs)
    return buffer.getvalue()


def _check_with_loader(text: str, programs_path: Path):
    """Load the new file with the normal loader before replacing the real one."""
    temp_path = programs_path.with_name("programs.csv.new")
    temp_path.write_text(text, encoding="utf-8")
    try:
        load_programs(temp_path)
    except DataError as error:
        raise SheetError(f"the updated programs.csv would not load: {error}") from error
    finally:
        temp_path.unlink()


# ---- Updating SOURCES.md ----

def _set_status(sources: str, sheet_row: dict) -> str:
    """Rewrite the program's row in the SOURCES.md table (6 columns)."""
    program_id = sheet_row["program_id"]
    lines = sources.split("\n")
    for index, line in enumerate(lines):
        if line.startswith(f"| {program_id} |"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            cells[3] = f"verified by {sheet_row['checked_by']} on {sheet_row['checked_on']}"
            if sheet_row["official_url"]:
                cells[4] = sheet_row["official_url"]
            cells[5] = sheet_row["notes"].replace("|", "/")
            lines[index] = "| " + " | ".join(cells) + " |"
    return "\n".join(lines)


def _count_verified(sources: str, program_ids: list[str]) -> str:
    verified = 0
    for line in sources.split("\n"):
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == 6 and cells[0] in program_ids and cells[3].startswith("verified by"):
            verified += 1
    return STATUS_LINE.sub(f"Verified: {verified} of {len(program_ids)} rows (programs)", sources)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))
