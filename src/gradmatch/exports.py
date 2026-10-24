"""Export search results as CSV and deadlines as an iCalendar (.ics) file.

to_csv() turns ProgramResults into spreadsheet text. The csv module does
the quoting, so names with commas or quotes stay in one cell.

to_ics() turns Program and Scholarship deadlines into calendar text that
calendar apps can import. It follows the parts of RFC 5545 we need:
lines end in CRLF, text values are escaped, and long lines are folded.
The DTSTAMP time is passed in by the caller; this module never calls now().
"""
import csv
import io
from datetime import datetime, timezone

from gradmatch.deadlines import deadline_of
from gradmatch.models import Program, Scholarship
from gradmatch.search import ProgramResult

CSV_COLUMNS = ["university", "program", "degree", "state", "yearly_cost", "total_cost",
               "fit", "funding", "deadline", "website"]

CRLF = "\r\n"
MAX_LINE_BYTES = 75     # RFC 5545: lines longer than 75 bytes must be folded
PRODID = "-//GradMatch//Deadlines//EN"


# ---- CSV ----

def to_csv(results: list[ProgramResult]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_COLUMNS)
    for result in results:
        program = result.program
        writer.writerow([
            program.university,
            program.program_name,
            program.degree,
            program.state,
            f"{result.yearly_cost:.2f}",
            f"{result.total_cost:.2f}",
            result.fit,
            result.funding,
            program.application_deadline.isoformat(),
            program.website,
        ])
    return buffer.getvalue()


# ---- iCalendar ----

def to_ics(items: list[Program | Scholarship], stamp: datetime) -> str:
    """Return a calendar with one all-day event per deadline."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:{PRODID}", "CALSCALE:GREGORIAN"]
    for item in items:
        lines += _event_lines(item, stamp)
    lines.append("END:VCALENDAR")
    # Every line, including the last, ends with CRLF.
    return "".join(_fold(line) + CRLF for line in lines)


def _event_lines(item: Program | Scholarship, stamp: datetime) -> list[str]:
    if isinstance(item, Program):
        uid = f"program-{item.program_id}@gradmatch"
        summary = f"Application deadline: {item.university} – {item.program_name}"
    else:
        uid = f"scholarship-{item.scholarship_id}@gradmatch"
        summary = f"Scholarship deadline: {item.name}"
    return [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{_utc_stamp(stamp)}",
        f"DTSTART;VALUE=DATE:{deadline_of(item):%Y%m%d}",
        f"SUMMARY:{_escape_text(summary)}",
        f"URL:{item.website}",
        "END:VEVENT",
    ]


def _utc_stamp(stamp: datetime) -> str:
    """Format as UTC, e.g. 20261024T150000Z. A time without a zone is taken as UTC."""
    if stamp.tzinfo is not None:
        stamp = stamp.astimezone(timezone.utc)
    return stamp.strftime("%Y%m%dT%H%M%SZ")


def _escape_text(text: str) -> str:
    """Escape a TEXT value: backslash first, then ; , and newlines."""
    text = text.replace("\\", "\\\\")
    text = text.replace(";", "\\;").replace(",", "\\,")
    return text.replace("\r\n", "\\n").replace("\n", "\\n")


def _fold(line: str) -> str:
    """Split a line longer than 75 bytes; each extra part starts with a space.

    The limit counts UTF-8 bytes, and a character is never cut in half.
    A continuation line holds 74 bytes, because its leading space is the 75th.
    """
    parts = []
    current = ""
    limit = MAX_LINE_BYTES
    for char in line:
        if len((current + char).encode("utf-8")) > limit:
            parts.append(current)
            current = char
            limit = MAX_LINE_BYTES - 1
        else:
            current += char
    parts.append(current)
    return (CRLF + " ").join(parts)
