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

## Unpublished values (`None`) and `apply_lookup.py`

Run after the loader, deadlines, exports and `apply_lookup` were changed to handle values that
are not published (blank cells become `None`, the new `source` column). `apply_lookup.py` was
added to `source_paths`, and `app/` to `also_copy` (the unit tests for `app/freshness.py` need it).

| Module | Mutants | Killed | Survived | Notes |
|---|---:|---:|---:|---|
| `data_loader.py` | 417 | 414 | 3 | the same 3 equivalent `encoding` mutants as before; every mutant in the new `None` and `source` code is killed |
| `deadlines.py` | 20 | 20 | 0 | includes skipping `None` deadlines in `upcoming()` |
| `exports.py` | 105 | 105 | 0 | includes empty CSV cells for `None` and skipping undated programs in `.ics` |
| `apply_lookup.py` (first run) | 424 | 370 | 54 | first time this module was mutation tested |
| `apply_lookup.py` (after new tests) | 424 | **402** | 22 | all 22 are equivalent, see below |

`scholarships.py` (35 of 35) and Rajeshwari's modules (216 of 216) are unchanged.

### Tests added for `apply_lookup.py`
The 32 survivors that were real gaps came from messages and output that the tests only matched
in part, and from cases no test used: an exact multi-problem error message, the exact waiver,
SOURCES.md, column-list and usage messages; a stipend of 0.5 (boundary of "greater than 0"); an
unchecked row before a checked one (`continue` vs `break`); changes from two rows (`+=` vs `=`);
Unix line endings in the written CSV; a line break inside quoted cells and notes; a `|` in notes;
the command run with only the sheet (default `data` folder) and its printed lines.

### Equivalent mutants (25, not killed on purpose)
- **`encoding` (20: 3 in `data_loader`, 17 in `apply_lookup`).** `encoding=None`, no `encoding`
  argument, and `"UTF-8"` instead of `"utf-8"` when reading or writing a file. Python runs in UTF-8
  mode on this machine, and `"UTF-8"` and `"utf-8"` are the same codec, so no test can see a
  difference. The explicit `encoding="utf-8"` stays for computers whose default is not UTF-8.
- **Temporary file name (2).** `_check_with_loader` writes the new CSV to a temporary file, loads
  it and deletes it; any name in the same folder behaves the same.
- **`program["source"] = None` instead of `""` (1).** `csv.DictWriter` writes `None` as an empty
  cell, so the file is identical.
- **`line.strip("XX|XX")` instead of `line.strip("|")` (2).** `strip` removes a *set* of characters
  from the ends of the line. Table lines start and end with `|`, and the first and last cells are
  separated from it by spaces, so the extra `X` never touches a cell.

## Bachelor's data: `fit.py` score rules, `data_loader._percentiles`, `ipeds_import.py`

Run after the BS degree, the SAT/ACT columns and the official-data importer were added.
`ipeds_import.py` was added to `source_paths`; `fit.py` and `data_loader.py` were already in it.
The new tests are in `tests/unit/test_ipeds_import_cli.py` (a new file, so Rajeshwari's
`test_ipeds_import.py` is unchanged) and at the end of `tests/unit/test_data_loader.py`.

| Module | Mutants | Killed (first run) | Survived (first run) | Killed (after) | Survived (after) |
|---|---:|---:|---:|---:|---:|
| `fit.py` (incl. SAT/ACT score rules) | 37 | 37 | 0 | 37 | 0 |
| `data_loader.py` (incl. `_percentiles`) | 479 | 474 | 5 | 476 | 3 (equivalent, as before) |
| `ipeds_import.py` | 644 | 550 | 94 | 625 | **19** (equivalent, see below) |

The other modules are unchanged: `apply_lookup.py` 402/424 (22 equivalent, see above),
`exports.py` 105/105, `deadlines.py` 20/20, `scholarships.py` 35/35, and Rajeshwari's `cost.py`,
`funding.py`, `search.py` and `validation.py` 235/235.

### What the survivors showed and the tests added
| Survivors | What changed | Test added |
|---|---|---|
| 2 in `_percentiles` | the column names or values inside the error messages swapped | exact messages for a one-sided SAT range and a reversed ACT range |
| 1 | `continue` became `break` when a school has no tuition rate | a school without a rate before one with a rate |
| 2 | `admitted <= applicants` became `<`; rounding to 4 decimals | acceptance rate of exactly 100% (boundary); 1 of 3 admitted gives 0.333 |
| 6 | `act_25`/`act_75` defaults and the `sat_75`/`act_25` names in `_fill_admissions` | every test-score column checked for BS rows with and without admissions data |
| 2 | `merge_programs` lost the old column order or the column list | an old file with an extra column (`notes`) keeps it, in its order |
| 4 | `newline=""` removed when reading an official file or merging | a line break inside a quoted cell is kept |
| 3 | the common-to-official name lookup, `* 100` and the zero-rate check in `tuition_check` | a common name (Purdue University) matched to the official one, a 60% difference, a zero in-state rate with a known out-of-state rate |
| 9 | `required=True` removed or changed for `--hd`, `--cost`, `--completions` | leaving out each file stops with exit code 2 and names it |
| 8 | the `--data` and `--output` defaults | run without them from a folder with a `data/` subfolder |
| 3 | the "row(s) added to …" message | exact message after `--merge` |
| 54 | the description and help texts | `--help` shows the first docstring paragraph only, every help text exactly, and nothing added |

### Equivalent mutants in `ipeds_import.py` (19, not killed on purpose)
- **`encoding` (13).** `encoding=None`, no argument, `"UTF-8"` or `"UTF-8-SIG"` instead of the
  lower-case names. Python runs in UTF-8 mode here and the names are the same codec.
- **`newline` when writing (2, `write_csv`).** With `newline=None` Python changes `\n` to the
  system line ending when writing; on Linux and macOS that is `\n`, so the file is identical. (On
  Windows it would not be, which is why `newline=""` stays.)
- **`newline` when `main` reads `living_costs.csv` and `programs.csv` (4).** Only a line break
  inside a quoted cell would change. From `living_costs.csv` only the state codes are used, and the
  `programs.csv` values `main` uses (school name, degree, field, tuition) never contain one; the
  school name also goes through `normalize()`, which drops line breaks. So these are equivalent for
  every file the importer is used with, and a test would only test a made-up file.
