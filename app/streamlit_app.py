"""GradMatch web app (Streamlit), in the Sage & Cream design.

In plain words: this file only draws the screens and reacts to clicks. Every calculation (search,
cost, fit, funding, scholarships, deadlines) happens in src/gradmatch, and the HTML for each row
and card is built in gradmatch.screens and gradmatch.components, so all of it can be unit tested.

Screens: Program search · PhD funding · Scholarships · Deadlines. Stars and tracked scholarships
are kept in st.session_state, the app's memory between clicks.

Run it with:  streamlit run app/streamlit_app.py
"""
import os
import sys
from dataclasses import replace
from datetime import date, datetime, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import freshness  # noqa: E402

# After an update, make sure the page does not run new app code on an old copy of gradmatch.
freshness.forget_stale_gradmatch(ROOT / "src" / "gradmatch", sys.modules)

import altair as alt  # noqa: E402
import streamlit as st  # noqa: E402

import theme  # noqa: E402
from gradmatch.components import CHANCE_COLORS, warning_banner  # noqa: E402
from gradmatch.cost import cost_breakdown, known_stipend  # noqa: E402
from gradmatch.data_loader import (DataError, load_living_costs, load_programs,  # noqa: E402
                                   load_scholarships)
from gradmatch.deadlines import (CustomDeadline, deadline_of, glance_counts,  # noqa: E402
                                 validate_custom_deadline)
from gradmatch.exports import to_csv, to_ics  # noqa: E402
from gradmatch.fit import MATCH, REACH, SAFETY, UNKNOWN  # noqa: E402
from gradmatch.models import StudentProfile  # noqa: E402
from gradmatch.presentation import ESTIMATE_NOTE, SPECIAL_LABELS, format_date, money  # noqa: E402
from gradmatch.scholarships import KINDS, eligible_scholarships, fellowship_count, kind_of  # noqa: E402
from gradmatch.starred import only_starred, star_key, toggle  # noqa: E402
from gradmatch.screens import (DISCLAIMER, cost_info_html,  # noqa: E402
                               deadline_row_html, faces_info_html, fellowships_note, funding_legend_html, glance_html,
                               header_pills_html, item_name, page_title_html, phd_card_html,
                               profile_summary_html, program_row_html, results_header_html,
                               scholarship_amount_html, scholarship_info_html)
from gradmatch.search import search_programs, tuition_state  # noqa: E402
from gradmatch.validation import CITIZENSHIP, DEGREES, US_STATES, validate_profile  # noqa: E402

# Where the CSV files live. Everything about students and programs is read from here.
DATA_DIR = ROOT / "data"
PAGES = ("Program search", "PhD funding", "Scholarships", "Deadlines")
MAX_ROWS = 60      # draw the first rows only; the CSV download has every match
MAX_PHD_CARDS = 30
WARN_CHOICES = (7, 14, 30)
DEGREE_LABELS = {"BS": "Bachelor's (BS)", "MS": "Master's (MS)", "PhD": "PhD"}
DEGREE_WORDS = {"BS": "Bachelor's", "MS": "Master's", "PhD": "PhD"}
CITIZENSHIP_LABELS = {
    "US": "U.S. citizen",
    "PR": "Permanent resident",
    "International": "International student",
}
PHD_SORTS = ("Stipend, high to low", "Money left after living costs", "School name")
SHOW_CHOICES = ("Only ones I qualify for", "Starred only", "Everything")
LOGO_HTML = ('<div class="gm-logo"><span class="gm-logo-mark">🎓</span>'
             '<span class="gm-serif">GradMatch</span></div>')


# st.cache_data remembers the loaded files, so the big programs file is read only once
# instead of every time the student clicks a button.
@st.cache_data
def load_data(data_dir: str = str(DATA_DIR)):
    programs = load_programs(Path(data_dir) / "programs.csv")
    living_costs = load_living_costs(Path(data_dir) / "living_costs.csv")
    scholarships = load_scholarships(Path(data_dir) / "scholarships.csv")
    return programs, living_costs, scholarships


def get_today() -> date:
    """Today's date. GRADMATCH_TODAY=2026-10-24 fixes it for demos and tests.

    GRADMATCH_DATA_DIR can point the app at a different data folder in the same way.
    """
    fixed = os.environ.get("GRADMATCH_TODAY")
    return date.fromisoformat(fixed) if fixed else date.today()


def optional_int(value):
    # An empty number box gives None; a filled one gives a float, so we turn it into a whole number.
    return None if value is None else int(value)


# ---- Stars and tracked deadlines (kept in the session) ----

def starred() -> frozenset:
    return st.session_state.setdefault("starred", frozenset())


def tracked() -> frozenset:
    return st.session_state.setdefault("tracked", frozenset())


def custom_deadlines() -> list:
    return st.session_state.setdefault("custom_deadlines", [])


def _flip(collection: str, key: str):
    # Called by a button before the page redraws, so the new state shows straight away.
    st.session_state[collection] = toggle(st.session_state.get(collection, frozenset()), key)


def star_button(item, name: str):
    """A round star button. Clicking it stars or unstars the item."""
    key = star_key(item)
    on = key in starred()
    st.button("★" if on else "☆", key=f"star-{key}", on_click=_flip, args=("starred", key),
              help=f"{'Unstar' if on else 'Star'} {name}")


# ---- The profile form (Program search, left side) ----

def show_profile_form(fields: list[str]):
    """Draw the form. Returns a StudentProfile after the student submits, else None."""
    # A form groups all the inputs so the page only re-runs when the student presses the button.
    with st.form("profile_form"):
        st.markdown('<h3 class="gm-serif">Your profile</h3>', unsafe_allow_html=True)
        degree = st.radio("Degree you are applying for", DEGREES, index=DEGREES.index("MS"),
                          key="degree", horizontal=True, format_func=DEGREE_LABELS.get,
                          help="Bachelor's results list colleges for undergraduate applicants.")
        start = fields.index("Computer Science") if "Computer Science" in fields else 0
        field = st.selectbox("Subject", fields, index=start, key="field")
        gpa = st.number_input("Your GPA (0.0 – 4.0)", min_value=0.0, max_value=10.0,
                              value=3.5, step=0.05, format="%.2f", key="gpa")
        budget = st.number_input("Yearly budget (USD)", min_value=0, max_value=500_000,
                                 value=40_000, step=1_000, key="budget",
                                 help="The most you can pay in one year, tuition plus living costs.")
        citizenship = st.selectbox("Citizenship", CITIZENSHIP, key="citizenship",
                                   format_func=CITIZENSHIP_LABELS.get)
        home_state = st.selectbox("Home state", US_STATES, index=US_STATES.index("MI"),
                                  key="home_state",
                                  help="Used to decide between in-state and out-of-state tuition.")
        preferred = st.multiselect("Preferred states (leave empty for any state)", US_STATES,
                                   key="preferred_states")
        with st.expander("Test scores and groups (optional)"):
            gre = st.number_input("GRE score (graduate only)", min_value=0, max_value=400,
                                  value=None, step=1, key="gre",
                                  help="Leave empty if you have not taken the GRE. Range 260 – 340.")
            toefl = st.number_input("TOEFL score", min_value=0, max_value=200,
                                    value=None, step=1, key="toefl",
                                    help="Required for international students. Range 0 – 120.")
            sat = st.number_input("SAT total (bachelor's only)", min_value=0, max_value=2000,
                                  value=None, step=10, key="sat",
                                  help="Range 400 – 1600. Used to compare you with a college's enrolled students.")
            act = st.number_input("ACT composite (bachelor's only)", min_value=0, max_value=50,
                                  value=None, step=1, key="act", help="Range 1 – 36.")
            special = st.multiselect("Does any of this apply to you?",
                                     list(SPECIAL_LABELS), key="special",
                                     format_func=lambda tag: SPECIAL_LABELS[tag].capitalize(),
                                     help="Some scholarships are only for these groups.")
        submitted = st.form_submit_button("Find programs", type="primary", width="stretch")

    if not submitted:
        return None
    # Pack everything the student typed into one StudentProfile object for the logic code.
    return StudentProfile(
        degree_sought=degree,
        gpa=float(gpa),
        field=field or "",
        home_state=home_state,
        citizenship=citizenship,
        annual_budget=float(budget),
        preferred_states=tuple(preferred),
        gre=optional_int(gre),
        toefl=optional_int(toefl),
        special=tuple(special),
        sat=optional_int(sat),
        act=optional_int(act),
    )


# ---- Charts (inside "Cost details and charts") ----

# Chart 1: each dot is a program. Right = admitted students have higher GPAs, up = more expensive.
def cost_chart(results, gpa: float):
    """Scatter chart: average admitted GPA (x) against cost per year (y)."""
    values = [{"Program": r.program.university + " – " + r.program.program_name,
               "Average GPA": r.program.avg_gpa, "Cost per year ($)": r.yearly_cost,
               "Fit": r.fit} for r in results if r.program.avg_gpa is not None]
    points = alt.Chart(alt.Data(values=values)).mark_circle(size=160, opacity=0.85).encode(
        x=alt.X("Average GPA:Q", scale=alt.Scale(zero=False)),
        y=alt.Y("Cost per year ($):Q", scale=alt.Scale(zero=True)),
        color=alt.Color("Fit:N", scale=alt.Scale(
            domain=[SAFETY, MATCH, REACH],
            range=[CHANCE_COLORS[SAFETY][0], CHANCE_COLORS[MATCH][0], CHANCE_COLORS[REACH][0]])),
        tooltip=[alt.Tooltip("Program:N"), alt.Tooltip("Average GPA:Q"),
                 alt.Tooltip("Cost per year ($):Q", format=",.0f"), alt.Tooltip("Fit:N")])
    you = alt.Chart(alt.Data(values=[{"Your GPA": gpa}])).mark_rule(
        strokeDash=[6, 4], size=2, color="#67645A").encode(x=alt.X("Your GPA:Q", title="Average GPA"))
    return (points + you).properties(height=320).interactive()


# Chart 2: the bars show what one year costs: tuition + living costs, minus the stipend.
def breakdown_chart(breakdown: dict):
    """Bar chart of what makes up one year's cost."""
    values = [{"Part": "Tuition", "Amount ($)": breakdown["tuition"]},
              {"Part": "Living costs", "Amount ($)": breakdown["living"]},
              {"Part": "Stipend", "Amount ($)": -breakdown["stipend"]}]
    return alt.Chart(alt.Data(values=values)).mark_bar().encode(
        x=alt.X("Part:N", sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Amount ($):Q"),
        color=alt.Color("Part:N", legend=None, scale=alt.Scale(
            domain=["Tuition", "Living costs", "Stipend"],
            range=["#5E7D63", "#D9A441", "#9DB8AC"])),
        tooltip=[alt.Tooltip("Part:N"), alt.Tooltip("Amount ($):Q", format=",.0f")],
    ).properties(height=260)


def show_cost_details(profile, results, living_costs):
    """The cost breakdown of one chosen program, and the two charts."""
    labels = [f"{r.program.university} – {r.program.program_name}" for r in results]
    chosen = st.selectbox("Choose a program", range(len(results)), key="cost_choice",
                          format_func=lambda i: labels[i])
    result = results[chosen]
    parts = cost_breakdown(result.program, tuition_state(profile), living_costs[result.program.state])
    cols = st.columns(4)
    cols[0].metric("Tuition per year", money(parts["tuition"]))
    cols[1].metric("Living costs per year", money(parts["living"]))
    cols[2].metric("Stipend per year", money(parts["stipend"]))
    cols[3].metric(f"Total for {parts['years']:g} years", money(parts["total"]))
    st.altair_chart(breakdown_chart(parts), width="stretch")
    if result.program.degree == "PhD" and known_stipend(result.program) > 0:
        st.caption("This PhD program pays a stipend, so tuition is assumed to be waived. "
                   "Mandatory student fees are not included.")
    if any(r.program.avg_gpa is not None for r in results):
        st.altair_chart(cost_chart(results, profile.gpa), width="stretch")
        st.caption("Dots to the right are programs whose admitted students have higher GPAs. "
                   "The dashed line is your GPA. Programs that do not publish an average GPA are not drawn.")
    else:
        st.info("None of these programs publish an average admitted GPA, so there is nothing to chart.")


# ---- Screen 1: Program search ----

def show_results(profile, results, living_costs):
    """The right side of Program search: title, filters, the table and the info cards."""
    states = ", ".join(profile.preferred_states) or "any state"
    st.markdown(page_title_html(f"{DEGREE_WORDS[profile.degree_sought]} programs that", "fit you"),
                unsafe_allow_html=True)
    st.markdown(f'<div class="gm-sub">{len(results)} programs in {profile.field} within '
                f'{money(profile.annual_budget)} / year · {states}</div>', unsafe_allow_html=True)
    if not results:
        st.info("No programs match this profile. Try a higher budget, fewer preferred "
                "states, or a different field.")
        return

    # Filter pills with counts (All / Safety / Match / Reach / Unknown) and "Starred only".
    counts = {label: sum(r.fit == label for r in results) for label in (SAFETY, MATCH, REACH, UNKNOWN)}
    options = ["All"] + [label for label, n in counts.items() if n]
    left, right = st.columns([1, 4], vertical_alignment="center")
    starred_only = left.toggle("Starred only", key="results_starred")
    chance = right.radio("Chance", options, horizontal=True, key="chance", label_visibility="collapsed",
                         format_func=lambda o: f"{o} {len(results) if o == 'All' else counts[o]}")
    shown = [r for r in results if (chance == "All" or r.fit == chance)
             and (not starred_only or star_key(r.program) in starred())]

    if len(shown) > MAX_ROWS:
        st.caption(f"Showing the first {MAX_ROWS} of {len(shown)} matches. Narrow your search with a "
                   "lower budget or preferred states, or download all of them.")
    if not shown:
        st.info("No programs match these filters.")
    else:
        st.markdown(results_header_html(), unsafe_allow_html=True)
    home = tuition_state(profile)
    for r in shown[:MAX_ROWS]:
        with st.container(key=f"row-{r.program.program_id}"):
            star_col, row_col = st.columns([0.5, 12], vertical_alignment="center")
            with star_col:
                star_button(r.program, r.program.university)
            row_col.markdown(program_row_html(r, home, living_costs[r.program.state], profile.toefl),
                             unsafe_allow_html=True)

    cost_card, faces_card = st.columns(2)
    cost_card.markdown(cost_info_html(), unsafe_allow_html=True)
    faces_card.markdown(faces_info_html(), unsafe_allow_html=True)
    st.caption(DISCLAIMER + " " + ESTIMATE_NOTE)
    st.download_button("Download all results (.csv)", to_csv(results),
                       file_name="gradmatch_results.csv", mime="text/csv")
    with st.expander("Cost details and charts"):
        show_cost_details(profile, results, living_costs)


# ---- Screen 2: PhD funding ----

def go_to_scholarships():
    st.session_state["page"] = PAGES[2]


def show_phd_page(profile, programs, living_costs, fields, scholarships):
    st.markdown(page_title_html("Funded", "PhD", " programs"), unsafe_allow_html=True)
    if profile is None:
        st.info("Fill in your profile on **Program search** first, so we can show your chances.")
        return
    subject_col, sort_col, waiver_col, star_col = st.columns([2, 2, 1.3, 1.3], vertical_alignment="bottom")
    start = fields.index(profile.field) if profile.field in fields else 0
    subject = subject_col.selectbox("Subject", fields, index=start, key="phd_subject")
    sort = sort_col.selectbox("Sort by", PHD_SORTS, key="phd_sort")
    full_only = waiver_col.checkbox("Full waiver only", key="phd_full",
                                    help="Only programs with a stipend, where tuition is waived.")
    starred_only = star_col.toggle("Starred only", key="phd_starred")

    # The same search as Program search, for PhD programs in this subject, with no budget limit.
    phd_profile = replace(profile, degree_sought="PhD", field=subject, annual_budget=float("inf"))
    results = search_programs(phd_profile, programs, living_costs)
    if full_only:
        results = [r for r in results if known_stipend(r.program) > 0]
    if starred_only:
        results = [r for r in results if star_key(r.program) in starred()]
    if sort == PHD_SORTS[0]:
        results = sorted(results, key=lambda r: (-known_stipend(r.program), r.program.university))
    elif sort == PHD_SORTS[2]:
        results = sorted(results, key=lambda r: r.program.university)

    st.markdown(f'<div class="gm-sub">{len(results)} PhD programs in {subject} · any state · '
                f'sorted by {sort.lower()}</div>', unsafe_allow_html=True)
    count = fellowship_count(phd_profile, scholarships)
    st.button(fellowships_note(count), key="phd_fellowships", type="tertiary", disabled=count == 0,
              on_click=go_to_scholarships)
    st.markdown(funding_legend_html(), unsafe_allow_html=True)
    if not results:
        st.info("No PhD programs match these filters.")
        return
    if len(results) > MAX_PHD_CARDS:
        st.caption(f"Showing the first {MAX_PHD_CARDS} of {len(results)} programs.")
    columns = st.columns(3)
    for index, r in enumerate(results[:MAX_PHD_CARDS]):
        with columns[index % 3]:
            with st.container(key=f"card-{r.program.program_id}"):
                body, star_col = st.columns([6, 1])
                body.markdown(phd_card_html(r), unsafe_allow_html=True)
                with star_col:
                    star_button(r.program, r.program.university)
    st.caption("Stipends and funding terms come from official data or program pages where we have "
               "them; confirm with each department.")


# ---- Screen 3: Scholarships ----

def show_scholarships_page(profile, scholarships, today):
    filters, cards = st.columns([1, 3], gap="large")
    kinds = sorted(set(KINDS.values()))
    with filters:
        st.markdown('<div class="gm-label">Type</div>', unsafe_allow_html=True)
        chosen_kinds = {k for k in kinds if st.checkbox(k, value=True, key=f"type-{k.lower()}")}
        show = st.radio("Show", SHOW_CHOICES, key="sch_show")
        if profile is not None:
            st.markdown(profile_summary_html(profile), unsafe_allow_html=True)

    eligible = {s.scholarship_id for s in eligible_scholarships(profile, scholarships)} if profile else set()
    if show == SHOW_CHOICES[0]:
        items = [s for s in scholarships if s.scholarship_id in eligible and s.deadline >= today]
    elif show == SHOW_CHOICES[1]:
        items = only_starred(scholarships, starred())
    else:
        items = list(scholarships)
    items = sorted((s for s in items if kind_of(s) in chosen_kinds), key=lambda s: (s.deadline, s.name))

    with cards:
        st.markdown(page_title_html("Scholarships &", "opportunities"), unsafe_allow_html=True)
        open_eligible = sum(1 for s in scholarships if s.scholarship_id in eligible and s.deadline >= today)
        st.markdown(f'<div class="gm-sub">{open_eligible} you can apply for · sorted by closest deadline. '
                    "Amounts are as listed by each provider and may be yearly or one-time.</div>",
                    unsafe_allow_html=True)
        if profile is None and show == SHOW_CHOICES[0]:
            st.info("Fill in your profile on **Program search** to see the scholarships you qualify for.")
            return
        if not items:
            st.info("No scholarships match these filters. Try another degree or field, or tick "
                    "the groups that apply to you in the form.")
            return
        for s in items:
            key = star_key(s)
            with st.container(key=f"sch-{s.scholarship_id}"):
                star_col, info_col, amount_col, track_col = st.columns([0.6, 7, 2.2, 1.9],
                                                                       vertical_alignment="center")
                with star_col:
                    star_button(s, s.name)
                info_col.markdown(scholarship_info_html(s, s.scholarship_id in eligible),
                                  unsafe_allow_html=True)
                amount_col.markdown(scholarship_amount_html(s, today), unsafe_allow_html=True)
                on = key in tracked()
                track_col.button("✓ Tracking" if on else "Track deadline", key=f"track-{s.scholarship_id}",
                                 type="secondary" if on else "primary", on_click=_flip,
                                 args=("tracked", key))


# ---- Screen 5: Deadlines ----

def deadline_items(results, scholarships, profile):
    """Everything with a date the student cares about: their programs, the scholarships they
    qualify for, and any scholarship they chose to track. Each item appears once, soonest first."""
    eligible = eligible_scholarships(profile, scholarships) if profile else []
    chosen = [s for s in scholarships if star_key(s) in tracked()]
    items, seen = [], set()
    for item in [r.program for r in results] + list(eligible) + chosen + custom_deadlines():
        if id(item) not in seen and deadline_of(item) is not None:
            seen.add(id(item))
            items.append(item)
    return sorted(items, key=lambda item: (deadline_of(item), item_name(item)))


def add_custom_deadline():
    """Called by the form button: check the name and date, then keep the deadline in the session."""
    name, day = st.session_state.get("custom_name", ""), st.session_state.get("custom_date")
    link = (st.session_state.get("custom_link") or "").strip()
    errors = validate_custom_deadline(name, day)
    if any(star_key(item) == f"deadline:{name.strip()}" for item in custom_deadlines()):
        errors.append("You already have a deadline with this name.")
    st.session_state["custom_errors"] = errors
    if not errors:
        custom_deadlines().append(CustomDeadline(name.strip(), day, link))
        st.session_state["custom_name"] = ""
        st.session_state["custom_link"] = ""


def show_add_deadline():
    with st.expander("+ Add a deadline"):
        with st.form("add_deadline", clear_on_submit=False, border=False):
            st.text_input("What is due", key="custom_name", placeholder="e.g. Recommendation letters")
            st.date_input("Date", key="custom_date", value=None, format="YYYY-MM-DD")
            st.text_input("Link (optional)", key="custom_link")
            st.form_submit_button("Add deadline", type="primary", on_click=add_custom_deadline)
        for message in st.session_state.get("custom_errors", []):
            st.error(message)


def show_deadlines_page(items, today):
    title_col, star_col, warn_col = st.columns([3, 1, 1.4], vertical_alignment="bottom")
    with title_col:
        st.markdown(page_title_html("Upcoming", "deadlines"), unsafe_allow_html=True)
        st.markdown(f'<div class="gm-sub">{len(items)} tracked · today is {today:%b} {today.day}</div>',
                    unsafe_allow_html=True)
    starred_only = star_col.toggle("Starred only", key="dl_starred")
    warn_days = warn_col.selectbox("Warn me when a deadline is within", WARN_CHOICES, index=1,
                                   key="warn_days", format_func=lambda d: f"{d} days")
    if starred_only:
        items = only_starred(items, starred())
    show_add_deadline()
    if not items:
        st.info("There are no deadlines for your programs or scholarships yet. Find programs first, "
                "or track a scholarship.")
        return

    close = [item for item in items if 0 <= (deadline_of(item) - today).days <= warn_days]
    if close:
        names = ", ".join(f"{item_name(item)} ({format_date(deadline_of(item))})" for item in close[:3])
        noun = "deadline is" if len(close) == 1 else "deadlines are"
        st.markdown(warning_banner(f"{len(close)} {noun} coming up in the next {warn_days} days", names),
                    unsafe_allow_html=True)

    timeline, side = st.columns([3, 1.2], gap="large")
    with timeline:
        st.markdown('<div class="gm-label">Timeline</div>', unsafe_allow_html=True)
        for index, item in enumerate(items):
            with st.container(key=f"dl-{index}"):
                row, star_col = st.columns([10, 1], vertical_alignment="center")
                row.markdown(deadline_row_html(item, today, warn_days), unsafe_allow_html=True)
                with star_col:
                    star_button(item, item_name(item))
    with side:
        st.markdown(glance_html(glance_counts(items, today, warn_days), warn_days), unsafe_allow_html=True)
        open_items = [item for item in items if deadline_of(item) >= today]
        stamp = datetime.combine(today, time(0, 0))
        st.download_button("Add these deadlines to my calendar (.ics)", to_ics(open_items, stamp),
                           file_name="gradmatch_deadlines.ics", mime="text/calendar", width="stretch")
        st.caption("Deadlines come from official program and scholarship pages. Always confirm the "
                   "date with the school.")


# ---- The page ----

def show_search_page(fields, programs, living_costs):
    """Program search: the form on the left, the results on the right. Returns the profile."""
    left, right = st.columns([1, 3], gap="large")
    with left:
        submitted = show_profile_form(fields)
    errors = []
    if submitted is not None:
        errors = validate_profile(submitted)
        if errors:
            st.session_state.pop("profile", None)
        else:
            st.session_state["profile"] = submitted
    profile = st.session_state.get("profile")
    with right:
        if errors:
            bullets = "\n".join(f"- {message}" for message in errors)
            st.error(f"Please fix the following and try again:\n\n{bullets}")
        elif profile is None:
            st.markdown(page_title_html("Programs that", "fit you"), unsafe_allow_html=True)
            st.info("Fill in your profile and press **Find programs**.")
        else:
            show_results(profile, search_programs(profile, programs, living_costs), living_costs)


def main():
    # Order: theme, data, header (its pills are filled in last, once the numbers are known),
    # then the chosen screen.
    st.set_page_config(page_title="GradMatch", page_icon="🎓", layout="wide")
    st.markdown(theme.page_css(), unsafe_allow_html=True)
    header = st.container()

    try:
        programs, living_costs, scholarships = load_data(
            os.environ.get("GRADMATCH_DATA_DIR", str(DATA_DIR)))
    except (DataError, OSError) as error:
        st.error(f"The program data could not be loaded: {error}")
        st.stop()

    with header:
        logo_col, nav_col, pills_col = st.columns([1.4, 5, 2.4], vertical_alignment="center")
        logo_col.markdown(LOGO_HTML, unsafe_allow_html=True)
        page = nav_col.radio("Page", PAGES, horizontal=True, key="page", label_visibility="collapsed")
        pills = pills_col.empty()

    today = get_today()
    fields = sorted({program.field for program in programs})

    # The profile form lives on Program search; the other screens use the saved profile.
    # st.session_state is the app's memory between clicks, so the profile survives switching screens.
    if page == PAGES[0]:
        show_search_page(fields, programs, living_costs)
    profile = st.session_state.get("profile")
    results = search_programs(profile, programs, living_costs) if profile else []
    items = deadline_items(results, scholarships, profile)

    if page == PAGES[1]:
        show_phd_page(profile, programs, living_costs, fields, scholarships)
    elif page == PAGES[2]:
        show_scholarships_page(profile, scholarships, today)
    elif page == PAGES[3]:
        show_deadlines_page(items, today)

    warn_days = st.session_state.get("warn_days", WARN_CHOICES[1])
    urgent = glance_counts(items, today, warn_days)["within_window"]
    pills.markdown(header_pills_html(len(starred()), urgent, warn_days), unsafe_allow_html=True)


main()
