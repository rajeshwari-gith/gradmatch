"""Work out what a program costs a student.

Rules (see CONTRIBUTING.md):
- In-state tuition if the student's home state is the program's state,
  otherwise out-of-state tuition.
- A PhD program that pays a stipend (stipend > 0) waives tuition, so the
  student is charged no tuition. MS programs always charge tuition.
- An unpublished stipend (None) counts as 0, the cautious choice, so tuition is not waived.
- Yearly cost = tuition charged + living cost of the program's state - stipend,
  and never below 0.
"""
from gradmatch.models import Program


def tuition_for(program: Program, home_state: str | None) -> float:
    """In-state rate if home_state is the program's state; None means no state (out-of-state)."""
    # Public universities charge residents of their own state less. home_state is None for
    # international students (see search.tuition_state), so they never get the cheap rate.
    if home_state is not None and home_state == program.state:
        return program.tuition_in_state
    return program.tuition_out_state


def known_stipend(program: Program) -> float:
    """The stipend, counting an unpublished one (None) as 0."""
    # Rows from government data leave the stipend blank (None). We count that as 0 so the
    # math never crashes and never makes a program look cheaper than it might really be.
    return program.stipend or 0.0


def tuition_charged(program: Program, home_state: str | None) -> float:
    # A funded PhD student normally pays no tuition (the university waives it). Without this
    # rule a funded PhD showed a big cost: that was our bug D-001 in DEFECT_LOG.md.
    if program.degree == "PhD" and known_stipend(program) > 0:
        return 0.0
    return tuition_for(program, home_state)


def yearly_cost(program: Program, home_state: str | None, living_cost: float) -> float:
    # What the student pays in one year: tuition + living costs, minus the stipend they get.
    cost = tuition_charged(program, home_state) + living_cost - known_stipend(program)
    # A stipend bigger than the costs would give a negative number; nobody "earns" a cost below 0.
    return max(cost, 0.0)


def total_cost(program: Program, home_state: str | None, living_cost: float) -> float:
    # Whole-degree cost: the yearly cost times the number of years (2 for most MS, 4 for BS, ...).
    return yearly_cost(program, home_state, living_cost) * program.duration_years


def is_affordable(program: Program, home_state: str | None, living_cost: float,
                  annual_budget: float) -> bool:
    # A program is affordable when one year costs no more than the student's yearly budget.
    return yearly_cost(program, home_state, living_cost) <= annual_budget


def cost_breakdown(program: Program, home_state: str | None, living_cost: float) -> dict[str, float]:
    """The pieces of the yearly cost, for the cost details view."""
    return {
        "tuition": tuition_charged(program, home_state),
        "living": living_cost,
        "stipend": known_stipend(program),
        "yearly": yearly_cost(program, home_state, living_cost),
        "total": total_cost(program, home_state, living_cost),
        "years": program.duration_years,
    }
