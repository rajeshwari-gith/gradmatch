# GradMatch

SE 413/513 – Software Testing, Track B
Rajeshwari Galugu and Sai Nishith Jangili

GradMatch helps students plan for graduate school. Students enter their degree, field, GPA,
home state and budget, and the app shows programs they can afford, their chance of getting in,
scholarships, and deadlines. The data is stored in a SQLite database.

Live app: https://gradmatch-app.streamlit.app

## Install

`python -m pip install -r requirements.txt`

## Run the app

`python -m streamlit run app.py`

## Run the tests

`python -m pytest -v`

With coverage:

`python -m pytest --cov=app --cov=programs --cov=scholarships --cov=database --cov-branch`

The test plan and defect log are in `TEST_PLAN.md`.
