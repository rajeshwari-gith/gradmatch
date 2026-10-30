# GradMatch

SE 413/513 Software Testing project, Fall 2026
Rajeshwari Galugu and Sai Nishith Jangili

A Streamlit app for students planning grad school. You enter your degree (MS or PhD), field,
GPA, home state, the states you'd like and your yearly budget. The app shows:

- programs you can afford, cheapest first, with a Safety / Match / Reach chance
- scholarships and fellowships you can apply for
- program and scholarship deadlines, with a warning when one is 2 weeks away or less

Live app: https://gradmatch-rg.streamlit.app

## Features

| Feature | File | Who |
|---|---|---|
| Program search and yearly cost | `search.py`, `cost.py` | Rajeshwari |
| Admission chance | `fit.py` | Rajeshwari |
| Scholarships | `scholarships.py` | Sai Nishith |
| Deadline tracker | `deadlines.py` | Sai Nishith |

Also: the page `app/streamlit_app.py` and CI (Rajeshwari), and the SQLite database
`database.py` (Sai Nishith). All code is in `src/gradmatch/`. The tests are in `tests/`, one
folder per testing technique. See [TEST_PLAN.md](TEST_PLAN.md).

## Running

Python 3.11 or newer.

```
pip install -r requirements.txt
streamlit run app/streamlit_app.py
pytest --cov              # all tests, with coverage (report in htmlcov/index.html)
pytest tests/unit         # only one folder
```

## Data

All data is in one SQLite database, `data/gradmatch.db`, with two tables, `programs` and
`scholarships`. The table rules in `database.py` refuse bad values, like a negative cost or a
GPA above 4.

**Programs**
- 159 MS and PhD programs.
- 4 subjects: Computer Science, Electrical Engineering, Mechanical Engineering, Statistics.
- 5 states: Illinois, Indiana, Michigan, Ohio, Wisconsin.
- Tuition, school names, websites and acceptance rates: government data (IPEDS 2024).
  The acceptance rate is the whole school's rate, not the program's.
- Living cost: the MERIC cost of living index for each state.
- Deadline: our estimate, because the government data does not have it.
  December 15, 2026 for PhD and February 1, 2027 for MS.

**Scholarships**
- 7 national scholarships and fellowships.
- Each one says who can apply (for example "US citizens" or "Everyone").
- The amounts and deadlines are estimates.

All results are estimates. They do not promise admission.
