# Test plan

## Requirements

1. Only programs in the chosen field are shown.
2. Only programs with a yearly cost at or under the budget are shown.
3. Yearly cost is tuition + living cost, using in-state tuition if the student is from that state.
4. Results are sorted cheapest first.
5. Chance: GPA at least 0.20 above the average is Safety, down to 0.15 below is Match, lower is Reach.
6. A GPA outside 0-4 or a negative budget gives an error.
7. A bad row in the data file gives an error with the line number.

## Tests

| File | What it tests |
|---|---|
| `test_cost.py` | cost.py |
| `test_fit.py` | fit.py, including the 0.20 and -0.15 edges and invalid GPAs |
| `test_data_loader.py` | data_loader.py with good and bad CSV files |
| `test_search.py` | search.py, every branch, plus searches on the real data |
| `test_app.py` | the whole page with Streamlit's AppTest |

Run with `pytest --cov`. GitHub Actions runs the tests on every push.

Current result: 61 tests passing, 100% line and branch coverage.
