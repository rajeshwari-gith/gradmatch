# Mutation testing

Coverage tells us which lines the tests *run*. Mutation testing asks a harder question: do the
tests *notice* when the code is wrong? The tool (`mutmut`) makes many small changes to the code
(a "mutant": `>=` becomes `>`, `continue` becomes `break`, `2` becomes `3`) and runs the tests
on each one. A mutant that makes a test fail is **killed** (good). A mutant that no test notices
**survives**, which points to a weak or missing test.

## How to run it
```
pip install mutmut
mutmut run            # about 10 seconds for the modules below
mutmut results        # lists the survivors
mutmut show <name>    # shows the exact change a survivor made
```
Configuration is in `pyproject.toml` (`[tool.mutmut]`). Only the unit tests are used.

## Rajeshwari's modules: `cost.py`, `fit.py`, `funding.py`, `validation.py`, `search.py`

| Run | Mutants | Killed | Survived |
|---|---:|---:|---:|
| First run | 208 | 205 | **3** |
| After adding 3 tests | 208 | **208** | 0 |

### The three survivors and what they showed

| Mutant | What changed | Why it survived | Test added |
|---|---|---|---|
| `fit.py` | the GPA difference was rounded to 3 decimals instead of 2 | no test used a GPA with more than 2 decimals, so the "rounded to 2 decimals" rule was never checked | `test_gpa_difference_is_rounded_to_two_decimals` (differences of 0.1951, 0.1949, -0.1509 and -0.1551 around the 0.20 and -0.15 limits) |
| `search.py` | `continue` became `break` when a program is in another field or degree | every earlier test listed the matching programs first, so stopping at the first miss went unnoticed | `test_a_program_in_another_field_before_a_matching_one_does_not_stop_the_search` |
| `search.py` | `continue` became `break` when a program is over budget | same reason: the affordable program always came first | `test_a_too_expensive_program_before_an_affordable_one_does_not_stop_the_search` |

None of these were bugs in the program. They were gaps in the tests, and the new tests close them.

### Limits of this result
- Only the five modules above were mutated, with the unit tests only (the system and acceptance
  tests are too slow to run once per mutant).
- 208 of 208 killed does not prove the tests are perfect. It means no simple one-line mistake of
  the kinds the tool tries goes unnoticed in these modules.
- No equivalent mutants (changes that do not alter behavior) turned up in this run.

## Sai's modules: `data_loader.py`, `scholarships.py`, `deadlines.py`, `exports.py`

Same tool and settings (`mutmut` 3.8, unit tests only). The four modules were added to
`source_paths` in `pyproject.toml`; `apply_lookup.py` and `api.py` will be added once their
branches are merged into `main`.

| Module | Mutants | Killed (first run) | Survived (first run) | Killed (after new tests) | Survived (after) |
|---|---:|---:|---:|---:|---:|
| `data_loader.py` | 375 | 352 | 23 | 372 | **3** (equivalent, see below) |
| `scholarships.py` | 35 | 35 | 0 | 35 | 0 |
| `deadlines.py` | 17 | 17 | 0 | 17 | 0 |
| `exports.py` | 92 | 84 | 8 | 92 | 0 |
| **Total** | 519 | 488 | 31 | 516 | 3 |

### What the survivors showed and the tests added

| Survivors | What changed | Why it survived | Test added |
|---|---|---|---|
| 12 in `data_loader.py` | a loaded field (`university`, `state`, `stipend`, `website`, scholarship `states`, …) replaced by `None` | the tests checked a few fields of each loaded object, not all of them | `test_programs_every_field_is_loaded`, `test_scholarships_every_field_is_loaded` (compare the whole object) |
| 3 in `data_loader.py` | the "degree_levels is required" message changed or removed | the old test matched only the word "degree", which also appears in pytest's temporary folder name | `test_scholarships_empty_degree_levels_message` (exact message) |
| 1 in `data_loader.py` | the `", "` between missing column names changed | only one column was ever missing in a test | `test_missing_columns_are_listed_with_comma_and_space` |
| 2 in `data_loader.py` | `cost < 0` became `cost <= 0` / `cost < 1` | no test used a living cost of exactly 0 | `test_living_cost_of_zero_is_accepted` (boundary value) |
| 2 in `data_loader.py` | `open(..., newline="")` changed or removed | no test had a line break inside a quoted cell | `test_line_break_inside_a_quoted_cell_is_kept_exactly` |
| 4 in `exports.py` | the `CALSCALE` and `END:VEVENT` lines changed | the tests looked for lines by content, so a broken closing line went unnoticed | `test_ics_calendar_header_and_every_event_is_closed` |
| 2 in `exports.py` | escaping of a Windows line break (`\r\n`) changed | only `\n` was tested | `test_ics_windows_line_break_in_a_name_is_escaped_once` |
| 1 in `exports.py` | `astimezone(timezone.utc)` became `astimezone(None)` (local time) | the test machine's time zone is UTC, so both gave the same answer | `test_ics_stamp_is_utc_whatever_the_server_time_zone` (sets `TZ`) |
| 1 in `exports.py` | continuation lines folded at 73 instead of 74 bytes | the tests only checked lines were *at most* 75 bytes | `test_ics_folded_lines_are_filled_to_75_bytes` |

None of these were bugs in the program; they were gaps in the tests.

### Equivalent mutants (3, not killed on purpose)
All three change the `encoding` argument when `data_loader._load` opens a CSV: `encoding=None`,
no `encoding` argument, and `"UTF-8"` instead of `"utf-8"`. On this machine Python's default
encoding is already UTF-8, and `"UTF-8"` and `"utf-8"` are the same codec, so the files are read
identically and no test can tell the difference here. The explicit `encoding="utf-8"` stays,
because it matters on computers whose default encoding is not UTF-8 (for example some Windows
setups). Killing these would need a test that fakes another system encoding, which would test
Python rather than our code.

### Limits of this result
- Unit tests only; the integration, system and acceptance tests were not run per mutant.
- 516 of 519 killed means no simple one-line change of the kinds `mutmut` tries goes unnoticed in
  these modules, apart from the three equivalent ones. It does not prove the tests are complete.
