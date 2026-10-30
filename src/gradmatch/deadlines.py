from dataclasses import dataclass
from datetime import date

from gradmatch.models import Scholarship

SOON_DAYS = 14


@dataclass(frozen=True)
class Deadline:
    name: str
    date: date
    days_left: int
    soon: bool


def today() -> date:
    return date.today()


def upcoming(scholarships: list[Scholarship], today: date) -> list[Deadline]:
    deadlines = []
    for s in scholarships:
        days_left = (s.deadline - today).days
        if days_left < 0:
            continue
        deadlines.append(Deadline(s.name, s.deadline, days_left, days_left <= SOON_DAYS))
    deadlines.sort(key=lambda d: d.date)
    return deadlines
