# GradMatch

**Course:** SE 413/513 – Software Testing, Fall 2026
**Track:** B – Testing a Newly-Developed System
**Team Members:** Rajeshwari Galugu and Sai Nishith Jangili

## Project Description

GradMatch is a simple Python app that helps students plan for graduate school. A student enters
their degree (MS or PhD), field, GPA, home state, the states they like and a yearly budget. The
app shows:

- programs they can afford, cheapest first, with a Safety / Match / Reach chance
- scholarships and fellowships they can apply for
- program and scholarship deadlines, with a warning when one is 2 weeks away or less

Live app: https://gradmatch-rg.streamlit.app

## Features

| Feature | File | Owner |
|---|---|---|
| Program search and yearly cost | `programs.py` | Rajeshwari |
| Admission chance | `programs.py` | Rajeshwari |
| Scholarships | `scholarships.py` | Sai Nishith |
| Deadline tracker | `scholarships.py` | Sai Nishith |

Also: the page `app.py` and CI (Rajeshwari), and the SQLite database `database.py`
(Sai Nishith).

## Technologies Used

Python, Streamlit, SQLite, pytest and pytest-cov.

## Installation

`python -m pip install -r requirements.txt`

## Run the Application

`python -m streamlit run app.py`

## Run Automated Tests

`python -m pytest -v`

Use `python -m pytest`, not plain `pytest`, so Python can find the code files.

The tests are in `tests/`, one folder per testing technique. See [TEST_PLAN.md](TEST_PLAN.md), which also has the defect log.

## Generate Coverage Report

`python -m pytest --cov=app --cov=programs --cov=scholarships --cov=database --cov-branch --cov-report=term-missing --cov-report=html`

The HTML report is saved in `htmlcov/index.html`.

## Data

All data is in one SQLite database, `data/gradmatch.db`, with two tables, `programs` and
`scholarships`. The table rules in `database.py` refuse bad values, like a negative cost or a
GPA above 4.

- **Programs:** 159 MS and PhD programs in Computer Science, Electrical Engineering, Mechanical
  Engineering and Statistics, in Illinois, Indiana, Michigan, Ohio and Wisconsin. Tuition,
  school names, websites and acceptance rates come from government data (IPEDS 2024); the
  acceptance rate is the whole school's rate. Living cost comes from the MERIC cost of living
  index. Deadlines are our estimate: December 15, 2026 for PhD and February 1, 2027 for MS.
- **Scholarships:** 7 national scholarships and fellowships. Each one says who can apply. The
  amounts and deadlines are estimates.

All results are estimates. They do not promise admission.

## Current Testing Results

15 automated tests pass, with 100% line and branch coverage. GitHub Actions runs them on
every push and saves the coverage report.

## Project Status

The app, the database and the unit, integration, system and acceptance tests are done.
Next: keep the defect log up to date, then the final report and the presentation.
