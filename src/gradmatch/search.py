from dataclasses import dataclass

from gradmatch.cost import funding, yearly_cost
from gradmatch.fit import chance, check_gpa
from gradmatch.models import Program, Student


@dataclass(frozen=True)
class Result:
    program: Program
    cost: int
    chance: str
    funding: str


def find_programs(programs: list[Program], student: Student) -> list[Result]:
    check_gpa(student.gpa)
    if student.budget < 0:
        raise ValueError("budget can't be negative")
    results = []
    for program in programs:
        if program.degree != student.degree or program.field != student.field:
            continue
        if student.states and program.state not in student.states:
            continue
        cost = yearly_cost(program, student.home_state)
        if cost > student.budget:
            continue
        results.append(Result(program, cost, chance(student.gpa, program.acceptance_rate),
                              funding(program)))
    results.sort(key=lambda result: (result.cost, result.program.university))
    if student.degree == "PhD":
        results.sort(key=lambda result: -(result.program.stipend or 0))
    return results

