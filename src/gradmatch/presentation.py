"""Small text helpers shared by the screens: money, dates, safe links and who can apply.

Everything here is plain Python with no Streamlit, so it can be unit tested. A website is only
linked if it starts with http:// or https://.
"""
from datetime import date

from gradmatch.models import Scholarship

SPECIAL_LABELS = {
    "first_gen": "first-generation students",
    "women_stem": "women in STEM",
    "new_american": "new Americans",
    "underrepresented_minority": "underrepresented minorities",
    "mcnair_scholar": "McNair Scholars",
}
CITIZENSHIP_WORDS = {"US": "U.S. citizens", "PR": "permanent residents",
                     "International": "international students"}

ESTIMATE_NOTE = ("Average GPA, acceptance rate, funding and fit are estimates. "
                 "PhD costs assume a tuition waiver and leave out mandatory student fees. "
                 "Where the school does not publish a value, the page says so instead of "
                 "guessing. Always check the official program page.")


def money(amount: float) -> str:
    # 27000 -> "$27,000" (no cents, with commas).
    return f"${amount:,.0f}"


def format_date(day: date) -> str:
    return f"{day:%b} {day.day}, {day.year}"


def safe_link(url: str) -> str | None:
    """Return the url if it is a normal web address, otherwise None."""
    # Only http(s) links become clickable. A bad value like "javascript:..." could run code in
    # the page, so we refuse anything else.
    url = (url or "").strip()
    return url if url.startswith(("http://", "https://")) else None


def toefl_warning(program_min_toefl: int | None, student_toefl: int | None) -> str | None:
    """Return a short warning if the student's TOEFL score is below the program's minimum."""
    if program_min_toefl is None or student_toefl is None:
        return None
    if student_toefl >= program_min_toefl:
        return None
    return f"TOEFL min {program_min_toefl} · you {student_toefl}"


# ---- Scholarships ----

def special_label(tag: str) -> str:
    return SPECIAL_LABELS.get(tag, tag.replace("_", " "))


# The scholarship cards describe who can apply in one short line.
def eligibility_summary(scholarship: Scholarship) -> str:
    """One line describing who can apply, e.g. 'PhD · Any field · GPA 3.00+ · U.S. citizens'."""
    parts = [", ".join(scholarship.degree_levels)]
    parts.append("Any field" if "Any" in scholarship.fields else ", ".join(scholarship.fields))
    if scholarship.min_gpa > 0:
        parts.append(f"GPA {scholarship.min_gpa:.2f}+")
    if "Any" in scholarship.citizenship:
        parts.append("Any citizenship")
    else:
        parts.append(" / ".join(CITIZENSHIP_WORDS.get(c, c) for c in scholarship.citizenship))
    parts.append("Any state" if "Any" in scholarship.states
                 else "Residents of " + ", ".join(scholarship.states))
    if scholarship.special:
        parts.append("For " + ", ".join(special_label(t) for t in scholarship.special))
    return " · ".join(parts)
