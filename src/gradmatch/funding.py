"""Label how well a program is funded.

Rules (see CONTRIBUTING.md):
- stipend >= living cost of the program's state -> Fully Funded
- 0 < stipend < living cost                     -> Partially Funded
- stipend == 0                                  -> Self-Funded
- stipend not published (None)                  -> Funding unknown
"""
from gradmatch.models import Program

FULLY_FUNDED = "Fully Funded"
PARTIALLY_FUNDED = "Partially Funded"
SELF_FUNDED = "Self-Funded"
FUNDING_UNKNOWN = "Funding unknown"


def funding_label(program: Program, living_cost: float) -> str:
    if program.stipend is None:
        return FUNDING_UNKNOWN
    if program.stipend <= 0:
        return SELF_FUNDED
    if program.stipend >= living_cost:
        return FULLY_FUNDED
    return PARTIALLY_FUNDED
