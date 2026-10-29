# How GradMatch works

A step-by-step walk through one search, in plain words. Each step names the file that does it.

```
 Official data --> ipeds_import.py --> data/*.csv --> data_loader.py
                                                          |
 Student form --> validation.py ---------------------------+
 (app/streamlit_app.py)                                     v
                                         search.py  (keep matches, drop over budget)
                                           |-- cost.py        tuition + living - stipend
                                           |-- fit.py         Safety / Match / Reach
                                           |-- funding.py     fully / partly / self-funded
                                           v
                    scholarships.py (who is eligible)    deadlines.py (days left)
                                           v
              presentation.py (cards)   exports.py (CSV, calendar)   api.py (REST)
```

## Our example student

Maya lives in Michigan, is a US citizen, has a 3.5 GPA, wants a Master's in Computer Science and
can pay $40,000 a year. (Illustrative numbers.)

| Step | File | What happens |
|---|---|---|
| 1. Data is ready | `ipeds_import.py`, `data_loader.py` | The official government files become program rows; the loader reads them and stops with the file and line number on a bad row. An empty cell means "not published". |
| 2. The form | `app/streamlit_app.py` | Maya enters her details and presses **Find programs**. |
| 3. Check the input | `validation.py` | GPA 0 to 4, SAT 400 to 1600, budget not negative, TOEFL required for international students. All problems are shown at once. |
| 4. Find matches | `search.py` | Keep her degree and field (and preferred states), drop anything over budget, then sort. |
| 5. Real cost | `cost.py` | Tuition + living costs - stipend, never below 0. A Michigan school: $15,000 + $12,000 - $0 = **$27,000 a year**, $54,000 for 2 years. An international student pays the out-of-state rate ($30,000), so $42,000, which is over budget. A funded PhD pays no tuition. |
| 6. Chance of admission | `fit.py` | Under 10% accepted: Reach. Colleges: SAT or ACT against the 25th/75th percentile. Otherwise GPA: +0.20 or more is Safety, -0.15 to +0.20 is Match, lower is Reach. No GPA published: estimated from the acceptance rate (60%+ Safety, 25–60% Match, under 25% Reach), one step easier for GPA 3.7+ and harder under 3.0; no data at all: left out. Maya 3.5 vs 3.3 is +0.20, so **Safety**. |
| 7. Funding | `funding.py` | Stipend covers living costs: Fully Funded. Some: Partially. None: Self-Funded. Blank: Funding unknown. |
| 8. Scholarships | `scholarships.py` | Shown only if every condition matches: degree, field, GPA, citizenship, state, special group. |
| 9. Deadlines | `deadlines.py` | Closed (past), Urgent (0 to 14 days), Soon (15 to 30), Later (31+). A Jan 15 deadline on Oct 27 is 80 days away: Later. |
| 10. Show it | `components.py`, `screens.py`, `presentation.py`, `app/theme.py`, `app/streamlit_app.py` | Four screens (program search, PhD funding, scholarships, deadlines): a results table with a face for each chance, PhD cards with a funding bar, scholarship cards, a deadline timeline with a warning window, stars, your own deadlines and two charts. |
| 11. Extras | `exports.py`, `api.py` | CSV and calendar downloads; the same answers through a REST API. |

## Design choices worth knowing

- **Logic is separate from the page.** Everything in `src/gradmatch` is plain Python, so it can be
  unit tested without a browser. The app only collects input and shows results.
- **"Today" is passed in.** Deadline code never reads the clock; the app reads `GRADMATCH_TODAY`
  for demos and tests. Tests give the same answer every day.
- **We never invent a number.** A value the government does not publish is `None` in the code and
  "n/a" on the screen. Our own estimates are labelled "(est.)".
- **Text from data is escaped** before it goes into a card, and only `http(s)` links are clickable.
- **One source of truth for the money rules** is [`CONTRIBUTING.md`](../CONTRIBUTING.md).

For what is tested and how, see [`test-plan.md`](test-plan.md); for the official data import, see
[`official-data-import.md`](official-data-import.md).
