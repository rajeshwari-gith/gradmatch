import csv

from gradmatch.models import Program


class DataError(Exception):
    pass


def parse_row(row: dict) -> Program:
    # DictReader uses None for missing values and as the key for extra ones
    if None in row.values() or None in row:
        raise ValueError("wrong number of values")
    program = Program(
        university=row["university"].strip(),
        program=row["program"].strip(),
        field=row["field"].strip(),
        state=row["state"].strip(),
        tuition_in_state=int(row["tuition_in_state"]),
        tuition_out_state=int(row["tuition_out_state"]),
        living_cost=int(row["living_cost"]),
        avg_gpa=float(row["avg_gpa"]),
        website=row["website"].strip(),
    )
    if not program.university or not program.program or not program.field:
        raise ValueError("university, program and field can't be empty")
    if min(program.tuition_in_state, program.tuition_out_state, program.living_cost) < 0:
        raise ValueError("costs can't be negative")
    if not 0 <= program.avg_gpa <= 4:
        raise ValueError(f"avg_gpa must be between 0 and 4, got {program.avg_gpa}")
    return program


def load_programs(path) -> list[Program]:
    programs = []
    with open(path, newline="", encoding="utf-8") as file:
        for line, row in enumerate(csv.DictReader(file), start=2):
            try:
                programs.append(parse_row(row))
            except (KeyError, ValueError) as error:
                raise DataError(f"{path}, line {line}: {error}") from error
    return programs
