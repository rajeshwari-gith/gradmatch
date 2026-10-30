SAFETY = "Safety"
MATCH = "Match"
REACH = "Reach"

SAFETY_MARGIN = 0.20
REACH_MARGIN = -0.15


def check_gpa(gpa: float) -> None:
    if gpa < 0 or gpa > 4:
        raise ValueError(f"GPA must be between 0 and 4, got {gpa}")


def chance(gpa: float, avg_gpa: float) -> str:
    check_gpa(gpa)
    diff = round(gpa - avg_gpa, 2)  # so 3.7 - 3.5 is 0.2, not 0.19999
    if diff >= SAFETY_MARGIN:
        return SAFETY
    if diff >= REACH_MARGIN:
        return MATCH
    return REACH
