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
  costs, an acceptance rate outside 0-1, a GPA outside 0-4 or a bad date.

## Decision table C: chance (REQ-4)

"—" means it does not matter.

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

| Folder | Technique | Test |
|---|---|---|
| `tests/unit/` | Unit testing | One file per feature: `test_cost.py`, `test_fit.py`, `test_search.py`, `test_scholarships.py`, `test_deadlines.py` |
| `tests/boundary_values/` | Equivalence partitioning and boundary values | `test_boundary_values` |
| `tests/decision_tables/` | Decision tables | `test_decision_tables` (tables C and S above) |
| `tests/control_flow/` | Control-flow (branch) testing | `test_every_branch_of_find_programs` |
| `tests/data_flow/` | Data-flow testing | `test_values_flow_through_find_programs` |
| `tests/test_doubles/` | Test doubles (mocks) | `test_app_with_mocked_database_and_date` |
| `tests/integration/` | Integration testing (SQLite) | `test_database` |
| `tests/system/` | System testing (Streamlit AppTest) | `test_whole_app` |
| `tests/acceptance/` | Acceptance testing | One test per user story |

## Traceability

| Requirement | Tests |
|---|---|
| REQ-1 | `test_every_branch_of_find_programs`, `test_whole_app` |
| REQ-2 | `test_boundary_values`, `test_every_branch_of_find_programs`, `test_values_flow_through_find_programs` |
| REQ-3 | `test_yearly_cost`, `test_values_flow_through_find_programs` |
| REQ-4 | `test_chance`, `test_boundary_values`, `test_decision_tables` |
| REQ-5 | `test_find_scholarships`, `test_boundary_values`, `test_decision_tables` |
| REQ-6 | `test_upcoming`, `test_boundary_values`, `test_app_with_mocked_database_and_date`, story 3 |
| REQ-7 | `test_boundary_values`, `test_every_branch_of_find_programs` |
| REQ-8 | `test_database` |

Result: 15 tests pass, 100% line and branch coverage. GitHub Actions runs them on every push.

## Defect log

| ID | Date | Problem | Found by | Fixed |
|----|------|---------|----------|-------|
| 1 | Oct 30 | A data row with too few values crashed the loader instead of giving an error message. | A test | Oct 30 |
| 2 | Oct 30 | The app did not start because Python could not find our code folder. | Running the app | Oct 30 |
| 3 | Oct 30 | MS results showed a PhD-only "Funding" column. | A test | Oct 30 |
| 4 | Oct 31 | Searching scholarships accepted a GPA above 4. | Code review | Oct 31 |
