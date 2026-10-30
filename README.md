# GradMatch

SE 413/513 Software Testing project, Fall 2026
Rajeshwari Galugu and Sai Nishith Jangili

A Streamlit app for students planning grad school. You enter your degree (MS or PhD), field,
GPA, GRE score (optional), home state, the states you'd like, budget and citizenship. The app shows:

- programs you can afford, cheapest first (PhD: best funded first), with a Safety / Match / Reach chance
- scholarships and fellowships you can apply for
- program and scholarship deadlines, with a warning when one is 2 weeks away or less

The same search is also available as a small REST API.

Live app: https://gradmatch-rg.streamlit.app

## Features

| Feature | Files | Who |
|---|---|---|
| Program search, yearly cost and PhD funding | `search.py`, `cost.py` | Rajeshwari |
| Admission chance | `fit.py` | Rajeshwari |
| Scholarships | `scholarships.py` | Sai Nishith |
| Deadline tracker | `deadlines.py` | Sai Nishith |

Also: the page `app/streamlit_app.py` and CI (Rajeshwari), and the data loader
`data_loader.py`, the SQLite database `database.py` and the API `api.py` (Sai Nishith). All code is in `src/gradmatch/`. The tests are in `tests/`, one folder per kind of test
(unit, integration, system, acceptance). See [TEST_PLAN.md](TEST_PLAN.md).

## Running

Python 3.11 or newer.

```
pip install -r requirements.txt
streamlit run app/streamlit_app.py
uvicorn --app-dir src gradmatch.api:app     # API at http://127.0.0.1:8000/docs
pytest --cov                                # coverage report in htmlcov/index.html
pytest tests/unit                           # only one kind of test
```

## Data

**Programs** (`data/programs.csv`)
- 159 MS and PhD programs.
- 4 subjects: Computer Science, Electrical Engineering, Mechanical Engineering, Statistics.
- 5 states: Illinois, Indiana, Michigan, Ohio, Wisconsin.

Where the numbers come from:
- Tuition, school names and websites: government data (IPEDS 2024).
- Acceptance rate: also IPEDS. It is the whole school's rate, not the program's.
- Living cost: the MERIC cost of living index for each state.
- Stipend, average GRE and deadline: our own estimates, because the government data
  does not have them.

How we estimated:
- Stipend: MS gets $0. PhD gets $30,000 at harder schools (accept under 50%), $24,000 at others.
- Average GRE: 320 at harder schools, 310 at others.
- Deadline: December 15, 2026 for PhD. February 1, 2027 for MS.

**Scholarships** (`data/scholarships.csv`)
- 7 national scholarships and fellowships.
- The amounts and deadlines are estimates.

All results are estimates. They do not promise admission.
