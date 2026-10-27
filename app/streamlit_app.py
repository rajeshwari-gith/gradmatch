"""GradMatch web app (Streamlit).

This file only collects the student's inputs and shows messages. All the
checking and calculating happens in src/gradmatch so it can be unit tested.

Run it with:  streamlit run app/streamlit_app.py
"""
import os
import sys
from datetime import date, datetime, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import altair as alt  # noqa: E402
import streamlit as st  # noqa: E402

from gradmatch.cost import cost_breakdown  # noqa: E402
from gradmatch.data_loader import (DataError, load_living_costs, load_programs,  # noqa: E402
                                   load_scholarships)
from gradmatch.deadlines import upcoming  # noqa: E402
from gradmatch.exports import to_csv, to_ics  # noqa: E402
from gradmatch.fit import MATCH, REACH, SAFETY  # noqa: E402
from gradmatch.models import StudentProfile  # noqa: E402
from gradmatch.presentation import (CARD_CSS, ESTIMATE_NOTE, FIT_COLORS,  # noqa: E402
                                    SPECIAL_LABELS, deadline_item_html, deadline_label, money,
                                    result_card_html, scholarship_card_html)
from gradmatch.scholarships import eligible_scholarships  # noqa: E402
from gradmatch.search import search_programs, tuition_state  # noqa: E402
from gradmatch.validation import CITIZENSHIP, DEGREES, US_STATES, validate_profile  # noqa: E402

DATA_DIR = ROOT / "data"
CITIZENSHIP_LABELS = {
    "US": "U.S. citizen",
    "PR": "Permanent resident",
    "International": "International student",
}


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
    return None if value is None else int(value)


def show_profile_form(fields: list[str]):
    """Draw the form. Returns a StudentProfile after the student submits, else None."""
    with st.form("profile_form"):
        left, right = st.columns(2)
        with left:
            degree = st.radio("Degree you are applying for", DEGREES, key="degree", horizontal=True)
            field = st.selectbox("Field of study", fields, key="field")
            gpa = st.number_input("Your GPA (0.0 – 4.0)", min_value=0.0, max_value=10.0,
                                  value=3.5, step=0.05, format="%.2f", key="gpa")
            gre = st.number_input("GRE score (optional)", min_value=0, max_value=400,
                                  value=None, step=1, key="gre",
                                  help="Leave empty if you have not taken the GRE. Range 260 – 340.")
            toefl = st.number_input("TOEFL score (optional)", min_value=0, max_value=200,
                                    value=None, step=1, key="toefl",
                                    help="Required for international students. Range 0 – 120.")
        with right:
            citizenship = st.selectbox("Citizenship", CITIZENSHIP, key="citizenship",
                                       format_func=CITIZENSHIP_LABELS.get)
            home_state = st.selectbox("Home state", US_STATES, index=US_STATES.index("MI"),
                                      key="home_state",
                                      help="Used to decide between in-state and out-of-state tuition.")
            preferred = st.multiselect("Preferred states (leave empty for any state)", US_STATES,
                                       key="preferred_states")
            budget = st.number_input("Yearly budget (USD)", min_value=0, max_value=500_000,
                                     value=40_000, step=1_000, key="budget",
                                     help="The most you can pay in one year, tuition plus living costs.")
            special = st.multiselect("Does any of this apply to you? (optional)",
                                     list(SPECIAL_LABELS), key="special",
                                     format_func=lambda tag: SPECIAL_LABELS[tag].capitalize(),
                                     help="Some scholarships are only for these groups.")
        submitted = st.form_submit_button("Find programs", type="primary")

    if not submitted:
        return None
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
    )


def cost_chart(results, gpa: float):
    """Scatter chart: average admitted GPA (x) against cost per year (y)."""
    values = [{"Program": r.program.university + " – " + r.program.program_name,
               "Average GPA": r.program.avg_gpa, "Cost per year ($)": r.yearly_cost,
               "Fit": r.fit} for r in results]
    points = alt.Chart(alt.Data(values=values)).mark_circle(size=160, opacity=0.85).encode(
        x=alt.X("Average GPA:Q", scale=alt.Scale(zero=False)),
        y=alt.Y("Cost per year ($):Q", scale=alt.Scale(zero=True)),
        color=alt.Color("Fit:N", scale=alt.Scale(
            domain=[SAFETY, MATCH, REACH],
            range=[FIT_COLORS[SAFETY], FIT_COLORS[MATCH], FIT_COLORS[REACH]])),
        tooltip=[alt.Tooltip("Program:N"), alt.Tooltip("Average GPA:Q"),
                 alt.Tooltip("Cost per year ($):Q", format=",.0f"), alt.Tooltip("Fit:N")])
    you = alt.Chart(alt.Data(values=[{"Your GPA": gpa}])).mark_rule(
        strokeDash=[6, 4], size=2, color="#8A94A6").encode(x=alt.X("Your GPA:Q", title="Average GPA"))
    return (points + you).properties(height=320).interactive()


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
            range=["#5B9BD5", "#F5C469", "#1BB89A"])),
        tooltip=[alt.Tooltip("Part:N"), alt.Tooltip("Amount ($):Q", format=",.0f")],
    ).properties(height=260)


def show_programs(profile: StudentProfile, results, living_costs, today: date):
    if not results:
        st.info("No programs match this profile. Try a higher budget, fewer preferred "
                "states, or a different field.")
        return

    st.caption(ESTIMATE_NOTE)
    st.markdown("".join(result_card_html(r, today, profile.toefl) for r in results),
                unsafe_allow_html=True)
    st.download_button("Download these results (.csv)", to_csv(results),
                       file_name="gradmatch_results.csv", mime="text/csv")

    st.subheader("Cost and admission fit")
    st.altair_chart(cost_chart(results, profile.gpa), width="stretch")
    st.caption("Dots to the right are programs whose admitted students have higher GPAs. "
               "The dashed line is your GPA.")

    st.subheader("Cost breakdown")
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
    if result.program.degree == "PhD" and result.program.stipend > 0:
        st.caption("This PhD program pays a stipend, so tuition is assumed to be waived. "
                   "Mandatory student fees are not included.")


def show_scholarships(matches, open_matches, today: date):
    if not matches:
        st.info("No scholarships match your profile. Try another degree or field, or tick "
                "the groups that apply to you in the form.")
        return
    hidden = len(matches) - len(open_matches)
    noun = "scholarship or opportunity" if len(open_matches) == 1 else "scholarships and opportunities"
    note = f"{len(open_matches)} open {noun} you qualify for"
    if hidden:
        note += f" ({hidden} already closed and hidden)"
    st.caption(note + ". Amounts are as listed by each provider and may be a yearly amount or a "
               "one-time total. Always check the official page for the exact rules.")
    if open_matches:
        st.markdown("".join(scholarship_card_html(s, today) for s in open_matches),
                    unsafe_allow_html=True)


def show_deadlines(results, open_matches, today: date):
    items = upcoming([r.program for r in results] + list(open_matches), today)
    if not items:
        st.info("There are no open deadlines for your programs or scholarships.")
        return
    st.caption("Open deadlines for your programs and scholarships, soonest first.")
    st.markdown("".join(deadline_item_html(item, today) for item in items), unsafe_allow_html=True)
    stamp = datetime.combine(today, time(0, 0))
    st.download_button("Add these deadlines to my calendar (.ics)", to_ics(items, stamp),
                       file_name="gradmatch_deadlines.ics", mime="text/calendar")


def show_results(profile: StudentProfile, programs, living_costs, scholarships, today: date):
    results = search_programs(profile, programs, living_costs)
    matches = eligible_scholarships(profile, scholarships)
    open_matches = upcoming(matches, today)

    if results:
        counts = {label: sum(r.fit == label for r in results) for label in (SAFETY, MATCH, REACH)}
        coming = upcoming([r.program for r in results] + list(open_matches), today)
        next_deadline = (deadline_label(_deadline(coming[0]), today)[1] if coming else "All closed")
        cols = st.columns(4)
        cols[0].metric("Programs found", len(results))
        cols[1].metric("Safety / Match / Reach",
                       f"{counts[SAFETY]} / {counts[MATCH]} / {counts[REACH]}")
        cols[2].metric("Scholarships you qualify for", len(open_matches))
        next_date, _, days_left = next_deadline.partition(" · ")
        cols[3].metric("Next deadline", next_date, delta=days_left or None,
                       delta_color="off", delta_arrow="off")

    st.markdown(CARD_CSS, unsafe_allow_html=True)
    programs_tab, scholarships_tab, deadlines_tab = st.tabs(["Programs", "Scholarships", "Deadlines"])
    with programs_tab:
        show_programs(profile, results, living_costs, today)
    with scholarships_tab:
        show_scholarships(matches, open_matches, today)
    with deadlines_tab:
        show_deadlines(results, open_matches, today)


def _deadline(item) -> date:
    return item.application_deadline if hasattr(item, "application_deadline") else item.deadline


def main():
    st.set_page_config(page_title="GradMatch", page_icon="🎓", layout="wide")
    st.title("🎓 GradMatch")
    st.caption("Find graduate programs, funding, scholarships and deadlines that fit you. "
               "All numbers are estimates – always check the official program website.")

    try:
        programs, living_costs, scholarships = load_data(
            os.environ.get("GRADMATCH_DATA_DIR", str(DATA_DIR)))
    except (DataError, OSError) as error:
        st.error(f"The program data could not be loaded: {error}")
        st.stop()

    fields = sorted({program.field for program in programs})
    submitted = show_profile_form(fields)
    if submitted is not None:
        errors = validate_profile(submitted)
        if errors:
            st.session_state.pop("profile", None)
            bullets = "\n".join(f"- {message}" for message in errors)
            st.error(f"Please fix the following and try again:\n\n{bullets}")
            return
        st.session_state["profile"] = submitted

    # The profile stays in the session, so using a dropdown or a download button
    # below does not make the results disappear.
    profile = st.session_state.get("profile")
    if profile is None:
        return

    st.success("Your profile looks good.")
    st.write(
        f"**{profile.degree_sought}** in **{profile.field}** · GPA **{profile.gpa:.2f}** · "
        f"home state **{profile.home_state}** · budget **${profile.annual_budget:,.0f}** per year"
    )
    show_results(profile, programs, living_costs, scholarships, get_today())


main()
