"""Load the CSV files in data/ into the shared models.

There is one loader per file. Each one reads every row, converts the text
cells to the right types and checks the business limits. A bad row raises
DataError with the file name, the line number and the problem, so whoever
edits the data can find and fix it quickly.
"""
import csv
from dataclasses import fields
from datetime import date, datetime

from gradmatch.models import Program, Scholarship

DEGREES = ("MS", "PhD")
GPA_MIN, GPA_MAX = 0.0, 4.0
RATE_MIN, RATE_MAX = 0.0, 1.0
DATE_FORMAT = "%Y-%m-%d"
LIVING_COST_COLUMNS = ["state", "annual_living_cost"]


class DataError(ValueError):
    """Raised when a CSV file or one of its rows is invalid."""


# ---- Public loaders ----

def load_programs(path) -> list[Program]:
    columns = [f.name for f in fields(Program)]
    return _load(path, columns, _to_program)


def load_scholarships(path) -> list[Scholarship]:
    columns = [f.name for f in fields(Scholarship)]
    return _load(path, columns, _to_scholarship)


def load_living_costs(path) -> dict[str, float]:
    """Return {state code: yearly living cost in USD}."""
    pairs = _load(path, LIVING_COST_COLUMNS, _to_living_cost)
    return dict(pairs)


# ---- Reading the file ----

def _load(path, columns, convert) -> list:
    """Read the CSV at path and convert every row with convert(row).

    Raises DataError if a column is missing, or if convert() raises a
    ValueError for a row (the line number is added to the message).
    """
    results = []
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        header = reader.fieldnames or []
        missing = [name for name in columns if name not in header]
        if missing:
            raise DataError(f"{path}: missing column(s): {', '.join(missing)}")

        for row in reader:
            # reader.line_num is the line just read; line 1 is the header.
            try:
                results.append(convert(row))
            except ValueError as error:
                raise DataError(f"{path}, line {reader.line_num}: {error}") from error
    return results


# ---- Converting one row ----

def _to_program(row) -> Program:
    degree = _degree(_text(row, "degree"))
    avg_gpa = _in_range(_number(row, "avg_gpa"), GPA_MIN, GPA_MAX, "avg_gpa")
    rate = _in_range(_number(row, "acceptance_rate"), RATE_MIN, RATE_MAX, "acceptance_rate")
    return Program(
        program_id=_text(row, "program_id"),
        university=_text(row, "university"),
        program_name=_text(row, "program_name"),
        field=_text(row, "field"),
        degree=degree,
        state=_text(row, "state"),
        tuition_in_state=_number(row, "tuition_in_state"),
        tuition_out_state=_number(row, "tuition_out_state"),
        duration_years=_number(row, "duration_years"),
        avg_gpa=avg_gpa,
        avg_gre=_optional_int(row, "avg_gre"),
        acceptance_rate=rate,
        stipend=_number(row, "stipend"),
        min_toefl=_optional_int(row, "min_toefl"),
        application_deadline=_date(row, "application_deadline"),
        website=_text(row, "website"),
    )


def _to_scholarship(row) -> Scholarship:
    degree_levels = tuple(_degree(level) for level in _list(row, "degree_levels"))
    if not degree_levels:
        raise ValueError("degree_levels is required")
    min_gpa = _in_range(_number(row, "min_gpa"), GPA_MIN, GPA_MAX, "min_gpa")
    return Scholarship(
        scholarship_id=_text(row, "scholarship_id"),
        name=_text(row, "name"),
        type=_text(row, "type"),
        amount=_number(row, "amount"),
        degree_levels=degree_levels,
        fields=_list(row, "fields"),
        min_gpa=min_gpa,
        citizenship=_list(row, "citizenship"),
        states=_list(row, "states"),
        special=_list(row, "special"),       # may be empty: no special requirement
        deadline=_date(row, "deadline"),
        website=_text(row, "website"),
    )


def _to_living_cost(row) -> tuple[str, float]:
    cost = _number(row, "annual_living_cost")
    if cost < 0:
        raise ValueError(f"annual_living_cost cannot be negative, got {cost}")
    return _text(row, "state"), cost


# ---- Small helpers for single cells ----

def _cell(row, name) -> str:
    # A short row gives None for the missing cells, so treat None as "".
    return (row[name] or "").strip()


def _text(row, name) -> str:
    value = _cell(row, name)
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _number(row, name) -> float:
    value = _text(row, name)
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"{name} must be a number, got '{value}'") from None


def _optional_int(row, name) -> int | None:
    value = _cell(row, name)
    if not value:
        return None             # empty cell = None (CLAUDE.md)
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"{name} must be a whole number, got '{value}'") from None


def _date(row, name) -> date:
    value = _text(row, name)
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError:
        raise ValueError(f"{name} must be a real date in YYYY-MM-DD format, got '{value}'") from None


def _list(row, name) -> tuple[str, ...]:
    """Split a ';' list cell, e.g. 'MS;PhD' -> ('MS', 'PhD'). Empty cell -> ()."""
    return tuple(item.strip() for item in _cell(row, name).split(";") if item.strip())


def _degree(value) -> str:
    if value not in DEGREES:
        raise ValueError(f"degree must be MS or PhD, got '{value}'")
    return value


def _in_range(value, low, high, name) -> float:
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}, got {value}")
    return value
