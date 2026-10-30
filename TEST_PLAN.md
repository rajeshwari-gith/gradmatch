# Test plan

## Requirements

- **REQ-1** Only programs with the chosen degree and field are shown, and only in the chosen
  states (no states chosen = any state).
- **REQ-2** Only programs with a yearly cost at or under the budget are shown, cheapest first
  (same cost: A-Z by university).
- **REQ-3** Yearly cost = tuition + living cost, with in-state tuition if the student is from that state.
- **REQ-4** Chance comes from the school's acceptance rate and the student's GPA (table C below).
- **REQ-5** A scholarship is shown only if the student's degree, field and GPA all fit (table S
  below). Biggest amount first, A-Z by name when amounts are the same.
- **REQ-6** Deadlines that have passed are hidden. A deadline 14 days away or less gets a warning.
- **REQ-7** A GPA outside 0-4 or a negative budget gives an error.
- **REQ-8** The database refuses bad data: empty names, a degree other than MS or PhD, negative
  costs, an acceptance rate outside 0-1, a GPA outside 0-4, a bad date or a value of the wrong type.

## Decision table C: chance (REQ-4)

"—" means the condition does not matter for that rule.

| Rule | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 |
|---|---|---|---|---|---|---|---|---|
| Acceptance rate | under 10% | 10-24% | 10-24% | 25-59% | 25-59% | 25-59% | 60%+ | 60%+ |
| GPA | — | 3.7+ | under 3.7 | 3.7+ | 3.0-3.69 | under 3.0 | 3.0+ | under 3.0 |
| **Chance** | Reach | Match | Reach | Safety | Match | Reach | Safety | Match |

## Decision table S: scholarship shown? (REQ-5)

| Rule | S1 | S2 | S3 | S4 |
|---|---|---|---|---|
| Degree fits | no | yes | yes | yes |
| Field fits ("Any" fits every field) | — | no | yes | yes |
| GPA at least the minimum | — | — | no | yes |
| **Shown** | no | no | no | yes |

## User stories

1. A student finds MS programs they can afford.
2. A student finds PhD programs and fellowships.
3. A student is warned about a deadline that is coming soon.

## Tests

The tests are grouped by technique, one folder each:

| Folder | Technique | What it checks |
|---|---|---|
| `tests/unit/` | Unit testing | One file per feature (`test_cost.py`, `test_fit.py`, `test_search.py`, `test_scholarships.py`, `test_deadlines.py`), each function with a simple example |
| `tests/boundary_values/` | Equivalence partitioning and boundary values | GPA, acceptance rate, budget, scholarship minimum GPA, days until a deadline |
| `tests/decision_tables/` | Decision tables | Tables C and S above, one test per rule |
| `tests/control_flow/` | Control-flow (branch) testing | Every branch of `find_programs()` |
| `tests/data_flow/` | Data-flow testing | Each value in `find_programs()` from where it is set to where it is used |
| `tests/test_doubles/` | Test doubles | A spy on the cost function, mocks for the database and today's date |
| `tests/integration/` | Integration testing | Our code with the SQLite database, including its rules for bad data |
| `tests/system/` | System testing | The whole app page with Streamlit's AppTest |
| `tests/acceptance/` | Acceptance testing | The 3 user stories above |
| `tests/property_based/` | Property-based testing | Rules that hold for any input, with Hypothesis |

Every test name starts with the requirement it checks (for example `test_req4_chance_table`),
and each decision-table test has the rule ID (for example `C2-10-24%-strong-gpa`).

## Traceability

| Requirement | Technique | Tests |
|---|---|---|
| REQ-1 | Control flow, boundary values, system | `test_req1_*`, `test_search_shows_programs_and_scholarships` |
| REQ-2 | Boundary values, control flow, data flow | `test_req2_*` |
| REQ-3 | Unit, data flow | `test_req3_*` |
| REQ-4 | Decision table C, boundary values, data flow, property-based | `test_req4_*`, `test_results_always_fit_the_student` |
| REQ-5 | Decision table S, boundary values, unit | `test_req5_*`, `test_find_scholarships` |
| REQ-6 | Boundary values, test doubles (mocked date), acceptance | `test_req6_*`, `test_mock_database`, story 3 |
| REQ-7 | Boundary values, control flow | `test_req7_*` |
| REQ-8 | Integration (SQLite) | `test_req8_database_refuses_bad_data` |
| User stories 1-3 | Acceptance | `tests/acceptance/test_user_stories.py` |

Expected values come from the requirements and tables above, not from running the code.

`tests/helpers.py` has the made-up programs, scholarships and students the tests share.

Boundary values and decision tables are black-box (functional) tests: they come from the
requirements above. Control-flow and data-flow tests are white-box: they come from the code.

Coverage: `pytest --cov` measures line and branch coverage and fails below 100%. GitHub Actions
runs every test on each push and saves the HTML coverage report (download "coverage-report"
from the run's page).

Current result: 45 tests passing, 100% line and branch coverage.
