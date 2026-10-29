"""HTML for the rows and cards of each screen in the new design.

In plain words: components.py has the small pieces (a badge, a tile, a tag). This file puts them
together into one results row, one PhD card, one scholarship card or one deadline row. The app
only places these and adds the buttons (stars, "Track deadline"), so everything that decides what
a row says can be unit tested here without Streamlit. Text from the data is always escaped.
"""
from datetime import date
from html import escape

from gradmatch.components import (PASSED, chance_badge, check_item, date_tile, face_svg, funding_bar,
                                  official_link, school_tile, stipend_box, tag)
from gradmatch.cost import known_stipend, tuition_charged
from gradmatch.deadlines import deadline_of
from gradmatch.fit import MATCH, REACH, SAFETY, UNKNOWN
from gradmatch.funding import FULLY_FUNDED
from gradmatch.models import Program, Scholarship
from gradmatch.scholarships import ASSISTANTSHIP, FELLOWSHIP, SCHOLARSHIP, kind_of
from gradmatch.presentation import eligibility_summary, format_date, money, toefl_warning
from gradmatch.search import ProgramResult

DISCLAIMER = ("Results are estimates, not a promise of admission. Data: US Department of Education "
              "(IPEDS), College Scorecard and official university websites.")
NOT_STATED = "Not published"
WITHIN_90 = 90       # a deadline more than this many days away counts as "later"

# The tag colour used for each kind of award (scholarships.kind_of gives the kind).
KIND_TAGS = {SCHOLARSHIP: "scholarship", FELLOWSHIP: "fellowship", ASSISTANTSHIP: "assistantship"}


# ---- Header ----

def header_pills_html(starred: int, urgent: int, urgent_days: int = 14) -> str:
    """The two pills on the right of the header: starred items and close deadlines."""
    noun = "deadline" if urgent == 1 else "deadlines"
    return (f'<span class="gm-pill gm-pill-star">★ Starred {starred}</span>'
            f'<span class="gm-pill gm-pill-notice">⏰ {urgent} {noun} in {urgent_days} days</span>')


def page_title_html(before: str, accent: str, after: str = "") -> str:
    """A page title with one word in the accent colour, e.g. "Master's programs that **fit you**"."""
    return (f'<h1 class="gm-serif">{escape(before)} <span class="gm-title-accent">{escape(accent)}</span>'
            f'{escape(after)}</h1>')


# ---- Screen 1: results table ----

RESULTS_COLUMNS = ("Program", "State", "Tuition", "Living", "Est. yearly", "Chance")


def results_header_html() -> str:
    cells = "".join(f"<div>{name}</div>" for name in RESULTS_COLUMNS)
    return f'<div class="gm-grid gm-table-head">{cells}</div>'


def rate_note(program: Program, home_state: str | None) -> str:
    """'in-state' when the student's tuition state is the program's state, else 'out-of-state'."""
    return "in-state" if home_state is not None and home_state == program.state else "out-of-state"


def score_ranges(program: Program) -> str:
    """The middle 50% SAT and ACT of enrolled students, for colleges that publish both ends."""
    parts = []
    if program.sat_25 is not None and program.sat_75 is not None:
        parts.append(f"SAT {program.sat_25}–{program.sat_75}")
    if program.act_25 is not None and program.act_75 is not None:
        parts.append(f"ACT {program.act_25}–{program.act_75}")
    return " · ".join(parts)


def program_row_html(result: ProgramResult, home_state: str | None, living_cost: float,
                     student_toefl: int | None = None) -> str:
    """One row of the results table: school, state and rate, tuition, living, yearly cost, chance."""
    program = result.program
    extras = official_link(program.website)
    scores = score_ranges(program)
    if scores:
        extras = f"{scores} (mid 50%) · {extras}"
    warning = toefl_warning(program.min_toefl, student_toefl)
    if warning:
        extras += " " + tag(warning, "pending")
    name = (f'<div class="gm-cell-name">{school_tile(program.university)}<div>'
            f'<div class="gm-name">{escape(program.university)}</div>'
            f'<div class="gm-sub">{escape(program.program_name)} · {extras}</div></div></div>')
    # data-label names each cell, so a phone can show the cells as a small labelled card.
    cells = [
        name,
        f'<div data-label="State">{escape(program.state)} <span class="gm-sub">{rate_note(program, home_state)}</span></div>',
        f'<div data-label="Tuition">{money(tuition_charged(program, home_state))}</div>',
        f'<div data-label="Living">{money(living_cost)}</div>',
        f'<div class="gm-money" data-label="Est. yearly">{money(result.yearly_cost)}</div>',
        f"<div>{chance_badge(result.fit)}</div>",
    ]
    return f'<div class="gm-grid gm-row">{"".join(cells)}</div>'


def cost_info_html() -> str:
    return ('<div class="gm-soft"><div class="gm-label">How cost is worked out</div>'
            "<p>In-state or out-of-state tuition (international students always pay out-of-state), "
            "plus the living cost of the school's state, minus any stipend. A funded PhD is assumed "
            "to waive tuition.</p></div>")


def faces_info_html() -> str:
    rows = "".join(f'<div class="gm-face-row">{face_svg(label)}<div><b>{label}</b> '
                   f'<span class="gm-sub">{meaning}</span></div></div>'
                   for label, meaning in (
                       (SAFETY, "above the program's typical range"),
                       (MATCH, "within the typical range"),
                       (REACH, "below the typical range"),
                       (UNKNOWN, "the school does not publish the numbers")))
    return f'<div class="gm-card"><div class="gm-label">What the faces mean</div>{rows}</div>'


# ---- Screen 2: PhD cards ----

def phd_checklist(program: Program, funding: str) -> list[tuple[str, bool]]:
    """The ✓ / ! lines on a PhD card. Health insurance is never in our data, so it says so."""
    stipend = program.stipend
    if stipend is None:
        waiver = ("Tuition waiver not published", False)
        living = ("Stipend not published", False)
    elif known_stipend(program) > 0:
        waiver = ("Tuition waived with funding", True)
        living = ("Stipend covers living costs", True) if funding == FULLY_FUNDED else (
            ("Stipend below living costs", False))
    else:
        waiver = ("No stipend listed, so tuition is charged", False)
        living = ("No stipend listed", False)
    return [waiver, living, ("Health insurance: see program page", False)]


def phd_card_html(result: ProgramResult) -> str:
    """The body of one PhD card: funding bar, school, stipend box with chance, checklist."""
    program = result.program
    amount = money(program.stipend) if program.stipend is not None else NOT_STATED
    checks = "".join(check_item(text, ok) for text, ok in phd_checklist(program, result.funding))
    return (f'{funding_bar(result.funding)}'
            f'<div class="gm-cell-name">{school_tile(program.university)}<div>'
            f'<div class="gm-name gm-serif">{escape(program.university)}</div>'
            f'<div class="gm-sub">{escape(program.program_name)} · {escape(program.state)} · '
            f'{official_link(program.website)}</div></div></div>'
            f'{stipend_box(amount, chance_badge(result.fit))}'
            f'<ul class="gm-check">{checks}</ul>')


def fellowships_note(count: int) -> str:
    """The line under the PhD title that points to the Scholarships screen."""
    if count == 0:
        return "No fellowships or assistantships match your profile yet"
    noun = "fellowship or assistantship" if count == 1 else "fellowships and assistantships"
    return f"{count} {noun} you can apply for →"


def funding_legend_html() -> str:
    return ('<div class="gm-legend"><b>Funding level</b>'
            '<span><i style="background:#5E7D63"></i> Fully funded: stipend covers living costs</span>'
            '<span><i style="background:#9DB8AC"></i> Partly funded</span>'
            '<span><i style="background:#E2DDD0"></i> Not funded or not published</span></div>')


# ---- Screen 3: scholarship cards ----

def scholarship_info_html(scholarship: Scholarship, qualifies: bool) -> str:
    """Type tag, '✓ You qualify', the name, who can apply and the official link."""
    kind = kind_of(scholarship)
    tags = tag(kind.upper(), KIND_TAGS[kind])
    if qualifies:
        tags += " " + tag("✓ You qualify", "qualify")
    return (f'<div>{tags}</div><div class="gm-name gm-serif">{escape(scholarship.name)}</div>'
            f'<div class="gm-sub">{escape(eligibility_summary(scholarship))} · '
            f'{official_link(scholarship.website)}</div>')


def due_text(deadline: date, today: date, urgent_days: int = 14) -> str:
    """'Due in 9 days' (urgent), 'Due today', 'Due Jan 15, 2027' (later) or 'Closed ...'."""
    days = (deadline - today).days
    if days < 0:
        return f'<span class="gm-sub">Closed {format_date(deadline)}</span>'
    if days == 0:
        return '<span class="gm-urgent">Due today</span>'
    if days <= urgent_days:
        unit = "day" if days == 1 else "days"
        return f'<span class="gm-urgent">Due in {days} {unit}</span>'
    return f'<span class="gm-sub">Due {format_date(deadline)}</span>'


def scholarship_amount_html(scholarship: Scholarship, today: date, urgent_days: int = 14) -> str:
    amount = money(scholarship.amount) if scholarship.amount > 0 else "Non-monetary"
    return (f'<div class="gm-amount"><div class="gm-money gm-big">{amount}</div>'
            f'<div>{due_text(scholarship.deadline, today, urgent_days)}</div></div>')


def profile_summary_html(profile) -> str:
    states = profile.home_state
    return (f'<div class="gm-soft"><div class="gm-label">Your profile</div>'
            f'<div>GPA {profile.gpa:.2f} · {escape(profile.degree_sought)} · {escape(profile.field)} · '
            f'{escape(states)} resident</div></div>')


# ---- Screen 5: deadline rows ----

def deadline_face(days_left: int, urgent_days: int = 14) -> str:
    """The face on a deadline: Reach when it is close, Match within 90 days, Safety later, Passed after."""
    if days_left < 0:
        return PASSED
    if days_left <= urgent_days:
        return REACH
    if days_left <= WITHIN_90:
        return MATCH
    return SAFETY


def days_left_text(days_left: int) -> str:
    if days_left < 0:
        return "Passed"
    if days_left == 0:
        return "Due today"
    return f"{days_left} day left" if days_left == 1 else f"{days_left} days left"


def item_name(item) -> str:
    """The name shown for any dated item: a program, a scholarship or a custom deadline."""
    if isinstance(item, Program):
        return f"{item.university} – {item.program_name}"
    return item.name


def item_kind(item) -> str:
    if isinstance(item, Program):
        return f"{item.degree} {item.field}"
    if isinstance(item, Scholarship):
        return f"{kind_of(item)} application"
    return item.note or "Your own deadline"


def deadline_row_html(item, today: date, urgent_days: int = 14) -> str:
    """One timeline row: date tile, name, kind and link, and a badge with a face and days left."""
    day = deadline_of(item)
    days_left = (day - today).days
    urgent = 0 <= days_left <= urgent_days
    name_class = "gm-name gm-passed" if days_left < 0 else "gm-name"
    link = official_link(item.website)
    detail = escape(item_kind(item)) + (f" · {link}" if link else "")
    return (f'<div class="gm-cell-name">{date_tile(day, urgent)}<div>'
            f'<div class="{name_class}">{escape(item_name(item))}</div>'
            f'<div class="gm-sub">{detail}</div></div>'
            f'<div class="gm-right">{chance_badge(deadline_face(days_left, urgent_days), days_left_text(days_left))}'
            f'</div></div>')


def glance_html(counts: dict, urgent_days: int = 14) -> str:
    """The 'At a glance' card. counts has within_window, within_90, later and passed."""
    rows = [(f"Within {urgent_days} days", counts["within_window"], "gm-urgent"),
            ("Within 90 days", counts["within_90"], ""),
            ("Later", counts["later"], ""),
            ("Passed", counts["passed"], "gm-sub")]
    body = "".join(f'<div class="gm-glance-row"><span>{label}</span><b class="{css}">{n}</b></div>'
                   for label, n, css in rows)
    return f'<div class="gm-soft"><div class="gm-serif gm-name">At a glance</div>{body}</div>'
