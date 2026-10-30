# GradMatch

SE 413/513 Software Testing, Fall 2026 – Rajeshwari Galugu and Sai Nishith Jangili

GradMatch is a small web app that helps a student find master's programs they can afford.
You pick a field, enter your GPA, home state and yearly budget, and it shows the programs
that fit, cheapest first, with a rough chance of getting in.

Live app: https://gradmatch-rg.streamlit.app

## The 4 features

| # | Feature | Code | Owner |
|---|---------|------|-------|
| 1 | **Yearly cost** – tuition + living cost. In-state tuition if your home state is the program's state, otherwise out-of-state. | `src/gradmatch/cost.py` | Rajeshwari |
| 2 | **Chance of getting in** – your GPA minus the program's average GPA: 0.20 or more is Safety, -0.15 to 0.19 is Match, below -0.15 is Reach. | `src/gradmatch/fit.py` | Rajeshwari |
| 3 | **Load and check the data** – reads `data/programs.csv` and stops with the line number if a row is bad. | `src/gradmatch/data_loader.py` | Nishith |
| 4 | **Search** – keeps programs in your field that fit your budget, cheapest first. | `src/gradmatch/search.py` | Nishith |

The web page is `app/streamlit_app.py` (both of us). `src/gradmatch/models.py` has the two data
classes, `Program` and `Student`.

## Run it

```
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Run the tests

```
pytest            # all tests
pytest --cov      # with line and branch coverage
```

The tests are in `tests/`, one file per course topic. See [docs/test-plan.md](docs/test-plan.md).
GitHub Actions runs every test on each push.

## Data

`data/programs.csv` has 15 master's programs (11 Computer Science, 4 Data Science).
The numbers are our estimates and still need checking on each official page – see
[data/README.md](data/README.md).
