# GradMatch

SE 413/513 Software Testing project, Fall 2026
Rajeshwari Galugu and Sai Nishith Jangili

A small Streamlit app that shows master's programs a student can afford. You enter your
field, GPA, home state and yearly budget, and it lists the programs in your budget,
cheapest first, with a Safety / Match / Reach chance.

Live app: https://gradmatch-rg.streamlit.app

## Features

| Feature | File | Who |
|---|---|---|
| Yearly cost (tuition + living cost, in-state or out-of-state) | `src/gradmatch/cost.py` | Rajeshwari |
| Chance of getting in, from GPA vs. average GPA | `src/gradmatch/fit.py` | Rajeshwari |
| Loading and checking the data file | `src/gradmatch/data_loader.py` | Nishith |
| Search by field and budget | `src/gradmatch/search.py` | Nishith |

The page itself is `app/streamlit_app.py`.

## Running (Python 3.11 or newer)

```
pip install -r requirements.txt
streamlit run app/streamlit_app.py
pytest --cov
```

## Data

`data/programs.csv` has 15 programs. Tuition and average GPA are estimates for now; we
still have to check them on each school's website. Living cost is from the MERIC cost of
living index (https://meric.mo.gov/data/cost-living-data-series).
