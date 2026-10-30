from gradmatch.models import Program


def yearly_cost(program: Program, home_state: str) -> int:
    if home_state == program.state:
        return program.tuition_in_state + program.living_cost
    return program.tuition_out_state + program.living_cost
