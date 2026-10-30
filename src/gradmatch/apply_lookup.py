"""Apply a filled lookup sheet to data/programs.csv and data/SOURCES.md.

A person opens each official program page and fills one sheet row. Only
rows with a name in `checked_by` are applied. For each one:
- every value is checked first; if any row is bad, nothing is written,
- a blank cell means "not stated on the page" and keeps the current value,
- the program row is updated and its `source` becomes "official-page"
  (the column is added to programs.csv if it is missing),
- its status in SOURCES.md becomes
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

# The columns the sheet must have. Missing ones are reported before anything else happens.
SHEET_COLUMNS = ["program_id", "university", "program_name", "degree", "official_url",
                 "tuition_in_state", "tuition_out_state", "application_deadline", "stipend",
                 "phd_tuition_waiver", "min_toefl", "checked_by", "checked_on", "notes"]
# Does the PhD waive tuition? "na" is for master's programs, where the question does not apply.
WAIVER_VALUES = ("yes", "no", "na")
TOEFL_MIN, TOEFL_MAX = 0, 120
DATE_FORMAT = "%Y-%m-%d"

# Sheet column -> programs.csv column, for the values copied as they are.
# Sheet column -> programs.csv column. Only these values come from the sheet; the estimates
# (average GPA, acceptance rate) stay as they are, and the app labels them "(est.)".
COPIED = {
    "official_url": "website",
    "tuition_in_state": "tuition_in_state",
    "tuition_out_state": "tuition_out_state",
    "application_deadline": "application_deadline",
    "stipend": "stipend",
    "min_toefl": "min_toefl",
}
# Every row a person checks gets this source, so anyone can see which rows were checked by hand.
OFFICIAL_SOURCE = "official-page"
IMPORTED_SOURCE = "ipeds"      # rows made by ipeds_import; they are not listed in SOURCES.md until checked
IMPORTED_HEADING = "## Checked programs imported from official data"
IMPORTED_TABLE_HEADER = ("| program_id | University | Program | Status | Source (official page) | Notes |\n"
                         "|---|---|---|---|---|---|")
STATUS_LINE = re.compile(r"Verified: \d+ of \d+ rows \(programs\)")


# The error for a bad sheet. When it is raised, nothing has been written yet.
class SheetError(ValueError):
    """Raised when the lookup sheet has a bad row; nothing has been written."""


# ---- Public function and command ----

# The whole job in order: read, check every row, update in memory, check the result with the
# real loader, and only then write both files. Returns one line per changed value so the
# person can see exactly what changed.
def apply_lookup(sheet_path, data_dir) -> list[str]:
    """Apply the sheet and return one line per changed value."""
    programs_path = Path(data_dir) / "programs.csv"
    sources_path = Path(data_dir) / "SOURCES.md"

    header, programs = _read_programs(programs_path)
    by_id = {row["program_id"]: row for row in programs}
    sources = sources_path.read_text(encoding="utf-8")

    checked = _read_sheet(sheet_path, by_id, sources)     # raises SheetError
    # An empty sheet changes nothing, so we do not even rewrite the files.
    if not checked:
        return ["0 row(s) applied, 0 value(s) changed"]     # nothing to do: write nothing

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


# The command line: python -m gradmatch.apply_lookup sheet.csv [data_folder].
# Exit code 0 = applied, 1 = bad sheet (nothing written), 2 = wrong arguments.
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

# Read the sheet and keep only rows with a name in checked_by (the rows a person actually
# checked). Every bad row is collected, not just the first, so the person can fix them all
# in one go. The line number is in each message, like in the CSV loader.
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


# All the checks for one sheet row. A blank cell is allowed: it means "not stated on the page"
# and keeps the old value. We never fill in a guess.
def _row_problems(row: dict, by_id: dict, sources: str) -> list[str]:
    program = by_id.get(row["program_id"])
    if program is None:
        return [f"unknown program_id '{row['program_id']}'"]

    problems = []
    # The 24 hand-entered programs must already be listed in SOURCES.md. A program from the importer
    # is not (there are tens of thousands); it gets its row here, once a person has checked it.
    if f"| {row['program_id']} |" not in sources and program["source"] != IMPORTED_SOURCE:
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


# The PhD tuition-waiver rule. The cost math waives tuition only for a PhD with a stipend above
# 0, so "yes" needs a stipend, or the waiver would be lost. "no" means stipend 0 (tuition is charged).
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
    # A stipend together with "no waiver" is refused rather than silently set to 0: dropping a
    # number the person typed would hide their mistake.
    if waiver == "no" and stipend_given and float(row["stipend"]) > 0:
        # The rule sets the stipend to 0; refuse rather than silently drop a value.
        return ["phd_tuition_waiver is no, so stipend must be blank or 0"]
    return []


# Small yes/no checks, each used by the row checks above.
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

# Read programs.csv as plain text rows (not Program objects), so we can write it back with
# exactly the same columns and formatting, changing only the cells we mean to change.
def _read_programs(path) -> tuple[list[str], list[dict]]:
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        header, programs = list(reader.fieldnames), list(reader)
    # Older files have no source column. We add it; a blank source means "estimate".
    if "source" not in header:
        # Older files have no source column. A blank source means "estimate".
        header.append("source")
        for program in programs:
            program["source"] = ""
    return header, programs


# Copy the filled-in sheet values into the program row and list each change as "old -> new".
def _update_program(program: dict, sheet_row: dict) -> list[str]:
    """Copy every non-blank value into the program row; return what changed."""
    new_values = {COPIED[name]: sheet_row[name] for name in COPIED if sheet_row[name]}
    if program["degree"] == "PhD" and sheet_row["phd_tuition_waiver"] == "no":
        new_values["stipend"] = "0"          # no waiver: tuition is charged, no stipend counted
    new_values["source"] = OFFICIAL_SOURCE    # a person checked this row on the official page

    changes = []
    for column, value in new_values.items():
        if program[column] != value:
            changes.append(f"{program['program_id']}: {column} {program[column] or '(empty)'} -> {value}")
            program[column] = value
    return changes


# Turn the rows back into CSV text, with \n line endings like the file already has.
def _programs_text(header: list[str], programs: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(programs)
    return buffer.getvalue()


# Safety net: write the new file next to the real one, load it with the normal loader, and
# delete it. If the loader would reject it, we stop before the real file is touched.
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

# Update this program's row in the SOURCES.md table. A "|" in the notes would break the
# Markdown table, so it is changed to "/".
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
    return _add_imported_row(sources, sheet_row)


def _add_imported_row(sources: str, sheet_row: dict) -> str:
    """Add a row for a checked imported program, under its own heading at the end of the file."""
    row = ("| " + " | ".join([
        sheet_row["program_id"], sheet_row["university"], sheet_row["program_name"],
        f"verified by {sheet_row['checked_by']} on {sheet_row['checked_on']}",
        sheet_row["official_url"], sheet_row["notes"].replace("|", "/")]) + " |")
    if IMPORTED_HEADING not in sources:
        sources = sources.rstrip("\n") + f"\n\n{IMPORTED_HEADING}\n\n{IMPORTED_TABLE_HEADER}\n"
    return sources.rstrip("\n") + "\n" + row + "\n"


# Recount the "Verified: N of M" line instead of adding 1, so it can never drift from the table.
# Only programs listed in SOURCES.md (the hand-entered ones) count; the 45,000 imported rows
# are official data and are not checked one by one.
def _count_verified(sources: str, program_ids: list[str]) -> str:
    """Count the programs listed in SOURCES.md (the hand-entered rows) and how many are verified.

    Imported rows are in programs.csv but not in SOURCES.md, so they are not counted.
    """
    known = set(program_ids)
    listed = verified = 0
    for line in sources.split("\n"):
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == 6 and cells[0] in known:
            listed += 1
            if cells[3].startswith("verified by"):
                verified += 1
    return STATUS_LINE.sub(f"Verified: {verified} of {listed} rows (programs)", sources)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))
