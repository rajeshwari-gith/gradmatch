"""A rough chance of getting in: Safety, Match or Reach."""

SAFETY = "Safety"
MATCH = "Match"
REACH = "Reach"

SAFETY_MARGIN = 0.20   # GPA this much above the average or more -> Safety
REACH_MARGIN = -0.15   # GPA more than this below the average -> Reach


def check_gpa(gpa: float) -> None:
    if gpa < 0 or gpa > 4:
        raise ValueError(f"GPA must be between 0 and 4, got {gpa}")


def chance(gpa: float, avg_gpa: float) -> str:
    check_gpa(gpa)
    # round() so that 3.7 - 3.5 counts as 0.20 and not 0.1999999.
    diff = round(gpa - avg_gpa, 2)
    if diff >= SAFETY_MARGIN:
        return SAFETY
    if diff >= REACH_MARGIN:
        return MATCH
    return REACH
