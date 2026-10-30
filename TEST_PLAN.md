# Test plan

## Requirements

1. Only programs with the chosen degree and field are shown, and only in the chosen states
   (no states chosen = any state).
2. Only programs with a yearly cost at or under the budget are shown, cheapest first
   (same cost: A-Z by university).
3. Yearly cost = tuition + living cost, with in-state tuition if the student is from that state.
4. Chance comes from the school's acceptance rate and the student's GPA (table below).
5. A scholarship is shown only if the student's degree, field and GPA all fit. Biggest amount
   first, A-Z by name when amounts are the same.
6. Deadlines that have passed are hidden. A deadline 14 days away or less gets a warning.
7. A GPA outside 0-4 or a negative budget gives an error.
8. The database refuses bad data: empty names, a degree other than MS or PhD, negative costs,
   an acceptance rate outside 0-1, a GPA outside 0-4, a bad date or a value of the wrong type.

## Chance rule

Under 10% acceptance is always Reach. Otherwise:

| Acceptance rate | GPA under 3.0 | GPA 3.0 to 3.69 | GPA 3.7 or more |
|---|---|---|---|
| 10% to 24% | Reach | Reach | Match |
| 25% to 59% | Reach | Match | Safety |
| 60% or more | Match | Safety | Safety |

## User stories

1. A student finds MS programs they can afford.
2. A student finds PhD programs and fellowships.
3. A student is warned about a deadline that is coming soon.

## Tests

The tests are grouped by technique, one folder each:

| Folder | Technique | What it checks |
|---|---|---|
| `tests/unit/` | Unit testing | Each function on its own with a simple example |
| `tests/boundary_values/` | Equivalence partitioning and boundary values | GPA, acceptance rate, budget, scholarship minimum GPA, days until a deadline |
| `tests/decision_tables/` | Decision tables | The chance table above and the scholarship rules |
| `tests/control_flow/` | Control-flow (branch) testing | Every branch of `find_programs()` |
| `tests/data_flow/` | Data-flow testing | Each value in `find_programs()` from where it is set to where it is used |
| `tests/test_doubles/` | Test doubles | A spy on the cost function, mocks for the database and today's date |
| `tests/integration/` | Integration testing | Our code with the SQLite database, including its rules for bad data |
| `tests/system/` | System testing | The whole app page with Streamlit's AppTest |
| `tests/acceptance/` | Acceptance testing | The 3 user stories above |
| `tests/property_based/` | Property-based testing | Rules that hold for any input, with Hypothesis |

`tests/helpers.py` has the made-up programs, scholarships and students the tests share.

Boundary values and decision tables are black-box (functional) tests: they come from the
requirements above. Control-flow and data-flow tests are white-box: they come from the code.

Coverage: `pytest --cov` measures line and branch coverage and fails below 100%. GitHub Actions
runs every test on each push and saves the HTML coverage report (download "coverage-report"
from the run's page).

Current result: 110 tests passing, 100% line and branch coverage.
