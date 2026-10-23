# GradMatch – Project Rules (read before any work)

SE 413/513 Software Testing, Fall 2026, Track B. Team: Rajeshwari Galugu + Sai Nishith Jangili.
GradMatch helps students find grad programs (MS/PhD) by GPA, budget and state, plus scholarships,
opportunities and deadlines. Stack: Python 3.11+, Streamlit, FastAPI, SQLite, pytest.

## Grading rules that affect how we work
- Commit small and often, with descriptive messages (one logical change per commit). Big late commits are penalized.
- Each member commits ONLY their own components (see Ownership) from their own GitHub account.
- Work on a branch `<name>/<feature>` (e.g. `sai/scholarships`), open a pull request, the other member reviews it.
- Every line must be explainable by its owner. Keep code simple; no clever tricks.
- Log AI use in `AI_LOG.md` (date, member, tool, what it helped with) for the report's AI disclosure.

## Repository layout
```
src/gradmatch/
  models.py            shared dataclasses (below) – change only with both members agreeing
  validation.py        [R] profile input validation
  search.py            [R] filter programs by field/degree/state/budget
  cost.py              [R] tuition (in/out-of-state) + living cost - stipend
  fit.py               [R] Reach / Match / Safety
  funding.py           [R] PhD funding label
  db.py                [S] SQLite setup + queries
  data_loader.py       [S] load + validate CSVs into models
  scholarships.py      [S] eligibility matching
  deadlines.py         [S] urgency status, checklist
  exports.py           [S] CSV + .ics export
  scorecard_client.py  [S] optional College Scorecard API client (always mocked in tests)
  api.py               [S] FastAPI endpoints
app/streamlit_app.py   [R] UI (thin – calls src/gradmatch only)
data/                  [S] programs.csv, scholarships.csv, living_costs.csv
tests/unit/ tests/integration/ tests/system/ tests/acceptance/
.github/workflows/ci.yml [R]
```
[R] = Rajeshwari, [S] = Sai Nishith.

## Shared models (`src/gradmatch/models.py`)
```python
from dataclasses import dataclass, field
from datetime import date

@dataclass(frozen=True)
class StudentProfile:
    degree_sought: str            # "MS" or "PhD"
    gpa: float                    # 0.0 - 4.0
    field: str                    # e.g. "Computer Science"
    home_state: str               # 2-letter code, e.g. "MI"
    citizenship: str              # "US", "PR" (permanent resident), "International"
    annual_budget: float          # USD per year, >= 0
    preferred_states: tuple[str, ...] = ()   # empty = any state
    gre: int | None = None        # 260 - 340
    toefl: int | None = None      # 0 - 120
    special: tuple[str, ...] = () # e.g. ("first_gen", "women_stem")

@dataclass(frozen=True)
class Program:
    program_id: str
    university: str
    program_name: str
    field: str
    degree: str                   # "MS" or "PhD"
    state: str
    tuition_in_state: float       # USD per year
    tuition_out_state: float
    duration_years: float
    avg_gpa: float
    avg_gre: int | None
    acceptance_rate: float        # 0.0 - 1.0
    stipend: float                # USD per year, 0 if none
    min_toefl: int | None
    application_deadline: date
    website: str

@dataclass(frozen=True)
class Scholarship:
    scholarship_id: str
    name: str
    type: str                     # scholarship | fellowship | assistantship | research | fee_waiver
    amount: float                 # USD (0 if non-monetary)
    degree_levels: tuple[str, ...]  # ("MS",), ("PhD",) or ("MS","PhD")
    fields: tuple[str, ...]       # ("Any",) or list of fields
    min_gpa: float
    citizenship: tuple[str, ...]  # ("Any",) or subset of US/PR/International
    states: tuple[str, ...]       # ("Any",) or list of state codes
    special: tuple[str, ...]      # () = no special requirement; else ALL listed required
    deadline: date
    website: str
```

## CSV formats (`data/`)
- `programs.csv`: columns = Program fields in order. Dates `YYYY-MM-DD`. Empty cell = None.
- `scholarships.csv`: columns = Scholarship fields; list fields use `;` (e.g. `MS;PhD`).
- `living_costs.csv`: `state,annual_living_cost`.
Every row needs a real `website` (official source). Data is an estimate; UI shows "verify on the official site".

## Business rules (tests are written against these – do not change silently)
- **Deadline status** (today is ALWAYS passed in as a parameter, never `date.today()` inside logic):
  days_left = (deadline - today).days; `< 0` → "closed"; `0–14` → "urgent"; `15–30` → "soon"; `> 30` → "later".
- **Scholarship eligibility**: ALL must hold: degree in degree_levels; field in fields or "Any";
  gpa >= min_gpa; citizenship in list or "Any"; home_state in states or "Any"; every `special` item in profile.special.
- **Tuition**: in-state rate if profile.home_state == program.state, else out-of-state.
- **Yearly cost** = tuition + living cost of program state − stipend (never below 0).
- **Fit** (diff = gpa − avg_gpa, rounded to 2 decimals): `diff >= 0.20` Safety; `-0.15 <= diff < 0.20` Match;
  `diff < -0.15` Reach. Exception: acceptance_rate < 0.10 is always Reach.
- **PhD funding**: stipend >= living cost → "Fully Funded"; 0 < stipend < living cost → "Partially Funded"; 0 → "Self-Funded".

## Testing rules
- `pytest` from repo root; coverage: `pytest --cov=src/gradmatch --cov-branch --cov-report=term-missing`.
- Tests never use the network (mock `scorecard_client`) and never depend on the real CSVs –
  use small fixture data in `tests/conftest.py` and a temp SQLite DB per test.
- Name tests after the technique where useful: `test_deadline_status_boundary_14_days_is_urgent`.
- Mark tests: `@pytest.mark.unit`, `integration`, `system`, `acceptance`.
- Any bug found by a test → add a row to `DEFECT_LOG.md` (id, date, module, description, severity, status).
