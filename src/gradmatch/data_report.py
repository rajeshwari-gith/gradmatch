"""Print a data quality report for the CSV files in data/.

Run it with:  PYTHONPATH=src python -m gradmatch.data_report [data_dir]

It reports rows by source, degree and field; how many cells are blank in each
column of the imported (source=ipeds) rows; duplicate ids; websites that do not
start with https://; and the "Verified" counts from SOURCES.md. It exits with 1
if it finds duplicate ids or non-https websites, so it can be used as a check.
"""

import csv
import re
import sys
from collections import Counter
from pathlib import Path

IMPORTED_SOURCE = "ipeds"
DEFAULT_SOURCE = "estimate"       # a blank source means a hand-entered estimate (CONTRIBUTING.md)
PROGRAMS_VERIFIED = re.compile(r"Verified: (\d+) of (\d+) rows \(programs\)")
SCHOLARSHIPS_VERIFIED = re.compile(r"Scholarships verified: (\d+) of (\d+)")


# ---- Building the report ----

# Collect every number of the report into one dict. Keeping "work out the numbers" apart from
# "print them" lets the tests check the numbers directly, without reading printed text.
def build_report(data_dir) -> dict:
    data_dir = Path(data_dir)
    programs = _read_rows(data_dir / "programs.csv")
    scholarships = _read_rows(data_dir / "scholarships.csv")
    imported = [row for row in programs if _source(row) == IMPORTED_SOURCE]
    return {
        "programs": len(programs),
        "scholarships": len(scholarships),
        "by_source": Counter(_source(row) for row in programs),
        "by_degree": Counter(row.get("degree", "") for row in programs),
        "by_field": Counter(row.get("field", "") for row in programs),
        "imported": len(imported),
        "blank_in_imported": _blank_counts(imported),
        "duplicate_program_ids": _duplicates(row.get("program_id", "") for row in programs),
        "duplicate_scholarship_ids": _duplicates(row.get("scholarship_id", "") for row in scholarships),
        "non_https": sorted(_non_https(programs, "program_id") + _non_https(scholarships, "scholarship_id")),
        "verified": _verified_counts(data_dir / "SOURCES.md"),
    }


# A problem is something that must be fixed in the data: the same id twice, or a link that is
# not https. Blank cells are not problems: they mean "not published" (CONTRIBUTING.md).
def has_problems(report: dict) -> bool:
    return bool(report["duplicate_program_ids"] or report["duplicate_scholarship_ids"]
                or report["non_https"])


# Read a CSV file into a list of dicts, one per row, with every cell as trimmed text.
def _read_rows(path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as file:
        return [{key: (value or "").strip() for key, value in row.items() if key}
                for row in csv.DictReader(file)]


def _source(row: dict) -> str:
    return row.get("source") or DEFAULT_SOURCE


# For each column, how many of the rows leave it blank. Every column is listed, also the ones
# with 0 blanks, so the reader sees which columns are always filled in.
def _blank_counts(rows: list[dict]) -> dict[str, int]:
    columns = list(rows[0]) if rows else []
    return {column: sum(1 for row in rows if not row.get(column)) for column in columns}


# The ids that appear more than once, each listed once, in sorted order.
def _duplicates(ids) -> list[str]:
    counts = Counter(ids)
    return sorted(i for i, n in counts.items() if n > 1)


# The ids of rows whose website does not start with https:// (an empty website counts too).
def _non_https(rows: list[dict], id_column: str) -> list[str]:
    return [row.get(id_column, "") for row in rows if not row.get("website", "").startswith("https://")]


# The two "Verified: N of M" counts from the top of SOURCES.md, or None when the file or the
# line is missing. These count only the hand-entered rows that a person checked.
def _verified_counts(path) -> dict:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    programs = PROGRAMS_VERIFIED.search(text)
    scholarships = SCHOLARSHIPS_VERIFIED.search(text)
    return {"programs": tuple(map(int, programs.groups())) if programs else None,
            "scholarships": tuple(map(int, scholarships.groups())) if scholarships else None}


# ---- Printing the report ----

# Turn the numbers into plain text, one section per question, biggest groups first.
def format_report(report: dict) -> str:
    lines = [f"Programs: {report['programs']:,}    Scholarships: {report['scholarships']:,}", ""]
    lines += _counter_section("Programs by source", report["by_source"])
    lines += _counter_section("Programs by degree", report["by_degree"])
    lines += _counter_section(f"Programs by field ({len(report['by_field'])} fields)", report["by_field"])

    lines.append(f"Blank cells in the {report['imported']:,} imported (ipeds) rows "
                 "(blank = not published):")
    for column, blanks in report["blank_in_imported"].items():
        lines.append(f"  {column:<22}{blanks:>8,}  {_percent(blanks, report['imported'])}")
    lines.append("")

    lines.append(f"Duplicate program ids: {_list_or_none(report['duplicate_program_ids'])}")
    lines.append(f"Duplicate scholarship ids: {_list_or_none(report['duplicate_scholarship_ids'])}")
    lines.append(f"Websites not starting with https://: {_list_or_none(report['non_https'])}")
    lines.append("")

    verified = report["verified"]
    lines.append("Checked by hand on official pages (from SOURCES.md):")
    lines.append(f"  programs:     {_of(verified['programs'])} hand-entered rows")
    lines.append(f"  scholarships: {_of(verified['scholarships'])}")
    return "\n".join(lines)


def _counter_section(title: str, counts: Counter) -> list[str]:
    # most_common() sorts by count; ties keep the order the values were first seen.
    rows = [f"  {name or '(blank)':<40}{count:>8,}" for name, count in counts.most_common()]
    return [f"{title}:"] + rows + [""]


def _percent(part: int, whole: int) -> str:
    return f"{part / whole:.0%}" if whole else "-"


def _list_or_none(items: list[str]) -> str:
    return ", ".join(items) if items else "none"


def _of(pair) -> str:
    return f"{pair[0]} of {pair[1]}" if pair else "not found"


# ---- Command line ----

# python -m gradmatch.data_report [data_dir]. Exit code 0 = no problems, 1 = duplicate ids or
# non-https websites (so a script or CI can notice), 2 = wrong arguments.
def main(argv: list[str]) -> int:
    if len(argv) > 2:
        print("usage: python -m gradmatch.data_report [data_dir]")
        return 2
    report = build_report(argv[1] if len(argv) == 2 else "data")
    print(format_report(report))
    return 1 if has_problems(report) else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))
