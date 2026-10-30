from dataclasses import dataclass
from datetime import date

SOON_DAYS = 14


@dataclass(frozen=True)
class Deadline:
    name: str
    date: date
    days_left: int
    soon: bool


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
