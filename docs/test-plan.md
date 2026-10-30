# Test plan

## What we test

The 4 features in the README. The requirements below are what the functional tests check.

| ID | Requirement |
|----|-------------|
| R1 | Only programs in the chosen field are shown. |
| R2 | Only programs whose yearly cost is at or under the budget are shown. |
| R3 | Yearly cost = tuition + living cost. In-state tuition if the home state is the program's state. |
| R4 | Results are sorted cheapest first. |
| R5 | Chance: GPA difference ≥ 0.20 is Safety, -0.15 to 0.19 is Match, below -0.15 is Reach. |
| R6 | A GPA outside 0–4 or a negative budget is rejected. |
| R7 | A bad row in the data file gives an error with its line number. |

## Tests by course topic

| Week | Topic | File | What it shows |
|---|---|---|---|
| 2 | Unit testing | `tests/test_unit.py` | Each function on its own |
| 3 | Test case design | `tests/test_test_design.py` | Equivalence partitions and boundary values for GPA, chance and budget |
| 4 | TDD and test doubles | `tests/test_test_doubles.py` | Stub, fake, spy and mock (TDD: see below) |
| 5 | Control-flow testing | `tests/test_control_flow.py` | One test per path of `chance()` and every branch of `find_programs()` |
| 6 | Data-flow testing | `tests/test_data_flow.py` | All def-use pairs of `diff`, `cost`, `student` and `results` |
| 7 | Coverage | `pyproject.toml` | 100% line and branch coverage; `pytest --cov` fails below 100% |
| 8 | Functional testing | `tests/test_functional.py` | One test (or more) per requirement R1–R7 |
| 9 | Integration testing | `tests/test_integration.py` | Loader + search + cost + chance on the real file and temp files |
| 10 | System testing | `tests/test_system.py` | The whole app run with Streamlit's AppTest |
| 11 | Acceptance testing | `tests/test_acceptance.py` | 3 user stories written as Given / When / Then |
| 13 | Continuous testing | `.github/workflows/tests.yml` | GitHub Actions runs all tests and coverage on every push |
| 14 | Advanced testing | `tests/test_advanced.py` | Property-based tests with Hypothesis |

The graphs and the def-use table for weeks 5 and 6 are in [control-and-data-flow.md](control-and-data-flow.md).

## TDD (week 4)

Each of us adds one small change to our own feature test first: write the test, run it and see it
fail (red), write just enough code to pass (green), then clean up. The test and the code go in
separate commits so the order shows in the history.

## Results

91 tests, all passing. Coverage: 100% of lines and branches.
Defects we found are in [DEFECT_LOG.md](../DEFECT_LOG.md).
