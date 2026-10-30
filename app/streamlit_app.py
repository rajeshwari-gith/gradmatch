import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gradmatch import data_loader  # noqa: E402
from gradmatch import deadlines as dl  # noqa: E402
from gradmatch.models import Student  # noqa: E402
from gradmatch.scholarships import find_scholarships  # noqa: E402
from gradmatch.database import create_database, get_fields, get_programs  # noqa: E402
from gradmatch.search import find_programs  # noqa: E402

DATA = ROOT / "data"
STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "IA", "ID", "IL",
          "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE",
          "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT",
          "VA", "VT", "WA", "WI", "WV", "WY"]
CITIZENSHIP = {"US citizen": "US", "Permanent resident": "PR", "International": "International"}

st.set_page_config(page_title="GradMatch")
st.title("GradMatch")
st.write("Find graduate programs you can afford, scholarships you can apply for, and their deadlines.")

try:
    database = create_database(data_loader.load_programs(DATA / "programs.csv"))
    scholarships = data_loader.load_scholarships(DATA / "scholarships.csv")
except (OSError, data_loader.DataError) as error:
    st.error(f"Could not read the data: {error}")
    st.stop()

with st.form("profile"):
    degree = st.radio("Degree", ["MS", "PhD"], horizontal=True, key="degree")
    field = st.selectbox("Field", get_fields(database), key="field")
    gpa = st.number_input("Your GPA", min_value=0.0, max_value=4.0, value=3.5, step=0.1, key="gpa")
    home_state = st.selectbox("Your home state", STATES, index=STATES.index("MI"), key="home_state")
    gre = st.number_input("GRE score (optional)", min_value=260, max_value=340, value=None,
                          key="gre")
    states = st.multiselect("States you'd like (leave empty for any)", STATES, key="states")
    budget = st.number_input("Yearly budget ($)", min_value=0, value=40000, step=1000, key="budget")
    citizenship = st.selectbox("Citizenship", list(CITIZENSHIP), key="citizenship")
    submitted = st.form_submit_button("Search")

if submitted:
    student = Student(degree, field, gpa, home_state, int(budget), CITIZENSHIP[citizenship],
                      tuple(states), None if gre is None else int(gre))

    st.subheader("Programs")
    results = find_programs(get_programs(database, degree, field), student)
    if results:
        order = "best funded first" if degree == "PhD" else "cheapest first"
        st.write(f"{len(results)} programs fit your budget, {order}.")
        rows = [{"University": r.program.university, "Program": r.program.program,
                 "State": r.program.state, "Yearly cost": f"${r.cost:,}", "Chance": r.chance}
                for r in results]
        for row, r in zip(rows, results):
            if degree == "PhD":
                row["Funding"] = r.funding
            row["Website"] = r.program.website
        st.dataframe(rows, hide_index=True,
                     column_config={"Website": st.column_config.LinkColumn()})
    else:
        st.info("No programs fit your budget. Try a bigger budget.")
    st.caption("Yearly cost = tuition + living cost, minus any PhD stipend (which comes with a "
               "tuition waiver). Chance is an estimate from the school's acceptance rate and your GPA.")

    st.subheader("Scholarships")
    found = find_scholarships(scholarships, student)
    if found:
        st.dataframe(
            [{"Name": s.name, "Amount": f"${s.amount:,}", "Deadline": s.deadline.isoformat(),
              "Website": s.website} for s in found],
            hide_index=True, column_config={"Website": st.column_config.LinkColumn()},
        )
    else:
        st.info("No scholarships match you.")

    st.subheader("Deadlines")
    dates = [(s.name, s.deadline) for s in found]
    dates += [(f"{r.program.university} ({r.program.program})", r.program.deadline)
              for r in results if r.program.deadline]
    deadlines = dl.upcoming(dates, dl.today())
    for d in deadlines:
        if d.soon:
            st.warning(f"{d.name} is due in {d.days_left} days ({d.date:%b %d}).")
    if deadlines:
        st.dataframe([{"Name": d.name, "Date": d.date.isoformat(), "Days left": d.days_left}
                      for d in deadlines], hide_index=True)
    else:
        st.info("No upcoming deadlines.")
