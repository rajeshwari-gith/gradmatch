# Test plan and requirement traceability

This document says **what we test, how, and which tests cover which feature**. It follows the
project guidelines (unit, integration, system and acceptance levels, named design techniques,
a coverage goal and a defect log). Numbers are from the latest run on `main`; the GitHub Actions
page shows the live ones.

## 1. Scope

| In scope | Not in scope |
|---|---|
| The search and cost rules, fit labels, funding labels | Whether a school's published numbers are correct (we import them as published) |
| Scholarship eligibility, deadline countdown, exports | Real-time university web pages (the link checker is run by hand, never in CI) |
| Reading and checking the data files, and the official-data importer | Browser look and feel beyond what Streamlit's `AppTest` can drive |
| The Streamlit app, the REST API and the lookup tool | Load testing |

## 2. Levels and where they live

| Level | Goal | Folder | Approach |
|---|---|---|---|
| Unit | One function or module alone | `tests/unit/` | Small objects built by helpers in `tests/conftest.py`; no files except tiny CSVs in a temp folder |
| Integration | Modules together | `tests/integration/` | CSV text through loader, search, scholarships, cards, exports; the REST API with FastAPI's `TestClient`; checks over the real data |
| System | The whole Streamlit app | `tests/system/` | `AppTest` drives the real page on fixed data (`tests/data_fixtures.py`) and a fixed date |
| Acceptance | A user story from the proposal | `tests/acceptance/` | Four stories, written in what the student sees |

## 3. Design techniques and an example of each

| Technique | Where we use it | Example test |
|---|---|---|
| Boundary-value analysis | GPA 0 and 4, SAT 400 and 1600, budget at the cost, deadline at 0, 1, 14, 15, 30, 31 days, SAT at the 25th/75th percentile | `test_affordability_boundary`, `test_gpa_difference_boundaries`, `test_deadline_status_boundaries` |
| Equivalence partitioning | Kinds of valid and invalid input, kinds of bad CSV cells, citizenship groups | `test_programs_bad_date_is_rejected`, `test_invalid_degrees` |
| Decision tables | Reach/Match/Safety, who pays which tuition, scholarship eligibility, PhD waiver | `test_decision_table` (scholarships), `test_phd_with_stipend_has_tuition_waived` |
| Property-based testing (Hypothesis) | Rules that must always hold | `test_yearly_cost_is_never_negative`, `test_no_result_is_ever_over_budget` |
| Regression tests | Each defect gets a failing test first | `test_funded_phd_pays_no_tuition` (D-001), `test_international_student_pays_out_of_state_tuition_even_with_a_matching_home_state` (D-003) |
| Mutation testing | Are the tests strong? | `docs/mutation-testing.md` |

## 4. Coverage goal and how it is measured

- **Goal:** 100% of lines and branches of `src/gradmatch` and `app/` (stricter than the usual 85%).
- **Tool:** `pytest-cov` with `branch = true` (see `pyproject.toml`).
- **Command:** `pytest --cov --cov-branch --cov-report=term-missing`.
- **Reported:** every GitHub Actions run prints the test count and a coverage table on its summary page.

## 5. Traceability: feature to tests

| Feature | Rule or source | Main tests |
|---|---|---|
| Input checks | `validation.py` | `tests/unit/test_validation.py`, `tests/system/test_profile_form.py` |
| Yearly and total cost, in-state rule, funded PhD, international rule | `cost.py`, `search.py` | `tests/unit/test_cost.py`, `tests/unit/test_search.py`, `tests/system/test_results_page.py` |
| Safety / Match / Reach, SAT and ACT percentiles, unknown fit | `fit.py` | `tests/unit/test_fit.py` |
| Funding label | `funding.py` | `tests/unit/test_funding.py` |
| Scholarship eligibility | `scholarships.py` | `tests/unit/test_scholarships.py`, `tests/acceptance/test_user_stories.py` (story 2) |
| Deadlines and urgent warning | `deadlines.py` | `tests/unit/test_deadlines.py`, story 3 |
| CSV and calendar downloads | `exports.py` | `tests/unit/test_exports.py`, `tests/integration/test_pipeline.py` |
| Reading data, bad-row messages, "not published" cells | `data_loader.py` | `tests/unit/test_data_loader.py`, `tests/system/test_data_errors.py` |
| Rows, cards, badges, colours, safe links | `screens.py`, `components.py`, `presentation.py`, `app/theme.py` | `tests/unit/test_screens.py`, `tests/unit/test_components.py`, `tests/unit/test_presentation.py`, `tests/unit/test_theme.py` |
| Stars, warning window, your own deadlines | `starred.py`, `deadlines.py`, app | `tests/unit/test_starred.py`, `tests/unit/test_deadlines.py`, `tests/system/test_results_page.py` |
| Official-data import (130 fields, three degree levels) | `ipeds_import.py` | `tests/unit/test_ipeds_import.py`, `tests/unit/test_ipeds_import_cli.py` |
| Verified-row tool | `apply_lookup.py` | `tests/unit/test_apply_lookup.py` |
| Bachelor's search | `search.py`, app | `tests/system/test_bachelors.py`, story 4 |
| Rows with unpublished values | all | `tests/system/test_unpublished_values.py`, fit and cost unit tests |
| REST API | `api.py` | `tests/integration/test_api.py` |
| Real data sanity (ids, ranges, degrees, imported rows) | data files | `tests/integration/test_real_data.py` |
| Stale-code fix after a deploy | `app/freshness.py` | `tests/unit/test_freshness.py` |

## 6. Tools

Python 3.11+, `pytest`, `pytest-cov`, Hypothesis, `mutmut`, Streamlit `AppTest`, FastAPI `TestClient`,
GitHub Actions (`.github/workflows/tests.yml`).

## 7. Risks and how we handle them

| Risk | What we do |
|---|---|
| Tests depend on the clock | "Today" is always passed in; the app reads `GRADMATCH_TODAY` for demos and tests |
| Tests depend on the real data | Only `test_real_data.py` reads it; every other test uses small fixed data |
| Streamlit keeps old code in memory after a deploy | `app/freshness.py` and its tests |
| A bug returns after a fix | Each defect has a regression test (see `DEFECT_LOG.md`) |
| Slow tests | The real-data checks load the data once per file; the full suite runs in about two minutes |

## 8. Defects

Four defects were found by tests and fixed (the fourth, a bare carriage return in a calendar name, was found by a property-based test); the log with severity and the finding test is in
[`DEFECT_LOG.md`](../DEFECT_LOG.md).

## 9. How to run everything

```
pip install -r requirements.txt
pytest --cov --cov-branch                # all tests with coverage
pytest tests/unit                        # one level
pip install mutmut && mutmut run         # mutation testing
```
