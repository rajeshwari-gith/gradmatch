"""Deadline urgency for programs and scholarships.

Rule (CONTRIBUTING.md): days_left = (deadline - today).days
  days_left < 0      -> "closed"
  0 <= days_left <= 14  -> "urgent"
  15 <= days_left <= 30 -> "soon"
  days_left > 30     -> "later"

`today` is always passed in by the caller; this module never calls
date.today(), so tests can use any fixed date.
"""
# In plain words: students miss deadlines, so the app labels each one as closed, urgent
# (two weeks or less), soon (one month or less) or later, and lists the open ones in date order.
# Why `today` is passed in instead of read inside: if the code called date.today() itself, a
# test written today would give a different answer next week. Passing the date in lets every
# test use a fixed day, and lets the app show "as of" any date for a demo.

from datetime import date

from gradmatch.models import Program, Scholarship

# The four labels the app shows, kept as constants so a typo cannot create a fifth one.
CLOSED = "closed"
URGENT = "urgent"
SOON = "soon"
LATER = "later"

# The cut-offs in days. Day 14 is still urgent and day 30 is still soon; the boundary tests
# check -1, 0, 14, 15, 30 and 31 days so an off-by-one mistake would be caught.
URGENT_MAX_DAYS = 14
SOON_MAX_DAYS = 30


# Count the days left and pick the label. Due today (0 days) is urgent, not closed, because
# the student can still apply. Counting whole days with dates (not hours) also gets leap years right.
def deadline_status(deadline: date, today: date) -> str:
    days_left = (deadline - today).days
    if days_left < 0:
        return CLOSED
    if days_left <= URGENT_MAX_DAYS:
        return URGENT
    if days_left <= SOON_MAX_DAYS:
        return SOON
    return LATER


# The list for the Deadlines tab and the calendar: drop programs with no published deadline
# (None cannot be compared to a date), drop closed ones, and sort the rest soonest first.
def upcoming(items: list[Program | Scholarship], today: date) -> list[Program | Scholarship]:
    """Return the items that are not closed, earliest deadline first.

    Items can be Programs, Scholarships, or a mix of both. A program whose
    deadline is not published (None) is left out.
    """
    dated = [item for item in items if deadline_of(item) is not None]
    still_open = [item for item in dated if deadline_status(deadline_of(item), today) != CLOSED]
    return sorted(still_open, key=deadline_of)


# Programs and scholarships name their deadline field differently. This one helper hides
# that, so the code above can treat both the same way.
def deadline_of(item: Program | Scholarship) -> date | None:
    """Programs call their deadline application_deadline; scholarships call it deadline.

    A program's deadline is None when it is not published.
    """
    if isinstance(item, Program):
        return item.application_deadline
    return item.deadline
