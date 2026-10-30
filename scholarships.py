from dataclasses import dataclass
from datetime import date

from database import Scholarship
from programs import Student

SOON_DAYS = 14


@dataclass(frozen=True)
class Deadline:
    name: str
    date: date
    days_left: int
    soon: bool


def qualifies(scholarship: Scholarship, student: Student) -> bool:
    if student.degree not in scholarship.degrees:
        return False
    if "Any" not in scholarship.fields and student.field not in scholarship.fields:
        return False
    return student.gpa >= scholarship.min_gpa


def find_scholarships(scholarships: list[Scholarship], student: Student) -> list[Scholarship]:
    found = [s for s in scholarships if qualifies(s, student)]
    found.sort(key=lambda s: (-s.amount, s.name))
    return found


def today() -> date:
    return date.today()


def upcoming(dates: list[tuple[str, date]], today: date) -> list[Deadline]:
    deadlines = []
    for name, day in dates:
        days_left = (day - today).days
        if days_left < 0:
            continue
        deadlines.append(Deadline(name, day, days_left, days_left <= SOON_DAYS))
    deadlines.sort(key=lambda d: d.date)
    return deadlines
