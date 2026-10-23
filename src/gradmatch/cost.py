"""Work out what a program costs a student.

Rules (see CLAUDE.md):
- In-state tuition if the student's home state is the program's state,
  otherwise out-of-state tuition.
- Yearly cost = tuition + living cost of the program's state - stipend,
  and never below 0.
"""
from gradmatch.models import Program


def tuition_for(program: Program, home_state: str) -> float:
    if home_state == program.state:
        return program.tuition_in_state
    return program.tuition_out_state


def yearly_cost(program: Program, home_state: str, living_cost: float) -> float:
    cost = tuition_for(program, home_state) + living_cost - program.stipend
    return max(cost, 0.0)


def total_cost(program: Program, home_state: str, living_cost: float) -> float:
    return yearly_cost(program, home_state, living_cost) * program.duration_years


def is_affordable(program: Program, home_state: str, living_cost: float,
                  annual_budget: float) -> bool:
    return yearly_cost(program, home_state, living_cost) <= annual_budget
