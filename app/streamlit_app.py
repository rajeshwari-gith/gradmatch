"""GradMatch web app (Streamlit).

This file only collects the student's inputs and shows messages. All the
checking and calculating happens in src/gradmatch so it can be unit tested.

Run it with:  streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st  # noqa: E402

from gradmatch.data_loader import DataError, load_living_costs, load_programs  # noqa: E402
from gradmatch.models import StudentProfile  # noqa: E402
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


def main():
    st.set_page_config(page_title="GradMatch", page_icon="🎓", layout="wide")
    st.title("🎓 GradMatch")
    st.caption("Find graduate programs, funding, scholarships and deadlines that fit you. "
               "All numbers are estimates – always check the official program website.")

    try:
        programs, living_costs = load_data()
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


main()
