# GradMatch

GradMatch helps students plan for graduate school. Undergraduates enter their GPA,
test scores, budget and preferred U.S. states to find Master's programs that fit them;
graduate students find PhD programs ranked by funding. It also shows scholarships,
opportunities and application deadlines.

SE 413/513 Software Testing, Fall 2026 – Track B project by
Rajeshwari Galugu and Sai Nishith Jangili.

Built with Python, Streamlit, FastAPI and SQLite. Results are estimates –
always verify on the official program website.

## Install

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the tests

```
pytest                                   # all tests
pytest -m unit                           # only unit tests
pytest --cov --cov-report=term-missing   # with line + branch coverage
```

## Project layout

```
src/gradmatch/   application code (business logic)
app/             Streamlit user interface
data/            program, scholarship and living-cost data (CSV)
tests/           unit, integration, system and acceptance tests
```

See `CLAUDE.md` for the team's rules, data formats and business rules.
