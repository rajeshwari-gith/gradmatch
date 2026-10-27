"""Work out what a program costs a student.

Rules (see CONTRIBUTING.md):
- In-state tuition if the student's home state is the program's state,
  otherwise out-of-state tuition.
- A PhD program that pays a stipend (stipend > 0) waives tuition, so the
  student is charged no tuition. MS programs always charge tuition.
- Yearly cost = tuition charged + living cost of the program's state - stipend,
  and never below 0.
"""
from gradmatch.models import Program


def tuition_for(program: Program, home_state: str | None) -> float:
    """In-state rate if home_state is the program's state; None means no state (out-of-state)."""
    if home_state is not None and home_state == program.state:
        return program.tuition_in_state
    return program.tuition_out_state


def tuition_charged(program: Program, home_state: str | None) -> float:
    if program.degree == "PhD" and program.stipend > 0:
        return 0.0
    return tuition_for(program, home_state)


def yearly_cost(program: Program, home_state: str | None, living_cost: float) -> float:
    cost = tuition_charged(program, home_state) + living_cost - program.stipend
    return max(cost, 0.0)


def total_cost(program: Program, home_state: str | None, living_cost: float) -> float:
    return yearly_cost(program, home_state, living_cost) * program.duration_years


def is_affordable(program: Program, home_state: str | None, living_cost: float,
                  annual_budget: float) -> bool:
    return yearly_cost(program, home_state, living_cost) <= annual_budget


def cost_breakdown(program: Program, home_state: str | None, living_cost: float) -> dict[str, float]:
    """The pieces of the yearly cost, for the cost details view."""
    return {
        "tuition": tuition_charged(program, home_state),
        "living": living_cost,
        "stipend": program.stipend,
        "yearly": yearly_cost(program, home_state, living_cost),
        "total": total_cost(program, home_state, living_cost),
        "years": program.duration_years,
    }
