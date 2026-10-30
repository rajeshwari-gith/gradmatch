# Test plan

## What we test

The rules (cost, Safety/Match/Reach, funding, scholarships, deadlines), reading the data files,
the data import, the Streamlit app and the API. We don't test whether the schools' own numbers
are right, and we don't do load testing.

## Test levels

| Level | Folder | How |
|---|---|---|
| Unit (825) | `tests/unit/` | one function at a time, with small made-up programs |
| Integration (150) | `tests/integration/` | CSV files through the loader, search and exports; the API; checks on the real data |
| System (94) | `tests/system/` | the whole app with Streamlit's AppTest, on fixed test data and a fixed date |
| Acceptance (11) | `tests/acceptance/` | our 4 user stories, checking what the student sees |

## Techniques

- **Boundary values**: budget exactly at the cost, deadlines at 0/14/15 days, GPA limits
  (`test_affordability_boundary`, `test_deadline_status_boundaries`, `test_gpa_difference_boundaries`)
- **Equivalence classes**: valid vs invalid input, good vs bad CSV rows
- **Decision tables**: scholarship eligibility, who pays in-state tuition (`test_decision_table`)
- **Property-based tests** (Hypothesis): things that must always be true, like a cost never below 0
  (`test_yearly_cost_is_never_negative`, `test_no_result_is_ever_over_budget`)
- **Regression tests**: every bug in `DEFECT_LOG.md` got a test first (`test_funded_phd_pays_no_tuition` for D-001)
- **Mutation testing** (mutmut): to check our tests actually catch mistakes, see `mutation-testing.md`

## Coverage

Our goal is 100% line and branch coverage of `src/gradmatch` and `app/`, and we're at 100%.
Run `pytest --cov`. GitHub Actions shows the numbers on every push.

## Which tests cover what

| Feature | Code | Tests |
|---|---|---|
| Profile form checks | `validation.py` | `test_validation.py`, `test_profile_form.py` |
| Cost, in-state rule, funded PhD | `cost.py`, `search.py` | `test_cost.py`, `test_search.py`, `test_results_page.py` |
| Safety / Match / Reach | `fit.py` | `test_fit.py` |
| Funding label | `funding.py` | `test_funding.py` |
| Scholarships | `scholarships.py` | `test_scholarships.py`, story 2 |
| Deadlines, warning window, own deadlines | `deadlines.py` | `test_deadlines.py`, story 3 |
| Stars | `starred.py` | `test_starred.py`, `test_results_page.py` |
| CSV and calendar downloads | `exports.py` | `test_exports.py`, `test_pipeline.py` |
| Reading the data | `data_loader.py` | `test_data_loader.py`, `test_data_errors.py` |
| Screens | `screens.py`, `components.py`, `theme.py` | `test_screens.py`, `test_components.py`, `test_theme.py` |
| Data import | `ipeds_import.py` | `test_ipeds_import.py`, `test_ipeds_import_cli.py` |
| API | `api.py` | `test_api.py`, `test_readme_examples.py` |
| Bachelor's search | `search.py` | `test_bachelors.py`, story 4 |
