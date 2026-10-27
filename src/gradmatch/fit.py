"""Label a program as Reach, Match or Safety for a student.

Rules (see CONTRIBUTING.md):
- A program that accepts fewer than 10% of applicants is always Reach.
- If the student gives a SAT (or ACT) score and the program publishes the 25th and 75th
  percentile of its enrolled students, compare the score (SAT first, then ACT):
    score >= 75th percentile  -> Safety
    25th <= score < 75th      -> Match
    score < 25th percentile   -> Reach
- If the program does not publish an average GPA, the fit is Unknown.
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
UNKNOWN = "Unknown"

SELECTIVE_RATE = 0.10
SAFETY_MARGIN = 0.20
REACH_MARGIN = -0.15


def score_fit(score: int, low: int, high: int) -> str:
    if score >= high:
        return SAFETY
    if score >= low:
        return MATCH
    return REACH


def classify_fit(gpa: float, program: Program, sat: int | None = None, act: int | None = None) -> str:
    if program.acceptance_rate is not None and program.acceptance_rate < SELECTIVE_RATE:
        return REACH
    if sat is not None and program.sat_25 is not None and program.sat_75 is not None:
        return score_fit(sat, program.sat_25, program.sat_75)
    if act is not None and program.act_25 is not None and program.act_75 is not None:
        return score_fit(act, program.act_25, program.act_75)
    if program.avg_gpa is None:
        return UNKNOWN

    diff = round(gpa - program.avg_gpa, 2)
    if diff >= SAFETY_MARGIN:
        return SAFETY
    if diff >= REACH_MARGIN:
        return MATCH
    return REACH
