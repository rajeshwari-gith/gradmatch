# GradMatch

GradMatch helps students plan for graduate school. A student enters their degree (MS or PhD),
field, GPA, test scores, home state, citizenship and yearly budget. The app then shows:

- **Programs** they can afford, labeled **Safety / Match / Reach**, with the real yearly cost
  (in-state or out-of-state tuition plus living costs, minus any stipend; tuition is assumed
  waived for funded PhD programs), a funding label, a TOEFL warning and the application deadline.
- **Scholarships** and fellowships they qualify for.
- **Deadlines** for their programs and scholarships, soonest first, with a warning when one is
  within 14 days, and a calendar (.ics) download.
- A **cost breakdown** for any program, a cost-versus-GPA chart and a CSV download.

SE 413/513 Software Testing, Fall 2026 – Track B project by
Rajeshwari Galugu and Sai Nishith Jangili.

**All numbers are estimates.** Average GPA, acceptance rate, funding and the fit labels are
estimates, PhD costs leave out mandatory student fees, and most data rows are not yet verified
against the official program pages (see `data/SOURCES.md` for the current count). Always check
the official program page.

Built with Python, Streamlit, Altair and plain CSV data files.

## Install

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

## Run the tests

```
pytest                                   # all tests (about 400)
pytest -m unit                           # one level: unit, integration, system or acceptance
pytest --cov --cov-report=term-missing   # with line and branch coverage
```

| Level | What it checks | Folder |
|---|---|---|
| Unit | one function or module at a time: validation, cost, fit, funding, search, scholarships, deadlines, loader, exports, cards | `tests/unit/` |
| Integration | modules working together, from CSV files to search, cards and exports; real data checks; the link checker | `tests/integration/` |
| System | the whole Streamlit app, driven with Streamlit's `AppTest` | `tests/system/` |
| Acceptance | the three user stories from the project specification | `tests/acceptance/` |

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

## Project layout

```
src/gradmatch/   application code (business logic, no Streamlit)
app/             Streamlit user interface
data/            programs, scholarships and living costs (CSV), plus SOURCES.md
tests/           unit, integration, system and acceptance tests
docs/            notes, for example the mutation testing results
DEFECT_LOG.md    defects found by testing, with how they were found and fixed
CONTRIBUTING.md  the team's rules, data formats and business rules
```

See `CONTRIBUTING.md` for the data formats and the rules the tests are written against.
