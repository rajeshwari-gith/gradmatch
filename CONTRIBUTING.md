# How we work

Rajeshwari Galugu and Sai Nishith Jangili, SE 413/513 Fall 2026.

- Make a branch like `rajeshwari/<thing>` or `sai/<thing>`, open a pull request, and merge it once
  CI is green.
- Small commits with short messages that say what changed.
- Check `git config user.name` and `user.email` are your own before committing.
- Every bug a test finds goes in `DEFECT_LOG.md`.
- Tests never use the internet or the real data files (except `test_real_data.py`).
- Mark tests with `unit`, `integration`, `system` or `acceptance`.

## Who owns what

- Rajeshwari: `cost.py`, `fit.py`, `funding.py`, `search.py`, `validation.py`, `ipeds_import.py`,
  `link_check.py`, the app (`app/`, `screens.py`, `components.py`, `presentation.py`) and CI
- Sai: `data_loader.py`, `scholarships.py`, `deadlines.py`, `exports.py`, `starred.py`,
  `requirements.py`, `api.py`, `apply_lookup.py`, `data_report.py` and the data files
- `models.py` is shared, so we change it only when we both agree

## Data files

- `programs.csv`, `scholarships.csv`, `living_costs.csv`, `requirements.csv` in `data/`
- Dates are `YYYY-MM-DD`. Lists use `;` (like `MS;PhD`). An empty cell means "not published".
- `source` is `estimate` (typed by us), `official-page` (checked by a person) or `ipeds` (imported).
- Every row needs its official website. Only mark a row as checked if someone really checked it.

## The rules our tests check

**Tuition:** in-state if your home state is the program's state, otherwise out-of-state.
International students always pay out-of-state.

**Cost per year:** tuition + living cost of the state - stipend, never below 0. A PhD with a
stipend waives tuition. An unknown stipend counts as 0.

**Chance (Safety / Match / Reach):**
- under 10% accepted: always Reach
- BS with SAT/ACT given: at or above the 75th percentile is Safety, between 25th and 75th is Match, below is Reach
- program publishes an average GPA: your GPA minus theirs is +0.20 or more Safety, -0.15 to +0.20 Match, lower Reach
- no average GPA: use the acceptance rate (the program's own, else the university's): 60%+ Safety,
  25-60% Match, under 25% Reach. Then a GPA of 3.7+ moves one step easier and under 3.0 one step harder.
- no GPA and no rate at all: the program is left out of the results

**Funding:** stipend at least the living cost = Fully Funded, smaller stipend = Partially Funded,
none = Self-Funded, unknown = Funding unknown.

**Scholarships:** you qualify only if everything matches: degree, field (or Any), GPA at least the
minimum, citizenship, state (or Any) and every special group it needs. The five types show as three
kinds: scholarship and fee_waiver = Scholarship, fellowship = Fellowship, assistantship and
research = Assistantship.

**Deadlines:** days left = deadline - today (today is always passed in). Under 0 = closed,
0 to 14 = urgent, 15 to 30 = soon, more = later. The warning window can be 0 to 90 days.
"At a glance" counts deadlines within the window, within 90 days, later, and passed.
