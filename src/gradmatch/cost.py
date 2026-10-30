"""How much one year of a program costs a student."""
from gradmatch.models import Program


def tuition(program: Program, home_state: str) -> int:
    # Students from the program's own state pay the cheaper in-state rate.
    if home_state == program.state:
        return program.tuition_in_state
    return program.tuition_out_state


def yearly_cost(program: Program, home_state: str) -> int:
    return tuition(program, home_state) + program.living_cost

