from dataclasses import dataclass

from gradmatch.cost import yearly_cost
from gradmatch.fit import chance, check_gpa
from gradmatch.models import Program, Student


@dataclass(frozen=True)
class Result:
    program: Program
    cost: int
    chance: str


def find_programs(programs: list[Program], student: Student) -> list[Result]:
    check_gpa(student.gpa)
    if student.budget < 0:
        raise ValueError("budget can't be negative")
    results = []
    for program in programs:
        if program.field != student.field:
            continue
        cost = yearly_cost(program, student.home_state)
        if cost > student.budget:
            continue
        results.append(Result(program, cost, chance(student.gpa, program.avg_gpa)))
    results.sort(key=lambda r: (r.cost, r.program.university))
    return results


def fields(programs: list[Program]) -> list[str]:
    return sorted({program.field for program in programs})
