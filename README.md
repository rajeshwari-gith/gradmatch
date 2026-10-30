# GradMatch

Our SE 413/513 Software Testing project (Track B), by Rajeshwari Galugu and Sai Nishith Jangili.

GradMatch helps students find college and grad programs they can afford. You enter your degree
(BS, MS or PhD), subject, GPA, budget and home state, and it shows:

- programs that fit your budget, with a Safety / Match / Reach chance
- PhD programs and their stipends
- scholarships you qualify for
- your deadlines, with a warning when one is close

Live app: https://gradmatch-rg.streamlit.app (it can take ~30 seconds to wake up)

## Data

`data/programs.csv` has about 45,000 programs. Most come from the US Department of Education
(IPEDS 2024). 24 rows were typed in by us. Things the government data doesn't have (average GPA,
stipend, deadline) are left blank, and the app says "not published" instead of guessing. More
details are in `data/README.md` and `data/SOURCES.md`.

## Run it

You need Python 3.11+.

```
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Tests

```
pytest            # all tests
pytest -m unit    # or integration, system, acceptance
pytest --cov      # with coverage
```

We have unit, integration, system (Streamlit AppTest) and acceptance tests, and all of them run
on GitHub Actions on every push. Coverage is 100%. Our test plan, mutation testing results and
the bugs we found are in `docs/` and `DEFECT_LOG.md`.

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

## Other tools

- `PYTHONPATH=src python -m gradmatch.ipeds_import ...` rebuilds the program rows from the IPEDS files
- `PYTHONPATH=src python -m gradmatch.link_check` finds broken website links in the data
- `PYTHONPATH=src python -m gradmatch.data_report` prints a short report on the data

## Folders

```
src/gradmatch/   the logic (cost, fit, search, scholarships, deadlines, API)
app/             the Streamlit app
data/            the CSV data files
tests/           all the tests
docs/            test plan and mutation testing results
```
