from gradmatch.models import Program


def tuition_for(program: Program, home_state: str) -> int:
    if home_state == program.state:
        return program.tuition_in_state
    return program.tuition_out_state


def yearly_cost(program: Program, home_state: str) -> int:
    # a PhD stipend comes with a tuition waiver
    if program.stipend:
        return max(program.living_cost - program.stipend, 0)
    return tuition_for(program, home_state) + program.living_cost


def funding(program: Program) -> str:
    if program.stipend is None:
        return "Not listed"
    if program.stipend >= program.living_cost:
        return "Fully funded"
    if program.stipend > 0:
        return "Partly funded"
    return "No funding"
