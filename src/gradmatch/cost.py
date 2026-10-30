from gradmatch.models import Program


def tuition_for(program: Program, home_state: str) -> int:
    if home_state == program.state:
        return program.tuition_in_state
    return program.tuition_out_state


def yearly_cost(program: Program, home_state: str) -> int:
    return tuition_for(program, home_state) + program.living_cost
