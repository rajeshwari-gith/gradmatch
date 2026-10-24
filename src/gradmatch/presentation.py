"""Turn search results into text and HTML for the results page.

Everything here is plain Python with no Streamlit, so it can be unit
tested. All text that comes from the data files is escaped before it goes
into HTML, and a website is only linked if it starts with http:// or https://.
"""
from datetime import date
from html import escape

from gradmatch.deadlines import CLOSED, LATER, SOON, URGENT, deadline_status
from gradmatch.fit import MATCH, REACH, SAFETY
from gradmatch.funding import FULLY_FUNDED, PARTIALLY_FUNDED, SELF_FUNDED
from gradmatch.search import ProgramResult

GREEN, YELLOW, CORAL, GREY = "#1BB89A", "#F5C469", "#F0705F", "#8A94A6"

FIT_COLORS = {SAFETY: GREEN, MATCH: YELLOW, REACH: CORAL}
FUNDING_COLORS = {FULLY_FUNDED: GREEN, PARTIALLY_FUNDED: YELLOW, SELF_FUNDED: GREY}
DEADLINE_COLORS = {URGENT: CORAL, SOON: YELLOW, LATER: GREY, CLOSED: GREY}

ESTIMATE_NOTE = ("Average GPA, acceptance rate, funding and fit are estimates. "
                 "PhD costs assume a tuition waiver and leave out mandatory student fees. "
                 "Always check the official program page.")

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


def result_card_html(result: ProgramResult, today: date, student_toefl: int | None = None) -> str:
    program = result.program
    title = f"{program.university} – {program.program_name}"
    link = safe_link(program.website)
    if link:
        title_html = (f'<a class="gm-title" href="{escape(link, quote=True)}" '
                      f'target="_blank" rel="noopener noreferrer">{escape(title)}</a>')
    else:
        title_html = f'<span class="gm-title">{escape(title)}</span>'

    status, deadline_text = deadline_label(program.application_deadline, today)
    stats = "".join([
        stat(money(result.yearly_cost), "per year"),
        stat(money(result.total_cost), f"{program.duration_years:g} yr total"),
        stat(f"{program.avg_gpa:.2f}", "avg GPA (est.)"),
        stat(percent(program.acceptance_rate), "accepted (est.)"),
    ])
    chip_list = [
        chip(result.fit, FIT_COLORS[result.fit]),
        chip(result.funding, FUNDING_COLORS[result.funding]),
        chip(deadline_text, DEADLINE_COLORS[status]),
    ]
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
