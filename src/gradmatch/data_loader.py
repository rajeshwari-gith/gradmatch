import csv
from datetime import date

from gradmatch.models import Program, Scholarship


class DataError(Exception):
    pass


def check_row(row: dict, optional=()) -> None:
    # DictReader uses None for missing values and as the key for extra ones
    if None in row.values() or None in row:
        raise ValueError("wrong number of values")
    for column, value in row.items():
        if column not in optional and not value.strip():
            raise ValueError(f"{column} is empty")


def parse_program(row: dict) -> Program:
    check_row(row, optional=("stipend",))
    program = Program(
        university=row["university"].strip(),
        program=row["program"].strip(),
        degree=row["degree"].strip(),
        field=row["field"].strip(),
        state=row["state"].strip(),
        tuition_in_state=int(row["tuition_in_state"]),
        tuition_out_state=int(row["tuition_out_state"]),
        living_cost=int(row["living_cost"]),
        acceptance_rate=float(row["acceptance_rate"]),
        stipend=int(row["stipend"]) if row["stipend"].strip() else None,
        website=row["website"].strip(),
    )
    if program.degree not in ("MS", "PhD"):
        raise ValueError(f"degree must be MS or PhD, got {program.degree}")
    if min(program.tuition_in_state, program.tuition_out_state, program.living_cost,
           program.stipend or 0) < 0:
        raise ValueError("costs can't be negative")
    if not 0 <= program.acceptance_rate <= 1:
        raise ValueError(f"acceptance_rate must be between 0 and 1, got {program.acceptance_rate}")
    return program


def parse_scholarship(row: dict) -> Scholarship:
    check_row(row)
    scholarship = Scholarship(
        name=row["name"].strip(),
        amount=int(row["amount"]),
        degrees=tuple(row["degrees"].split(";")),
        fields=tuple(row["fields"].split(";")),
        min_gpa=float(row["min_gpa"]),
        citizenship=tuple(row["citizenship"].split(";")),
        deadline=date.fromisoformat(row["deadline"]),
        website=row["website"].strip(),
    )
    if scholarship.amount < 0:
        raise ValueError("amount can't be negative")
    if not 0 <= scholarship.min_gpa <= 4:
        raise ValueError(f"min_gpa must be between 0 and 4, got {scholarship.min_gpa}")
    return scholarship


def load(path, parse) -> list:
    items = []
    with open(path, newline="", encoding="utf-8") as file:
        for line, row in enumerate(csv.DictReader(file), start=2):
            try:
                items.append(parse(row))
            except (KeyError, ValueError) as error:
                raise DataError(f"{path}, line {line}: {error}") from error
    return items


def load_programs(path) -> list[Program]:
    return load(path, parse_program)


def load_scholarships(path) -> list[Scholarship]:
    return load(path, parse_scholarship)
