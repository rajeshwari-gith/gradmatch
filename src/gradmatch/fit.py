"""Label a program as Reach, Match or Safety for a student.

Rules (see CONTRIBUTING.md):
- The acceptance rate used is the program's own, or else its university's overall rate
  (official Department of Education data), passed in as school_rate.
- A program that accepts fewer than 10% of applicants is always Reach.
- If the student gives a SAT (or ACT) score and the program publishes the 25th and 75th
  percentile of its enrolled students, compare the score (SAT first, then ACT):
    score >= 75th percentile  -> Safety
    25th <= score < 75th      -> Match
    score < 25th percentile   -> Reach
- If the program publishes an average GPA, compare the student's GPA to it
  (difference rounded to 2 decimals):
    diff >= 0.20          -> Safety
    -0.15 <= diff < 0.20  -> Match
    diff < -0.15          -> Reach
- Otherwise estimate it from the acceptance rate and the student's GPA:
    rate >= 60% -> Safety, 25% <= rate < 60% -> Match, rate < 25% -> Reach,
    then GPA >= 3.7 moves one step easier and GPA < 3.0 one step harder
    (never past Safety or Reach).
- With no average GPA and no acceptance rate at all, the fit is Unknown.
"""
from gradmatch.models import Program

REACH = "Reach"
MATCH = "Match"
SAFETY = "Safety"
UNKNOWN = "Unknown"

# The cut-off numbers live here, in one place, so the rules are easy to find and change.
SELECTIVE_RATE = 0.10     # accepting under 10% of applicants = very hard to get in
SAFETY_MARGIN = 0.20      # GPA this far above the average = a safe choice
REACH_MARGIN = -0.15      # GPA this far below the average = a long shot
OPEN_RATE = 0.60          # accepting 60% or more = usually a safe choice
HARD_RATE = 0.25          # accepting under 25% = usually a long shot
STRONG_GPA = 3.7          # a GPA this high makes the estimate one step easier
WEAK_GPA = 3.0            # a GPA below this makes it one step harder
_EASIER = (REACH, MATCH, SAFETY)  # the labels from hardest to easiest


def score_fit(score: int, low: int, high: int) -> str:
    # low and high are the 25th and 75th percentile test scores of students who enrolled.
    # At or above the top quarter you are very likely in; below the bottom quarter it is a reach.
    if score >= high:
        return SAFETY
    if score >= low:
        return MATCH
    return REACH


def rate_fit(gpa: float, rate: float) -> str:
    """Estimate the chance from how many applicants a school accepts, nudged by the student's GPA."""
    # Start from the school's selectivity, then move one step for a strong or a weak GPA.
    step = 2 if rate >= OPEN_RATE else 1 if rate >= HARD_RATE else 0
    if gpa >= STRONG_GPA:
        step += 1
    elif gpa < WEAK_GPA:
        step -= 1
    return _EASIER[max(0, min(step, 2))]


def classify_fit(gpa: float, program: Program, sat: int | None = None, act: int | None = None,
                 school_rate: float | None = None) -> str:
    # Most graduate programs do not publish their own acceptance rate, so the university's
    # overall rate (from the same official data) stands in for it.
    rate = program.acceptance_rate if program.acceptance_rate is not None else school_rate
    # Rule 1: a very selective program is a Reach for everybody, even with a perfect GPA.
    if rate is not None and rate < SELECTIVE_RATE:
        return REACH
    # Rule 2: for colleges that publish test-score ranges, use the student's SAT, else ACT.
    if sat is not None and program.sat_25 is not None and program.sat_75 is not None:
        return score_fit(sat, program.sat_25, program.sat_75)
    if act is not None and program.act_25 is not None and program.act_75 is not None:
        return score_fit(act, program.act_25, program.act_75)
    # Rule 3: no average GPA published (typical for government data): estimate it from the
    # acceptance rate. With no rate either, we honestly don't know.
    if program.avg_gpa is None:
        return rate_fit(gpa, rate) if rate is not None else UNKNOWN

    # Rule 4: compare GPAs. round() avoids tiny float errors like 0.1999999 sitting on the edge.
    diff = round(gpa - program.avg_gpa, 2)
    if diff >= SAFETY_MARGIN:
        return SAFETY
    if diff >= REACH_MARGIN:
        return MATCH
    return REACH
