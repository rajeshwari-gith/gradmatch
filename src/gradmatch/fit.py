SAFETY = "Safety"
MATCH = "Match"
REACH = "Reach"


def check_gpa(gpa: float) -> None:
    if gpa < 0 or gpa > 4:
        raise ValueError(f"GPA must be between 0 and 4, got {gpa}")


def check_gre(gre: int) -> None:
    if gre < 260 or gre > 340:
        raise ValueError(f"GRE must be between 260 and 340, got {gre}")


def chance(gpa: float, acceptance_rate: float, gre: int | None = None,
           avg_gre: int | None = None) -> str:
    check_gpa(gpa)
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

    if gre is not None and avg_gre is not None:
        if gre >= avg_gre + 5:
            points += 1
        elif gre < avg_gre - 5:
            points -= 1

    if points >= 2:
        return SAFETY
    if points == 1:
        return MATCH
    return REACH
