"""Deadline urgency for programs and scholarships.

Rule (CLAUDE.md): days_left = (deadline - today).days
  days_left < 0      -> "closed"
  0 <= days_left <= 14  -> "urgent"
  15 <= days_left <= 30 -> "soon"
  days_left > 30     -> "later"

`today` is always passed in by the caller; this module never calls
date.today(), so tests can use any fixed date.
"""
from datetime import date

from gradmatch.models import Program, Scholarship

CLOSED = "closed"
URGENT = "urgent"
SOON = "soon"
LATER = "later"

URGENT_MAX_DAYS = 14
SOON_MAX_DAYS = 30


def deadline_status(deadline: date, today: date) -> str:
    days_left = (deadline - today).days
    if days_left < 0:
        return CLOSED
    if days_left <= URGENT_MAX_DAYS:
        return URGENT
    if days_left <= SOON_MAX_DAYS:
        return SOON
    return LATER


def upcoming(items: list[Program | Scholarship], today: date) -> list[Program | Scholarship]:
    """Return the items that are not closed, earliest deadline first.

    Items can be Programs, Scholarships, or a mix of both.
    """
    still_open = [item for item in items if deadline_status(deadline_of(item), today) != CLOSED]
    return sorted(still_open, key=deadline_of)


def deadline_of(item: Program | Scholarship) -> date:
    """Programs call their deadline application_deadline; scholarships call it deadline."""
    if isinstance(item, Program):
        return item.application_deadline
    return item.deadline
