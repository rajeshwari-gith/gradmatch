from pathlib import Path

import streamlit as st

import deadlines
from database import connect, get_programs, get_scholarships
from models import Student
from scholarships import find_scholarships
from search import find_programs

DATABASE = Path(__file__).parent / "data" / "gradmatch.db"
STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "IA", "ID", "IL",
          "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE",
          "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT",
          "VA", "VT", "WA", "WI", "WV", "WY"]

st.set_page_config(page_title="GradMatch")
st.title("GradMatch")
st.write("Find graduate programs you can afford, scholarships you can apply for, and their deadlines.")

connection = connect(DATABASE)
programs = get_programs(connection)
scholarships = get_scholarships(connection)
connection.close()
if not programs:
    st.error("No programs found in the database.")
    st.stop()

with st.form("profile"):
    degree = st.radio("Degree", ["MS", "PhD"], horizontal=True, key="degree")
    field = st.selectbox("Field", sorted({p.field for p in programs}), key="field")
    gpa = st.number_input("Your GPA", min_value=0.0, max_value=4.0, value=3.5, step=0.1, key="gpa")
    home_state = st.selectbox("Your home state", STATES, index=STATES.index("MI"), key="home_state")
    states = st.multiselect("States you'd like (leave empty for any)", STATES, key="states")
    budget = st.number_input("Yearly budget ($)", min_value=0, value=40000, step=1000, key="budget")
    submitted = st.form_submit_button("Search")

if submitted:
    student = Student(degree, field, gpa, home_state, int(budget), tuple(states))

    st.subheader("Programs")
    results = find_programs(programs, student)
    if results:
        st.write(f"{len(results)} programs fit your budget, cheapest first.")
        st.dataframe(
            [{"University": r.program.university, "State": r.program.state, "Yearly cost": f"${r.cost:,}", "Chance": r.chance,
              "Website": r.program.website} for r in results],
            hide_index=True, column_config={"Website": st.column_config.LinkColumn()},
        )
    else:
        st.info("No programs fit your budget. Try a bigger budget.")
    st.caption("Yearly cost = tuition + living cost. Chance is an estimate from the school's "
               "acceptance rate and your GPA.")

    st.subheader("Scholarships")
    found = find_scholarships(scholarships, student)
    if found:
        st.dataframe(
            [{"Name": s.name, "Amount": f"${s.amount:,}", "Open to": s.open_to,
              "Deadline": s.deadline.isoformat(),
              "Website": s.website} for s in found],
            hide_index=True, column_config={"Website": st.column_config.LinkColumn()},
        )
    else:
        st.info("No scholarships match your degree, field and GPA.")

    st.subheader("Deadlines")
    dates = [(s.name, s.deadline) for s in found]
    dates += [(f"{r.program.university} application", r.program.deadline)
              for r in results]
    coming = deadlines.upcoming(dates, deadlines.today())
    for d in coming:
        if d.soon:
            st.warning(f"{d.name} is due in {d.days_left} days ({d.date:%b %d}).")
    if coming:
        st.dataframe([{"Name": d.name, "Date": d.date.isoformat(), "Days left": d.days_left}
                      for d in coming], hide_index=True)
    else:
        st.info("No upcoming deadlines.")
