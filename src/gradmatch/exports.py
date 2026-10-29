"""Export search results as CSV and deadlines as an iCalendar (.ics) file.

to_csv() turns ProgramResults into spreadsheet text. The csv module does
the quoting, so names with commas or quotes stay in one cell.

A value that is not published (None) becomes an empty CSV cell.

to_ics() turns Program, Scholarship and CustomDeadline deadlines into calendar
text that calendar apps can import; a program with no published deadline is left out. It follows the parts of RFC 5545 we need:
lines end in CRLF, text values are escaped, and long lines are folded.
The DTSTAMP time is passed in by the caller; this module never calls now().
"""
# In plain words: students want to keep their results. This file makes two downloads: a CSV
# file of the programs (opens in Excel or Google Sheets) and an .ics file of the deadlines
# (opens in Google Calendar, Outlook or Apple Calendar). Both are plain text built here, so they
# can be unit tested without the app.

import csv
import io
import re
from datetime import date, datetime, timezone

from gradmatch.deadlines import CustomDeadline, deadline_of
from gradmatch.models import Program, Scholarship
from gradmatch.search import ProgramResult

# The columns of the CSV download, in the order the student sees them.
CSV_COLUMNS = ["university", "program", "degree", "state", "yearly_cost", "total_cost",
               "fit", "funding", "deadline", "website"]

# The calendar standard (RFC 5545) says every line ends with \r\n. Some calendar apps
# may reject a file that uses only \n, so we follow the rule exactly.
CRLF = "\r\n"
MAX_LINE_BYTES = 75     # RFC 5545: lines longer than 75 bytes must be folded
PRODID = "-//GradMatch//Deadlines//EN"


# ---- CSV ----

# Build the CSV text. The csv module adds quotes when a name has a comma or a quote in it,
# so "Computer Science, Data Track" stays in one cell instead of shifting every column.
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
            _money_cell(result.yearly_cost),
            _money_cell(result.total_cost),
            result.fit,
            result.funding,
            _date_cell(program.application_deadline),
            program.website,
        ])
    return buffer.getvalue()


# A money cell: two decimals, or an empty cell when the value is not published (never 0).
def _money_cell(amount: float | None) -> str:
    return "" if amount is None else f"{amount:.2f}"


# A date cell as YYYY-MM-DD, which spreadsheets sort correctly; empty when not published.
def _date_cell(day: date | None) -> str:
    return "" if day is None else day.isoformat()


# ---- iCalendar ----

# Build the calendar text. `stamp` (the time the file was made) is passed in for the same
# reason as `today` in deadlines.py: the tests can use a fixed time and get the same file every run.
def to_ics(items: list[Program | Scholarship | CustomDeadline], stamp: datetime) -> str:
    """Return a calendar with one all-day event per deadline."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:{PRODID}", "CALSCALE:GREGORIAN"]
    for item in items:
        if deadline_of(item) is not None:      # no published deadline: no event
            lines += _event_lines(item, stamp)
    lines.append("END:VCALENDAR")
    # Every line, including the last, ends with CRLF.
    return "".join(_fold(line) + CRLF for line in lines)


# One all-day calendar event for one deadline. The UID stays the same every time the file
# is made, so importing it again updates the event instead of adding a copy. The "program-",
# "scholarship-" and "deadline-" prefixes stop items of different kinds from clashing.
# A custom deadline has no id, so its UID is made from its date and name; it gets a URL line
# only if the student gave a link, and its note becomes the event's description.
def _event_lines(item: Program | Scholarship | CustomDeadline, stamp: datetime) -> list[str]:
    extra = []
    if isinstance(item, Program):
        uid = f"program-{item.program_id}@gradmatch"
        summary = f"Application deadline: {item.university} – {item.program_name}"
    elif isinstance(item, Scholarship):
        uid = f"scholarship-{item.scholarship_id}@gradmatch"
        summary = f"Scholarship deadline: {item.name}"
    else:
        uid = f"deadline-{item.deadline:%Y%m%d}-{_slug(item.name)}@gradmatch"
        summary = f"Deadline: {item.name}"
        if item.note:
            extra.append(f"DESCRIPTION:{_escape_text(item.note)}")
    if item.website:
        extra.append(f"URL:{item.website}")
    return [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{_utc_stamp(stamp)}",
        f"DTSTART;VALUE=DATE:{deadline_of(item):%Y%m%d}",
        f"SUMMARY:{_escape_text(summary)}",
        *extra,
        "END:VEVENT",
    ]


# A name made safe for a UID: lower case, and every run of other characters becomes one "-".
# "Rec letters, MSU!" -> "rec-letters-msu".
def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# Calendar times must say their time zone. We always write UTC (the Z at the end), so the
# file is the same whichever time zone the server runs in.
def _utc_stamp(stamp: datetime) -> str:
    """Format as UTC, e.g. 20261024T150000Z. A time without a zone is taken as UTC."""
    if stamp.tzinfo is not None:
        stamp = stamp.astimezone(timezone.utc)
    return stamp.strftime("%Y%m%dT%H%M%SZ")


# In a calendar file ; and , are separators and a real line break would end the line, so
# they get a backslash in front. The backslash itself is escaped first; doing it last would
# double the backslashes we just added.
def _escape_text(text: str) -> str:
    """Escape a TEXT value: backslash first, then ; , and newlines."""
    text = text.replace("\\", "\\\\")
    text = text.replace(";", "\\;").replace(",", "\\,")
    # A lone \r (no \n after it) is a line break too; it is escaped the same way (defect D-004).
    return text.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")


# Why fold: the calendar standard says no line may be longer than 75 bytes, and some apps may
# cut or reject longer ones. A long program name is split, and each extra piece starts with a space,
# which tells the calendar app to glue the pieces back together. We count bytes, not letters,
# because letters like é take 2 bytes, and we never cut one of those in half.
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
