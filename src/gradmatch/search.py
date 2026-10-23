"""Find the programs that fit a student's profile.

search_programs() keeps a program only if:
- its field and degree match what the student is looking for,
- it is in one of the student's preferred states (or any state if none
  are chosen), and
- its yearly cost fits the student's yearly budget.

Each result carries its cost, Reach/Match/Safety label and funding label.
MS results are sorted cheapest first; PhD results are sorted by how much
the stipend is left after living costs (best funded first).
"""
from dataclasses import dataclass

from gradmatch.cost import total_cost, yearly_cost
from gradmatch.fit import classify_fit
from gradmatch.funding import funding_label
from gradmatch.models import Program, StudentProfile


@dataclass(frozen=True)
class ProgramResult:
    program: Program
    yearly_cost: float
    total_cost: float
    fit: str
    funding: str


def matches_filters(profile: StudentProfile, program: Program) -> bool:
    if program.field != profile.field:
        return False
    if program.degree != profile.degree_sought:
        return False
    if profile.preferred_states and program.state not in profile.preferred_states:
        return False
    return True


def search_programs(profile: StudentProfile, programs: list[Program],
                    living_costs: dict[str, float]) -> list[ProgramResult]:
    results = []
    for program in programs:
        if not matches_filters(profile, program):
            continue
        if program.state not in living_costs:
            raise ValueError(f"No living cost found for state {program.state}.")
        living = living_costs[program.state]
        cost = yearly_cost(program, profile.home_state, living)
        if cost > profile.annual_budget:
            continue
        results.append(ProgramResult(
            program=program,
            yearly_cost=cost,
            total_cost=total_cost(program, profile.home_state, living),
            fit=classify_fit(profile.gpa, program),
            funding=funding_label(program, living),
        ))

    if profile.degree_sought == "PhD":
        results.sort(key=lambda r: (-(r.program.stipend - living_costs[r.program.state]),
                                    r.program.university))
    else:
        results.sort(key=lambda r: (r.yearly_cost, r.program.university))
    return results
