"""GradMatch web app (Streamlit).

This file only collects the student's inputs and shows messages. All the
checking and calculating happens in src/gradmatch so it can be unit tested.

Run it with:  streamlit run app/streamlit_app.py
"""
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import altair as alt  # noqa: E402
import streamlit as st  # noqa: E402

from gradmatch.data_loader import DataError, load_living_costs, load_programs  # noqa: E402
from gradmatch.deadlines import upcoming  # noqa: E402
from gradmatch.fit import MATCH, REACH, SAFETY  # noqa: E402
from gradmatch.models import StudentProfile  # noqa: E402
from gradmatch.presentation import (CARD_CSS, FIT_COLORS, deadline_label,  # noqa: E402
                                    result_card_html)
from gradmatch.search import search_programs  # noqa: E402
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
    return programs, living_costs


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
        strokeDash=[6, 4], size=2).encode(x="Your GPA:Q")
    return (points + you).properties(height=320).interactive()


def show_results(profile: StudentProfile, programs, living_costs, today: date):
    results = search_programs(profile, programs, living_costs)
    if not results:
        st.info("No programs match this profile. Try a higher budget, fewer preferred "
                "states, or a different field.")
        return

    counts = {label: sum(r.fit == label for r in results) for label in (SAFETY, MATCH, REACH)}
    open_deadlines = upcoming([r.program for r in results], today)
    next_deadline = (deadline_label(open_deadlines[0].application_deadline, today)[1]
                     if open_deadlines else "All closed")

    first, second, third = st.columns(3)
    first.metric("Programs found", len(results))
    second.metric("Safety / Match / Reach",
                  f"{counts[SAFETY]} / {counts[MATCH]} / {counts[REACH]}")
    third.metric("Next deadline", next_deadline)

    st.markdown(CARD_CSS, unsafe_allow_html=True)
    st.markdown("".join(result_card_html(r, today) for r in results), unsafe_allow_html=True)
    st.subheader("Cost and admission fit")
    st.altair_chart(cost_chart(results, profile.gpa), width="stretch")
    st.caption("Dots to the right are programs whose admitted students have higher GPAs. "
               "The dashed line is your GPA.")


def main():
    st.set_page_config(page_title="GradMatch", page_icon="🎓", layout="wide")
    st.title("🎓 GradMatch")
    st.caption("Find graduate programs, funding, scholarships and deadlines that fit you. "
               "All numbers are estimates – always check the official program website.")

    try:
        programs, living_costs = load_data(os.environ.get("GRADMATCH_DATA_DIR", str(DATA_DIR)))
    except (DataError, OSError) as error:
        st.error(f"The program data could not be loaded: {error}")
        st.stop()

    fields = sorted({program.field for program in programs})
    profile = show_profile_form(fields)
    if profile is None:
        return

    errors = validate_profile(profile)
    if errors:
        bullets = "\n".join(f"- {message}" for message in errors)
        st.error(f"Please fix the following and try again:\n\n{bullets}")
        return

    st.session_state["profile"] = profile
    st.success("Your profile looks good.")
    st.write(
        f"**{profile.degree_sought}** in **{profile.field}** · GPA **{profile.gpa:.2f}** · "
        f"home state **{profile.home_state}** · budget **${profile.annual_budget:,.0f}** per year"
    )
    show_results(profile, programs, living_costs, get_today())


main()
