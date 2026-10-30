from dataclasses import dataclass

from database import Program

SAFETY = "Safety"
MATCH = "Match"
REACH = "Reach"


@dataclass(frozen=True)
class Student:
    degree: str
    field: str
    gpa: float
    home_state: str
    budget: int
    states: tuple[str, ...] = ()


@dataclass(frozen=True)
class Result:
    program: Program
    cost: int
    chance: str


def yearly_cost(program: Program, home_state: str) -> int:
    if home_state == program.state:
        return program.tuition_in_state + program.living_cost
    return program.tuition_out_state + program.living_cost


def check_gpa(gpa: float) -> None:
    if gpa < 0 or gpa > 4:
        raise ValueError(f"GPA must be between 0 and 4, got {gpa}")


def chance(gpa: float, acceptance_rate: float) -> str:
    if acceptance_rate < 0.10:
        return REACH

    points = 0
    if acceptance_rate >= 0.60:
        points += 2
    elif acceptance_rate >= 0.25:
        points += 1

    if gpa >= 3.7:
        points += 1
    elif gpa < 3.0:
        points -= 1

    if points >= 2:
        return SAFETY
    if points == 1:
        return MATCH
    return REACH


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
        results.append(Result(program, cost, chance(student.gpa, program.acceptance_rate)))
    results.sort(key=lambda result: (result.cost, result.program.university))
    return results
