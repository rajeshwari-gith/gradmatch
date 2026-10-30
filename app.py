from pathlib import Path

import streamlit as st

from database import connect, get_programs, get_scholarships
from programs import find_programs
from scholarships import find_scholarships, today, upcoming

DATABASE = Path(__file__).parent / "data" / "gradmatch.db"
STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "IA", "ID", "IL",
          "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE",
          "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT",
          "VA", "VT", "WA", "WI", "WV", "WY"]

st.title("GradMatch")
st.write("Find graduate programs you can afford, scholarships you can apply for, and their deadlines.")

connection = connect(DATABASE)
programs = get_programs(connection)
scholarships = get_scholarships(connection)
connection.close()

with st.form("profile"):
    degree = st.radio("Degree", ["MS", "PhD"], horizontal=True, key="degree")
    field = st.selectbox("Field", sorted({p["field"] for p in programs}), key="field")
    gpa = st.number_input("Your GPA", min_value=0.0, max_value=4.0, value=3.5, step=0.1, key="gpa")
    home_state = st.selectbox("Your home state", STATES, index=STATES.index("MI"), key="home_state")
    states = st.multiselect("States you'd like (leave empty for any)", STATES, key="states")
    budget = st.number_input("Yearly budget ($)", min_value=0, value=40000, step=1000, key="budget")
    submitted = st.form_submit_button("Search")

if submitted:
    student = {"degree": degree, "field": field, "gpa": gpa, "home_state": home_state,
               "budget": int(budget), "states": states}

    st.subheader("Programs")
    results = find_programs(programs, student)
    if results:
        st.write(f"{len(results)} programs fit your budget, cheapest first.")
        st.dataframe([{"University": r["program"]["university"], "State": r["program"]["state"],
                       "Yearly cost": r["cost"], "Chance": r["chance"],
                       "Website": r["program"]["website"]} for r in results])
    else:
        st.info("No programs fit your budget. Try a bigger budget.")

    st.subheader("Scholarships")
    found = find_scholarships(scholarships, student)
    if found:
        st.dataframe([{"Name": s["name"], "Amount": s["amount"], "Open to": s["open_to"],
                       "Deadline": s["deadline"], "Website": s["website"]} for s in found])
    else:
        st.info("No scholarships match your degree, field and GPA.")

    st.subheader("Deadlines")
    dates = [(s["name"], s["deadline"]) for s in found]
    dates += [(r["program"]["university"] + " application", r["program"]["deadline"])
              for r in results]
    coming = upcoming(dates, today())
    for d in coming:
        if d["soon"]:
            st.warning(f"{d['name']} is due in {d['days_left']} days.")
    if coming:
        st.dataframe([{"Name": d["name"], "Date": d["date"], "Days left": d["days_left"]}
                      for d in coming])
    else:
        st.info("No upcoming deadlines.")
