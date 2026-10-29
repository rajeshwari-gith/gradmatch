"""Find the programs that fit a student's profile.

search_programs() keeps a program only if:
- its field and degree match what the student is looking for,
- it is in one of the student's preferred states (or any state if none
  are chosen), and
- its yearly cost fits the student's yearly budget, and
- a Reach/Match/Safety chance can be given (a program with no average GPA and no
  acceptance rate, for itself or its university, is left out).

Each result carries its cost, Reach/Match/Safety label and funding label.
MS results are sorted cheapest first; PhD results are sorted by how much
the stipend is left after living costs (best funded first).
"""
from dataclasses import dataclass

from gradmatch.cost import known_stipend, total_cost, yearly_cost
from gradmatch.fit import UNKNOWN, classify_fit
from gradmatch.funding import funding_label
from gradmatch.models import Program, StudentProfile


@dataclass(frozen=True)
class ProgramResult:
    program: Program
    yearly_cost: float
    total_cost: float
    fit: str
    funding: str


def tuition_state(profile: StudentProfile) -> str | None:
    """The state whose in-state tuition rate applies to this student, or None.

    International students are not residents of any state, so they always pay
    the out-of-state rate, whatever home state they chose.
    """
    if profile.citizenship == "International":
        return None
    return profile.home_state


def matches_filters(profile: StudentProfile, program: Program) -> bool:
    # The cheap yes/no checks come first. A program must be the same field and degree,
    # and (if the student picked states) be in one of those states.
    if program.field != profile.field:
        return False
    if program.degree != profile.degree_sought:
        return False
    if profile.preferred_states and program.state not in profile.preferred_states:
        return False
    return True


def school_rates(programs: list[Program]) -> dict[tuple[str, str], float]:
    """Each university's overall acceptance rate, keyed by (university, state).

    Official data publishes it on the university's bachelor's rows; graduate rows of the same
    university borrow it when they have no rate of their own.
    """
    return {(p.university, p.state): p.acceptance_rate for p in programs
            if p.degree == "BS" and p.acceptance_rate is not None}


def search_programs(profile: StudentProfile, programs: list[Program],
                    living_costs: dict[str, float]) -> list[ProgramResult]:
    rates = school_rates(programs)
    results = []
    for program in programs:
        if not matches_filters(profile, program):
            continue
        # Every state in the data must have a living cost. Failing loudly beats silently
        # showing a wrong price.
        if program.state not in living_costs:
            raise ValueError(f"No living cost found for state {program.state}.")
        living = living_costs[program.state]
        cost = yearly_cost(program, tuition_state(profile), living)
        # Too expensive for this student's yearly budget: leave it out of the results.
        if cost > profile.annual_budget:
            continue
        fit = classify_fit(profile.gpa, program, profile.sat, profile.act,
                           rates.get((program.university, program.state)))
        # No chance can be given at all: leave it out rather than show "Unknown".
        if fit == UNKNOWN:
            continue
        results.append(ProgramResult(
            program=program,
            yearly_cost=cost,
            total_cost=total_cost(program, tuition_state(profile), living),
            fit=fit,
            funding=funding_label(program, living),
        ))

    # Sorting: a PhD student cares about money left after living costs, so best funded first.
    # Everyone else sees the cheapest first. Ties are broken by university name so the order is stable.
    if profile.degree_sought == "PhD":
        results.sort(key=lambda r: (-(known_stipend(r.program) - living_costs[r.program.state]),
                                    r.program.university))
    else:
        results.sort(key=lambda r: (r.yearly_cost, r.program.university))
    return results
