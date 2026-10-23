"""Label a program as Reach, Match or Safety for a student.

Rules (see CONTRIBUTING.md):
- A program that accepts fewer than 10% of applicants is always Reach.
- Otherwise compare the student's GPA to the program's average GPA
  (difference rounded to 2 decimals):
    diff >= 0.20          -> Safety
    -0.15 <= diff < 0.20  -> Match
    diff < -0.15          -> Reach
"""
from gradmatch.models import Program

REACH = "Reach"
MATCH = "Match"
SAFETY = "Safety"

SELECTIVE_RATE = 0.10
SAFETY_MARGIN = 0.20
REACH_MARGIN = -0.15


def classify_fit(gpa: float, program: Program) -> str:
    if program.acceptance_rate < SELECTIVE_RATE:
        return REACH

    diff = round(gpa - program.avg_gpa, 2)
    if diff >= SAFETY_MARGIN:
        return SAFETY
    if diff >= REACH_MARGIN:
        return MATCH
    return REACH
