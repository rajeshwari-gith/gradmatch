SAFETY = "Safety"
MATCH = "Match"
REACH = "Reach"
LEVELS = (REACH, MATCH, SAFETY)

VERY_SELECTIVE = 0.10
EASY_RATE = 0.60
HARD_RATE = 0.25
STRONG_GPA = 3.7
WEAK_GPA = 3.0
GRE_MARGIN = 5


def check_gpa(gpa: float) -> None:
    if gpa < 0 or gpa > 4:
        raise ValueError(f"GPA must be between 0 and 4, got {gpa}")


def check_gre(gre: int) -> None:
    if gre < 260 or gre > 340:
        raise ValueError(f"GRE must be between 260 and 340, got {gre}")


def chance(gpa: float, acceptance_rate: float, gre: int | None = None,
           avg_gre: int | None = None) -> str:
    check_gpa(gpa)
    if acceptance_rate < VERY_SELECTIVE:
        return REACH
    if acceptance_rate >= EASY_RATE:
        level = 2
    elif acceptance_rate >= HARD_RATE:
        level = 1
    else:
        level = 0
    if gpa >= STRONG_GPA:
        level += 1
    elif gpa < WEAK_GPA:
        level -= 1
    if gre is not None and avg_gre is not None:
        if gre >= avg_gre + GRE_MARGIN:
            level += 1
        elif gre < avg_gre - GRE_MARGIN:
            level -= 1
    level = max(0, min(level, 2))
    return LEVELS[level]
