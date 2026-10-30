SAFETY = "Safety"
MATCH = "Match"
REACH = "Reach"


def check_gpa(gpa: float) -> None:
    if gpa < 0 or gpa > 4:
        raise ValueError(f"GPA must be between 0 and 4, got {gpa}")


def chance(gpa: float, acceptance_rate: float) -> str:
    if acceptance_rate < 0.10:
        return REACH

    points = 0
    if acceptance_rate >= 0.60:
        points += 2
    elif acceptance_rate >= 0.25:
        points += 1

    if gpa >= 3.7:
        points += 1
    elif gpa < 3.0:
        points -= 1

    if points >= 2:
        return SAFETY
    if points == 1:
        return MATCH
    return REACH
