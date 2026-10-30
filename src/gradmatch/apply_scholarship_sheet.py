"""Apply a filled scholarship sheet to data/scholarships.csv and data/SOURCES.md.

A person opens each official scholarship page and fills one sheet row. Only
rows with a name in `checked_by` are applied. For each one:
- every value is checked first; if any row is bad, nothing is written,
- a blank cell means "not stated on the page" and keeps the current value,
- the amount, deadline and website in scholarships.csv are updated,
- its status in SOURCES.md becomes "verified by <checked_by> on <checked_on>",
- the "Scholarships verified: N of M" count is counted again.

Run it with:  PYTHONPATH=src python -m gradmatch.apply_scholarship_sheet <sheet.csv> [data_dir]
"""
# In plain words: this is the scholarship version of apply_lookup. A person checks each
# scholarship on its official page and types the amount, the deadline and the link into
# data/scholarship_lookup_sheet.csv. This script copies those values into scholarships.csv and
# marks the scholarship "verified by <name> on <date>" in SOURCES.md. Like apply_lookup, it
# checks every row first and writes nothing at all if any row is wrong.

import csv
import io
import re
import sys
from pathlib import Path

from gradmatch.apply_lookup import SheetError, _is_date, _is_non_negative_number
from gradmatch.data_loader import DataError, load_scholarships

# The columns the sheet must have. `name` is only there to help the person find the right page.
SHEET_COLUMNS = ["scholarship_id", "name", "official_url", "amount", "deadline",
                 "checked_by", "checked_on", "notes"]
# Sheet column -> scholarships.csv column. Only these values come from the sheet.
COPIED = {"official_url": "website", "amount": "amount", "deadline": "deadline"}
STATUS_LINE = re.compile(r"Scholarships verified: \d+ of \d+")
# The scholarship table in SOURCES.md has 5 columns; the program tables have 6.
TABLE_CELLS = 5
STATUS, SOURCE, NOTES = 2, 3, 4      # the cells of a scholarship row that this script changes


# ---- Public function and command ----

# The whole job in order: read, check every row, update in memory, check the result with the
# real loader, and only then write both files. Returns one line per changed value.
def apply_scholarship_sheet(sheet_path, data_dir) -> list[str]:
    """Apply the sheet and return one line per changed value."""
    scholarships_path = Path(data_dir) / "scholarships.csv"
    sources_path = Path(data_dir) / "SOURCES.md"

    header, scholarships = _read_scholarships(scholarships_path)
    by_id = {row["scholarship_id"]: row for row in scholarships}
    sources = sources_path.read_text(encoding="utf-8")

    checked = _read_sheet(sheet_path, by_id, sources)     # raises SheetError
    if not checked:
        return ["0 row(s) applied, 0 value(s) changed"]     # nothing to do: write nothing

    changes = []
    for sheet_row in checked:
        changes += _update_scholarship(by_id[sheet_row["scholarship_id"]], sheet_row)
        sources = _set_status(sources, sheet_row)
    sources = _count_verified(sources, set(by_id))

    new_scholarships = _csv_text(header, scholarships)
    _check_with_loader(new_scholarships, scholarships_path)   # raises SheetError
    scholarships_path.write_text(new_scholarships, encoding="utf-8")
    sources_path.write_text(sources, encoding="utf-8")
    return [f"{len(checked)} row(s) applied, {len(changes)} value(s) changed"] + changes


# The command line. Exit code 0 = applied, 1 = bad sheet (nothing written), 2 = wrong arguments.
def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3):
        print("usage: python -m gradmatch.apply_scholarship_sheet <sheet.csv> [data_dir]")
        return 2
    data_dir = argv[2] if len(argv) == 3 else "data"
    try:
        lines = apply_scholarship_sheet(argv[1], data_dir)
    except SheetError as error:
        print(f"Nothing was written.\n{error}")
        return 1
    print("\n".join(lines))
    return 0


# ---- Reading and checking the sheet ----

# Keep only the rows a person checked (a name in checked_by). Every bad row is collected with
# its line number, so all mistakes can be fixed in one go.
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
                errors.append(f"line {reader.line_num} ({row['scholarship_id']}): " + "; ".join(problems))
            else:
                checked.append(row)
    if errors:
        raise SheetError("\n".join(errors))
    return checked


# All the checks for one sheet row. A blank value is allowed and keeps the old value; only
# checked_on must always be there, because "verified on <date>" needs a date.
def _row_problems(row: dict, by_id: dict, sources: str) -> list[str]:
    if row["scholarship_id"] not in by_id:
        return [f"unknown scholarship_id '{row['scholarship_id']}'"]

    problems = []
    if f"| {row['scholarship_id']} |" not in sources:
        problems.append("scholarship_id has no row in SOURCES.md")
    if row["official_url"] and not row["official_url"].startswith("https://"):
        problems.append("official_url must start with https://")
    if row["amount"] and not _is_non_negative_number(row["amount"]):
        problems.append(f"amount must be a non-negative number, got '{row['amount']}'")
    if row["deadline"] and not _is_date(row["deadline"]):
        problems.append("deadline must be a date in YYYY-MM-DD format")
    if not _is_date(row["checked_on"]):
        problems.append("checked_on must be a date in YYYY-MM-DD format")
    return problems


# ---- Updating scholarships.csv ----

# Read scholarships.csv as plain text rows, so it is written back with the same columns.
def _read_scholarships(path) -> tuple[list[str], list[dict]]:
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames), list(reader)


# Copy the filled-in sheet values into the scholarship row and list each change as "old -> new".
def _update_scholarship(scholarship: dict, sheet_row: dict) -> list[str]:
    changes = []
    for sheet_column, column in COPIED.items():
        value = sheet_row[sheet_column]
        if value and scholarship[column] != value:
            changes.append(f"{scholarship['scholarship_id']}: {column} {scholarship[column]} -> {value}")
            scholarship[column] = value
    return changes


def _csv_text(header: list[str], rows: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


# Safety net: load the new file with the normal loader before the real file is replaced.
def _check_with_loader(text: str, scholarships_path: Path):
    temp_path = scholarships_path.with_name("scholarships.csv.new")
    temp_path.write_text(text, encoding="utf-8")
    try:
        load_scholarships(temp_path)
    except DataError as error:
        raise SheetError(f"the updated scholarships.csv would not load: {error}") from error
    finally:
        temp_path.unlink()


# ---- Updating SOURCES.md ----

# Update this scholarship's row in the SOURCES.md table. A "|" in the notes would break the
# Markdown table, so it is changed to "/". The row is known to exist (checked in _row_problems).
def _set_status(sources: str, sheet_row: dict) -> str:
    lines = sources.split("\n")
    for index, line in enumerate(lines):
        cells = _cells(line)
        if len(cells) == TABLE_CELLS and cells[0] == sheet_row["scholarship_id"]:
            cells[STATUS] = f"verified by {sheet_row['checked_by']} on {sheet_row['checked_on']}"
            if sheet_row["official_url"]:
                cells[SOURCE] = sheet_row["official_url"]
            cells[NOTES] = sheet_row["notes"].replace("|", "/")
            lines[index] = "| " + " | ".join(cells) + " |"
    return "\n".join(lines)


# Recount "Scholarships verified: N of M" from the table instead of adding 1, so the count can
# never drift from the rows. Only 5-cell rows whose first cell is a scholarship id count.
def _count_verified(sources: str, scholarship_ids: set) -> str:
    listed = verified = 0
    for line in sources.split("\n"):
        cells = _cells(line)
        if len(cells) == TABLE_CELLS and cells[0] in scholarship_ids:
            listed += 1
            if cells[STATUS].startswith("verified by"):
                verified += 1
    return STATUS_LINE.sub(f"Scholarships verified: {verified} of {listed}", sources)


# The cells of a Markdown table row, trimmed. A line that is not a table row gives one cell.
def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip("|").split("|")]


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))
