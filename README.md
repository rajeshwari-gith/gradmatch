# GradMatch

GradMatch helps students plan for college and graduate school. A student enters the degree
they want (**BS**, **MS** or **PhD**), one of **130 fields**, GPA, test scores (GRE and TOEFL for
graduate programs; **SAT** and **ACT** for bachelor's programs), home state, citizenship and
yearly budget. The app then shows:

- **Programs** they can afford, labeled **Safety / Match / Reach**, with the real yearly cost
  (in-state or out-of-state tuition plus living costs, minus any stipend; tuition is assumed
  waived for funded PhD programs), a funding label, a TOEFL warning and the application deadline.
- **Scholarships** and fellowships they qualify for.
- **Deadlines** for their programs and scholarships, soonest first, with a warning when one is
  within 14 days, and a calendar (.ics) download.
- A **cost breakdown** for any program, a cost-versus-GPA chart and a CSV download.

SE 413/513 Software Testing, Fall 2026 – Track B project by
Rajeshwari Galugu and Sai Nishith Jangili.

**Live app:** https://gradmatch-rg.streamlit.app (it may take about 30 seconds to wake up if
nobody has opened it for a while).

## The data

`data/programs.csv` has **45,424 programs**:

- **24 hand-entered** Computer Science and Data Science MS/PhD rows (`source` blank or `estimate`,
  or `official-page` once a person has checked them). `data/SOURCES.md` tracks how many of these
  24 have been checked on the official program page.
- **45,400 imported** rows from the official 2024 US Department of Education data (IPEDS,
  `source=ipeds`): 29,829 bachelor's, 12,426 master's and 3,145 PhD programs at 2,023 schools.

The 130 fields are listed in `data/README.md` (they are the `CIP_FIELDS` in
`src/gradmatch/ipeds_import.py`).

**Read the numbers with care.** In the imported rows, tuition is the school-wide yearly rate plus
required fees (not a per-program price), and a blank cell means "not published" (admitted GPA,
stipend and deadline are never in the government data). In the hand-entered rows, average GPA and
acceptance rate are estimates, and the app labels them "(est.)". PhD costs leave out mandatory
student fees. Always check the official program page. See `data/README.md` for what every column
means.

Built with Python, Streamlit, Altair, FastAPI and plain CSV data files.

## Install

Needs **Python 3.11 or newer** (check with `python3 --version`).

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the app

```
streamlit run app/streamlit_app.py
```

Light and dark themes are in the app menu (three dots, Settings, Theme). Two settings help with
demos: `GRADMATCH_TODAY=2026-10-24` fixes today's date and `GRADMATCH_DATA_DIR=some/folder` uses a
different data folder.

## Use the REST API

The same search is available as a JSON API (FastAPI). `uvicorn`, the server that runs it, is
installed with `requirements.txt`:

```
PYTHONPATH=src uvicorn gradmatch.api:app --reload      # http://127.0.0.1:8000, docs at /docs
```

The examples below are run by `tests/integration/test_readme_examples.py`, so they stay correct.

| Call | What it returns |
|---|---|
| `GET /health` | `{"status": "ok"}` |
| `GET /programs?field=&degree=&state=&limit=&offset=` | programs in file order, filtered by exact field, degree (`BS`, `MS`, `PhD`) and state; at most `limit` (1–1000, default 100) after skipping `offset` (default 0) |
| `POST /match?limit=` | `{"total_programs": n, "programs": [...], "scholarships": [...]}` for a student profile; the first `limit` programs (1–1000, default 50) with cost, fit and funding |
| `GET /deadlines?today=YYYY-MM-DD&urgent_days=` | `{"urgent_days": n, "glance": {...}, "deadlines": [...]}`: open program and scholarship deadlines, soonest first, each with its status for the warning window `urgent_days` (0–90, default 14), and the counts `within_window`, `within_90`, `later` and `passed` |
| `GET /starred` | the starred keys, sorted |
| `POST /starred` | star one item; the body is `{"key": "program:<id>"}` (or `scholarship:<id>`, `deadline:<name>`); returns the starred keys |
| `DELETE /starred?key=` | take the star away from one item; returns the starred keys |

Examples:

```
curl "http://127.0.0.1:8000/programs?field=Data%20Science&degree=MS&state=MI&limit=2"

curl -X POST "http://127.0.0.1:8000/match?limit=3" -H "Content-Type: application/json" \
     -d '{"degree_sought": "BS", "gpa": 3.6, "field": "Computer Science", "home_state": "MI",
          "citizenship": "US", "annual_budget": 40000, "sat": 1300}'

curl "http://127.0.0.1:8000/deadlines?today=2026-10-27&urgent_days=7"

curl -X POST "http://127.0.0.1:8000/starred" -H "Content-Type: application/json" \
     -d '{"key": "program:GVSU-MSCS"}'

curl -X DELETE "http://127.0.0.1:8000/starred?key=program:GVSU-MSCS"
```

The starred items are kept in the server's memory only: everyone using the same server shares
them, and they are gone when the server restarts. Starring an item twice, or removing a star that
is not there, is not an error. A key that does not start with `program:`, `scholarship:` or
`deadline:` gives 422.

The profile fields are `degree_sought`, `gpa`, `field`, `home_state`, `citizenship` (`US`, `PR` or
`International`) and `annual_budget`, plus optional `preferred_states`, `gre`, `toefl`, `sat`, `act`
and `special`. An invalid profile, limit, offset or date gives 422; missing values are `null`.

## Import the official data

`src/gradmatch/ipeds_import.py` builds rows from the IPEDS files HD, COST1, C_A and (optionally)
ADM. See `docs/official-data-import.md` for where to download them and the rules it follows.

```
PYTHONPATH=src python -m gradmatch.ipeds_import --hd HD2024.csv --cost cost1_2024.csv \
    --completions C2024_a.csv --admissions ADM2024.csv --data data \
    --output data/programs_ipeds.csv --report data/tuition_check.csv
```

Add `--merge` to also put the new rows into `data/programs.csv`; it replaces the rows of an
earlier import, so running it again gives the same file, and never touches hand-entered rows.

## Run the tests

```
pytest                                   # all tests (about 820)
pytest -m unit                           # one level: unit, integration, system or acceptance
pytest --cov --cov-report=term-missing   # with line and branch coverage
```

All tests pass with 100% line and branch coverage of `src/gradmatch` and the app.

| Level | What it checks | Folder |
|---|---|---|
| Unit | one function or module at a time: validation, cost, fit, funding, search, scholarships, deadlines, loader, exports, cards | `tests/unit/` |
| Integration | modules working together, from CSV files to search, cards and exports; the REST API; real data checks; the link checker | `tests/integration/` |
| System | the whole Streamlit app, driven with Streamlit's `AppTest` | `tests/system/` |
| Acceptance | the user stories from the project specification, plus a bachelor's search story | `tests/acceptance/` |

Test techniques used: boundary-value analysis, equivalence partitioning, decision tables,
property-based testing (Hypothesis) and mutation testing (see `docs/mutation-testing.md`).
Tests never read the real data files, except the checks in `tests/integration/test_real_data.py`.
Every push runs all tests on GitHub Actions; the run page shows the test count and the
coverage table.

## Check the data links

Every row in `data/` has an official `website`. After adding or editing rows, run this on
your own computer (it needs internet) to find links that no longer open:

```
PYTHONPATH=src python -m gradmatch.link_check
```

It prints every broken link and exits with 1 if there are any. It never changes the data.

## Data quality report

```
PYTHONPATH=src python -m gradmatch.data_report
```

Prints rows by source, degree and field, how many cells are blank ("not published") in each
column of the imported rows, duplicate ids, websites that are not https, and the "Verified"
counts from `data/SOURCES.md`. It exits with 1 if there are duplicate ids or non-https links.
A dated snapshot is in `docs/data-report.md`.

## Project layout

```
src/gradmatch/   application code (business logic, no Streamlit)
app/             Streamlit user interface
data/            programs, scholarships and living costs (CSV), plus SOURCES.md
tests/           unit, integration, system and acceptance tests
docs/            test plan, how it works, mutation testing, official-data import, data report
DEFECT_LOG.md    defects found by testing, with how they were found and fixed
CONTRIBUTING.md  the team's rules, data formats and business rules
```

See `CONTRIBUTING.md` for the data formats and the rules the tests are written against.

## Documentation

| Document | What it covers |
|---|---|
| [`docs/how-it-works.md`](docs/how-it-works.md) | one search, step by step, and the design choices behind it |
| [`docs/test-plan.md`](docs/test-plan.md) | test levels, techniques, coverage goal and which tests cover each feature |
| [`docs/mutation-testing.md`](docs/mutation-testing.md) | mutation testing results and the tests it led to |
| [`docs/official-data-import.md`](docs/official-data-import.md) | how the official government data is imported |
| [`docs/data-report.md`](docs/data-report.md) | a dated snapshot of the data quality report |
| [`DEFECT_LOG.md`](DEFECT_LOG.md) | every defect found by testing, with severity and status |
