# GradMatch – Project Rules (read before any work)

SE 413/513 Software Testing, Fall 2026, Track B. Team: Rajeshwari Galugu + Sai Nishith Jangili.
GradMatch helps students find grad programs (MS/PhD) by GPA, budget and state, plus scholarships,
opportunities and deadlines. Stack: Python 3.11+, Streamlit, FastAPI, SQLite, pytest.

## Grading rules that affect how we work
- Commit small and often, with descriptive messages (one logical change per commit). Big late commits are penalized.
- Each member commits ONLY their own components (see Ownership) from their own GitHub account.
- Work on a branch `<name>/<feature>` (e.g. `sai/scholarships`), open a pull request, the other member reviews it.
- Every line must be explainable by its owner. Keep code simple; no clever tricks.
- Commit messages say what changed in a short imperative line (for example "Add property-based tests for search").
- Before the first commit on a new machine, check `git config user.name` and `git config user.email` are your own.

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
- `requirements.csv`: `program_id,name,required,limit_text,prompt_text,source_url,checked_by,checked_on`; `required` is `yes`/`no`; only rows checked on the official page (blank limit or prompt = not stated).
Every row needs a real `website` (official source). Data is an estimate; UI shows "verify on the official site".

## Business rules (tests are written against these – do not change silently)
- **Deadline status** (today is ALWAYS passed in as a parameter, never `date.today()` inside logic):
  days_left = (deadline - today).days; `< 0` → "closed"; `0–14` → "urgent"; `15–30` → "soon"; `> 30` → "later".
  The warning window (14 by default) is `urgent_days`, a whole number from 0 to 90: `0–urgent_days` → "urgent",
  then "soon" up to 30, then "later". `glance_counts` counts `within_window` (0–urgent_days), `within_90` (0–90,
  includes the window), `later` (> 90) and `passed` (< 0); unpublished deadlines are not counted.
- **Scholarship eligibility**: ALL must hold: degree in degree_levels; field in fields or "Any";
  gpa >= min_gpa; citizenship in list or "Any"; home_state in states or "Any"; every `special` item in profile.special.
- **Scholarship kind** (`kind_of`): the five `type` values are shown as three kinds. `scholarship` → Scholarship;
  `fee_waiver` → Scholarship (money off the cost, no work in return); `fellowship` → Fellowship; `assistantship` →
  Assistantship; `research` → Assistantship (paid research work). Any other type is an error.
  `fellowship_count` counts the eligible scholarships whose kind is Fellowship or Assistantship.
- **Tuition**: in-state rate if profile.home_state == program.state, else out-of-state. **International students (citizenship "International") are never residents of a state and always pay the out-of-state rate.**
- **Tuition charged**: a PhD program with `stipend > 0` waives tuition (charged 0); MS programs always charge tuition.
- **Yearly cost** = tuition charged + living cost of program state − stipend (never below 0).
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

## Values that are not published (rows imported from official government data)
Rows built from the US Department of Education data (IPEDS) have the state, the graduate tuition
and the institution website, but **not** the admitted GPA, acceptance rate, stipend or deadline.
Those cells are left **blank** in `programs.csv`, and a blank means **"not published"** (it is
never a guess). The rules:
- **Loader:** blank `avg_gpa`, `acceptance_rate`, `stipend`, `application_deadline`, `avg_gre` and
  `min_toefl` are allowed and become `None`. A non-blank value is still checked against its range
  and format. The tuition columns, state, degree, field and website stay required.
- **New optional column `source`:** `estimate` (hand-drafted values, the default when blank),
  `official-page` (checked by a person on the program's official page) or `ipeds` (imported).
- **Fit:** `avg_gpa` is `None` -> estimated from the acceptance rate (the program's own, else its university's
  overall rate from the `BS` rows of the same university and state): `rate >= 0.60` Safety; `0.25 <= rate < 0.60`
  Match; `rate < 0.25` Reach; then `gpa >= 3.7` one step easier and `gpa < 3.0` one step harder, never past
  Safety or Reach. A rate below 10% is always `Reach`. No GPA and no rate at all -> `Unknown`, and the
  search leaves that program out.
- **Funding:** `stipend` is `None` -> `Funding unknown`. For the cost, an unknown stipend counts as 0
  (the cautious choice), so an unknown PhD stipend means tuition is not waived.
- **Deadlines:** a `None` deadline is left out of the Deadlines tab, the calendar file and
  `upcoming()`; the program card says to check the program page.
- **Exports and the API:** a `None` value is written as an empty cell (CSV) or `null` (JSON).
- **Cards:** an unknown value is shown as "not published", never as 0.


## Bachelor's programs (undergraduate search)

- `degree` can be `BS`, `MS` or `PhD`. `BS` rows are colleges for undergraduate applicants.
- A `BS` row uses undergraduate tuition (in-state and out-of-state), `duration_years` 4 and `stipend` 0.
- The same cost rule applies: tuition charged + living cost - stipend, in-state only for US/PR students of that state.
- GRE does not apply to a bachelor's search. The fit uses the same rules as above, so a `BS` row without a published average GPA gets a chance estimated from its acceptance rate.
- Undergraduate scholarships go in `scholarships.csv` with `BS` in `degree_levels`. Add one only after checking it on the provider's official page.
