"""Turn search results into text and HTML for the results page.

Everything here is plain Python with no Streamlit, so it can be unit
tested. All text that comes from the data files is escaped before it goes
into HTML, and a website is only linked if it starts with http:// or https://.
"""
from datetime import date
from html import escape

from gradmatch.deadlines import CLOSED, LATER, SOON, URGENT, deadline_of, deadline_status
from gradmatch.fit import MATCH, REACH, SAFETY, UNKNOWN
from gradmatch.funding import FULLY_FUNDED, FUNDING_UNKNOWN, PARTIALLY_FUNDED, SELF_FUNDED
from gradmatch.models import Program, Scholarship
from gradmatch.search import ProgramResult

GREEN, YELLOW, CORAL, GREY, BLUE = "#1BB89A", "#F5C469", "#F0705F", "#8A94A6", "#5B9BD5"

FIT_COLORS = {SAFETY: GREEN, MATCH: YELLOW, REACH: CORAL, UNKNOWN: GREY}
FUNDING_COLORS = {FULLY_FUNDED: GREEN, PARTIALLY_FUNDED: YELLOW, SELF_FUNDED: GREY,
                  FUNDING_UNKNOWN: GREY}
DEADLINE_COLORS = {URGENT: CORAL, SOON: YELLOW, LATER: GREY, CLOSED: GREY}

SPECIAL_LABELS = {
    "first_gen": "first-generation students",
    "women_stem": "women in STEM",
    "new_american": "new Americans",
    "underrepresented_minority": "underrepresented minorities",
    "mcnair_scholar": "McNair Scholars",
}
CITIZENSHIP_WORDS = {"US": "U.S. citizens", "PR": "permanent residents",
                     "International": "international students"}

NOT_PUBLISHED = "n/a"
SOURCE_CHIPS = {"ipeds": ("Official school data", BLUE), "official-page": ("Verified on official page", GREEN)}

ESTIMATE_NOTE = ("Average GPA, acceptance rate, funding and fit are estimates. "
                 "PhD costs assume a tuition waiver and leave out mandatory student fees. "
                 "Where a value is shown as n/a, the school does not publish it in official "
                 "data. Always check the official program page.")

CARD_CSS = """
<style>
.gm-card {display:flex; flex-wrap:wrap; align-items:center; gap:0.75rem 1.5rem;
  padding:0.9rem 1.1rem; margin:0 0 0.6rem 0; border-radius:0.75rem;
  border:1px solid rgba(128,128,128,0.25); border-left-width:6px;
  background:rgba(128,128,128,0.07);}
.gm-main {flex:1 1 16rem; min-width:14rem;}
.gm-title {font-weight:600; font-size:1.05rem; text-decoration:none;}
.gm-sub {opacity:0.7; font-size:0.85rem; margin-top:0.15rem;}
.gm-stats {display:flex; gap:1.4rem; flex:0 1 auto;}
.gm-stat-value {font-weight:600; font-size:1.05rem;}
.gm-stat-label {opacity:0.65; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.04em;}
.gm-chips {display:flex; flex-wrap:wrap; gap:0.4rem; flex:0 1 auto;}
.gm-chip {display:inline-block; padding:0.15rem 0.65rem; border-radius:999px; font-size:0.78rem;
  font-weight:600; border:1px solid var(--chip); background:color-mix(in srgb, var(--chip) 18%, transparent);}
</style>
"""


def money(amount: float) -> str:
    return f"${amount:,.0f}"


def percent(rate: float) -> str:
    return f"{rate * 100:.0f}%"


def format_date(day: date) -> str:
    return f"{day:%b} {day.day}, {day.year}"


def safe_link(url: str) -> str | None:
    """Return the url if it is a normal web address, otherwise None."""
    url = (url or "").strip()
    return url if url.startswith(("http://", "https://")) else None


def deadline_label(deadline: date, today: date) -> tuple[str, str]:
    """Return (status, text), e.g. ("urgent", "Dec 15, 2026 · 3 days left")."""
    status = deadline_status(deadline, today)
    days_left = (deadline - today).days
    if status == CLOSED:
        return status, f"Closed {format_date(deadline)}"
    if days_left == 0:
        return status, f"{format_date(deadline)} · due today"
    unit = "day" if days_left == 1 else "days"
    return status, f"{format_date(deadline)} · {days_left} {unit} left"


def toefl_warning(program_min_toefl: int | None, student_toefl: int | None) -> str | None:
    """Return a short warning if the student's TOEFL score is below the program's minimum."""
    if program_min_toefl is None or student_toefl is None:
        return None
    if student_toefl >= program_min_toefl:
        return None
    return f"TOEFL min {program_min_toefl} · you {student_toefl}"


def chip(text: str, color: str) -> str:
    return f'<span class="gm-chip" style="--chip:{color}">{escape(text)}</span>'


def stat(value: str, label: str) -> str:
    return (f'<div><div class="gm-stat-value">{escape(value)}</div>'
            f'<div class="gm-stat-label">{escape(label)}</div></div>')


def _estimate_stat(value, label, show) -> str:
    """A stat that is n/a when unpublished. A value we hold is always an estimate: no official
    data set publishes the average admitted GPA or acceptance rate of one program."""
    if value is None:
        return stat(NOT_PUBLISHED, label)
    return stat(show(value), f"{label} (est.)")


def result_card_html(result: ProgramResult, today: date, student_toefl: int | None = None) -> str:
    program = result.program
    title = f"{program.university} – {program.program_name}"
    link = safe_link(program.website)
    if link:
        title_html = (f'<a class="gm-title" href="{escape(link, quote=True)}" '
                      f'target="_blank" rel="noopener noreferrer">{escape(title)}</a>')
    else:
        title_html = f'<span class="gm-title">{escape(title)}</span>'

    stats = "".join([
        stat(money(result.yearly_cost), "per year"),
        stat(money(result.total_cost), f"{program.duration_years:g} yr total"),
        _estimate_stat(program.avg_gpa, "avg GPA", lambda v: f"{v:.2f}"),
        _estimate_stat(program.acceptance_rate, "accepted", percent),
    ])
    chip_list = [
        chip(result.fit, FIT_COLORS[result.fit]),
        chip(result.funding, FUNDING_COLORS[result.funding]),
    ]
    if program.application_deadline is None:
        chip_list.append(chip("Deadline: check program page", GREY))
    else:
        status, deadline_text = deadline_label(program.application_deadline, today)
        chip_list.append(chip(deadline_text, DEADLINE_COLORS[status]))
    if program.source in SOURCE_CHIPS:
        chip_list.append(chip(*SOURCE_CHIPS[program.source]))
    warning = toefl_warning(program.min_toefl, student_toefl)
    if warning:
        chip_list.append(chip(warning, YELLOW))
    chips = "".join(chip_list)
    return (
        f'<div class="gm-card" style="border-left-color:{FIT_COLORS[result.fit]}">'
        f'<div class="gm-main">{title_html}'
        f'<div class="gm-sub">{escape(program.degree)} · {escape(program.field)} · {escape(program.state)}</div></div>'
        f'<div class="gm-stats">{stats}</div>'
        f'<div class="gm-chips">{chips}</div></div>'
    )


# ---- Scholarships and deadlines ----

def special_label(tag: str) -> str:
    return SPECIAL_LABELS.get(tag, tag.replace("_", " "))


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


def _title_html(text: str, website: str) -> str:
    link = safe_link(website)
    if link:
        return (f'<a class="gm-title" href="{escape(link, quote=True)}" '
                f'target="_blank" rel="noopener noreferrer">{escape(text)}</a>')
    return f'<span class="gm-title">{escape(text)}</span>'


def _stripe_color(status: str) -> str:
    return BLUE if status == LATER else DEADLINE_COLORS[status]


def scholarship_card_html(scholarship: Scholarship, today: date) -> str:
    status, deadline_text = deadline_label(scholarship.deadline, today)
    amount = money(scholarship.amount) if scholarship.amount > 0 else "Non-monetary"
    chips = "".join([
        chip(scholarship.type.replace("_", " ").title(), BLUE),
        chip(deadline_text, DEADLINE_COLORS[status]),
    ])
    return (
        f'<div class="gm-card" style="border-left-color:{_stripe_color(status)}">'
        f'<div class="gm-main">{_title_html(scholarship.name, scholarship.website)}'
        f'<div class="gm-sub">{escape(eligibility_summary(scholarship))}</div></div>'
        f'<div class="gm-stats">{stat(amount, "award")}</div>'
        f'<div class="gm-chips">{chips}</div></div>'
    )


def deadline_item_html(item: Program | Scholarship, today: date) -> str:
    """A compact row for the Deadlines tab: what it is, its name and the countdown."""
    status, deadline_text = deadline_label(deadline_of(item), today)
    if isinstance(item, Program):
        kind, name, website = "Program", f"{item.university} – {item.program_name}", item.website
    else:
        kind, name, website = "Scholarship", item.name, item.website
    chips = chip(kind, BLUE) + chip(deadline_text, DEADLINE_COLORS[status])
    return (
        f'<div class="gm-card" style="border-left-color:{_stripe_color(status)}">'
        f'<div class="gm-main">{_title_html(name, website)}</div>'
        f'<div class="gm-chips">{chips}</div></div>'
    )
