# Test plan

## Requirements

1. Only programs with the chosen degree and field are shown, and only in the chosen states
   (no states chosen = any state).
2. Only programs with a yearly cost at or under the budget are shown, cheapest first
   (same cost: A-Z by university).
3. Yearly cost is tuition + living cost, using in-state tuition if the student is from that state.
   A PhD stipend waives tuition and is taken off the living cost (never below $0).
   Funding: stipend at least the living cost = Fully funded, less = Partly funded,
   0 = No funding. PhD results are listed best funded first.
4. Chance is worked out from the school's acceptance rate and the student's GPA (table below).
   If the student gives a GRE score and the program lists its average GRE, a GRE 5 or more points
   above the average moves the chance one step easier, and more than 5 below one step harder.
5. A scholarship is shown only if the student's degree, field and GPA all fit, biggest amount first and A-Z by name when amounts are the same.
6. The deadline tracker shows the deadlines of the student's programs and scholarships.
   Deadlines that have passed are hidden. A deadline 14 days away or less gets a warning.
7. A GPA outside 0-4, a GRE outside 260-340 or a negative budget gives an error.
8. The database refuses bad data: empty names, a degree other than MS or PhD, negative costs,
   an acceptance rate outside 0-1, a GRE outside 260-340, a GPA outside 0-4, a bad date
   or a value of the wrong type.

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

| Folder | Kind of test | Files |
|---|---|---|
| `tests/unit/` | One module on its own | `test_cost.py`, `test_fit.py`, `test_search.py`, `test_scholarships.py`, `test_deadlines.py` |
| `tests/integration/` | Parts working together: the SQLite database and the API | `test_database.py`, `test_api.py` |
| `tests/system/` | The whole app page, with Streamlit's AppTest | `test_app.py` |
| `tests/acceptance/` | The 3 user stories above | `test_user_stories.py` |

`tests/helpers.py` has the made-up programs, scholarships and students the tests share.

Methods used: equivalence partitioning and boundary values (GPA, GRE, rate, budget, days left),
decision tables (chance, scholarships), branch coverage, mocks (database, today's date)
and property-based tests with Hypothesis.

Run with `pytest --cov`. GitHub Actions runs the tests on every push and saves the HTML
coverage report (download "coverage-report" from the run's page).

Current result: 145 tests passing, 100% line and branch coverage.
