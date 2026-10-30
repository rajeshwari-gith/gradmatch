"""Deadline urgency for programs and scholarships.

Rule (CONTRIBUTING.md): days_left = (deadline - today).days
  days_left < 0      -> "closed"
  0 <= days_left <= 14  -> "urgent"
  15 <= days_left <= 30 -> "soon"
  days_left > 30     -> "later"

The warning window (14 days by default) can be set from 0 to 90 days with
`urgent_days`. glance_counts() gives the four numbers of the "at a glance" row.

A CustomDeadline is a deadline the student types in themselves (for example a
recommendation letter due date). It works everywhere a program or scholarship
deadline does: deadline_of, upcoming, glance_counts and exports.to_ics.

`today` is always passed in by the caller; this module never calls
date.today(), so tests can use any fixed date.
"""
# In plain words: students miss deadlines, so the app labels each one as closed, urgent
# (two weeks or less), soon (one month or less) or later, and lists the open ones in date order.
# Why `today` is passed in instead of read inside: if the code called date.today() itself, a
# test written today would give a different answer next week. Passing the date in lets every
# test use a fixed day, and lets the app show "as of" any date for a demo.

from dataclasses import dataclass
from datetime import date, datetime

from gradmatch.models import Program, Scholarship


# A deadline the student adds by hand. It is not in any data file; the screen keeps it.
# frozen=True like the shared models, so a deadline cannot change after it is made.
@dataclass(frozen=True)
class CustomDeadline:
    name: str                 # e.g. "Recommendation letters for MSU"
    deadline: date
    website: str = ""         # optional link
    note: str = ""            # optional short note


DATE_FORMAT = "%Y-%m-%d"

# The four labels the app shows, kept as constants so a typo cannot create a fifth one.
CLOSED = "closed"
URGENT = "urgent"
SOON = "soon"
LATER = "later"

# The cut-offs in days. Day 14 is still urgent and day 30 is still soon; the boundary tests
# check -1, 0, 14, 15, 30 and 31 days so an off-by-one mistake would be caught.
URGENT_MAX_DAYS = 14
SOON_MAX_DAYS = 30
# The longest warning window a student can choose, and the "within 90 days" count.
GLANCE_DAYS = 90


# Count the days left and pick the label. Due today (0 days) is urgent, not closed, because
# the student can still apply. Counting whole days with dates (not hours) also gets leap years right.
# urgent_days is the student's warning window: with 7, a deadline in 10 days is "soon" instead of
# "urgent". With a window of 30 days or more there is no "soon" left: it is urgent or later.
def deadline_status(deadline: date, today: date, urgent_days: int = URGENT_MAX_DAYS) -> str:
    _check_window(urgent_days)
    days_left = (deadline - today).days
    if days_left < 0:
        return CLOSED
    if days_left <= urgent_days:
        return URGENT
    if days_left <= SOON_MAX_DAYS:
        return SOON
    return LATER


# The list for the Deadlines tab and the calendar: drop programs with no published deadline
# (None cannot be compared to a date), drop closed ones, and sort the rest soonest first.
def upcoming(items: list[Program | Scholarship | CustomDeadline],
             today: date) -> list[Program | Scholarship | CustomDeadline]:
    """Return the items that are not closed, earliest deadline first.

    Items can be Programs, Scholarships, CustomDeadlines, or a mix. A program whose
    deadline is not published (None) is left out.
    """
    dated = [item for item in items if deadline_of(item) is not None]
    still_open = [item for item in dated if deadline_status(deadline_of(item), today) != CLOSED]
    return sorted(still_open, key=deadline_of)


# The four numbers of the "at a glance" row. A deadline due today counts as open (0 days left).
# "within_90" includes the warning window, so with the default window a deadline in 5 days is
# counted in both "within_window" and "within_90". "later" is more than 90 days away, "passed" is
# before today. Programs with no published deadline are not counted anywhere.
def glance_counts(items: list[Program | Scholarship | CustomDeadline], today: date,
                  urgent_days: int = URGENT_MAX_DAYS) -> dict:
    """Return {"within_window", "within_90", "later", "passed"} counts for the dated items."""
    _check_window(urgent_days)
    counts = {"within_window": 0, "within_90": 0, "later": 0, "passed": 0}
    for item in items:
        deadline = deadline_of(item)
        if deadline is None:
            continue                         # not published: nothing to count
        days_left = (deadline - today).days
        if days_left < 0:
            counts["passed"] += 1
        elif days_left > GLANCE_DAYS:
            counts["later"] += 1
        else:
            counts["within_90"] += 1
            if days_left <= urgent_days:
                counts["within_window"] += 1
    return counts


# The window must be a whole number from 0 to 90 days. A window longer than 90 days would count
# more deadlines "within the window" than "within 90 days", which makes no sense on screen.
# bool is refused too: True is an int in Python, but "a window of True days" is a mistake.
def _check_window(urgent_days: int):
    if (not isinstance(urgent_days, int) or isinstance(urgent_days, bool)
            or not 0 <= urgent_days <= GLANCE_DAYS):
        raise ValueError(f"urgent_days must be a whole number from 0 to {GLANCE_DAYS}, got {urgent_days!r}")


# Programs and scholarships name their deadline field differently. This one helper hides
# that, so the code above can treat both the same way. Scholarships and custom deadlines both
# call it `deadline`.
def deadline_of(item: Program | Scholarship | CustomDeadline) -> date | None:
    """Programs call their deadline application_deadline; scholarships and custom deadlines call it deadline.

    A program's deadline is None when it is not published.
    """
    if isinstance(item, Program):
        return item.application_deadline
    return item.deadline


# Check what the student typed before a CustomDeadline is made, and return every problem (an
# empty list means it is fine), like validate_profile does for the profile form. `day` can be a
# date from a date picker or text in YYYY-MM-DD; "2026-02-30" is not a real date and is refused.
def validate_custom_deadline(name, day) -> list[str]:
    """Return the problems with a custom deadline's name and date; [] if both are fine."""
    errors = []
    if not isinstance(name, str) or not name.strip():
        errors.append("Name is required.")
    if not _is_real_date(day):
        errors.append("Date must be a real date (YYYY-MM-DD).")
    return errors


def _is_real_date(day) -> bool:
    if isinstance(day, datetime):
        return False                     # a date and time, not a day
    if isinstance(day, date):
        return True
    try:
        datetime.strptime(day, DATE_FORMAT)
        return True
    except (TypeError, ValueError):
        return False
