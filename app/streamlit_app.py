import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gradmatch import data_loader  # noqa: E402
from gradmatch.models import Student  # noqa: E402
from gradmatch.search import fields, find_programs  # noqa: E402

DATA = ROOT / "data" / "programs.csv"
STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "IA", "ID", "IL",
          "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE",
          "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT",
          "VA", "VT", "WA", "WI", "WV", "WY"]

st.set_page_config(page_title="GradMatch")
st.title("GradMatch")
st.write("Find master's programs that fit your budget, and see a rough chance of getting in.")

try:
    programs = data_loader.load_programs(DATA)
except (OSError, data_loader.DataError) as error:
    st.error(f"Could not read the program data: {error}")
    st.stop()

with st.form("profile"):
    field = st.selectbox("Field", fields(programs), key="field")
    gpa = st.number_input("Your GPA", min_value=0.0, max_value=4.0, value=3.5, step=0.1, key="gpa")
    home_state = st.selectbox("Your home state", STATES, index=STATES.index("MI"), key="home_state")
    budget = st.number_input("Yearly budget ($)", min_value=0, value=40000, step=1000, key="budget")
    submitted = st.form_submit_button("Find programs")

if submitted:
    results = find_programs(programs, Student(gpa, field, home_state, int(budget)))
    if not results:
        st.info("No programs fit your budget. Try a bigger budget.")
    else:
        st.success(f"{len(results)} programs found, cheapest first.")
        st.dataframe(
            [{"University": r.program.university,
              "Program": r.program.program,
              "State": r.program.state,
              "Yearly cost": f"${r.cost:,}",
              "Chance": r.chance,
              "Website": r.program.website} for r in results],
            hide_index=True,
            column_config={"Website": st.column_config.LinkColumn()},
        )
    st.caption("Yearly cost = tuition + living cost. Chance compares your GPA to the average GPA: "
               "0.20 or more above is Safety, down to 0.15 below is Match, lower is Reach.")
