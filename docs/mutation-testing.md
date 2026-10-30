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

## Scholarship kinds: `scholarships.py`

Run again after `kind_of` and `fellowship_count` were added: **44 of 44 mutants killed** (35
before). The tests check each of the five types once, an unknown type (exact message), and a
count where eligible and not eligible fellowships, assistantships and scholarships are mixed.

## Bachelor's data: `fit.py` score rules, `data_loader._percentiles`, `ipeds_import.py`

Run after the BS degree, the SAT/ACT columns and the official-data importer were added.
`ipeds_import.py` was added to `source_paths`; `fit.py` and `data_loader.py` were already in it.
The new tests are in `tests/unit/test_ipeds_import_cli.py` (a new file, so Rajeshwari's
`test_ipeds_import.py` is unchanged) and at the end of `tests/unit/test_data_loader.py`.

| Module | Mutants | Killed (first run) | Survived (first run) | Killed (after) | Survived (after) |
|---|---:|---:|---:|---:|---:|
| `fit.py` (incl. SAT/ACT score rules) | 37 | 37 | 0 | 37 | 0 |
| `data_loader.py` (incl. `_percentiles`) | 479 | 474 | 5 | 476 | 3 (equivalent, as before) |
| `ipeds_import.py` | 644 | 550 | 94 | 633 of 652 | **19** (equivalent, see below) |

The importer's first run was on the code at `325d1b6`; the "after" run is on the code at
`fd69f15` (130 fields, admissions-page links, `kept_rows()` for a repeatable merge), which has
8 more mutants. The other modules: `apply_lookup.py` 406/428 (22 equivalent, see above; 4 new
mutants from the fix that counts only hand-entered rows, all killed),
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
| 37 | the description and help texts | `--help` shows the first docstring paragraph only, every help text exactly, and nothing added |

### Equivalent mutants in `ipeds_import.py` (19, not killed on purpose)
- **`encoding` (13).** `encoding=None`, no argument, `"UTF-8"` or `"UTF-8-SIG"` instead of the
  lower-case names, in `read_csv`, `kept_rows`, `merge_programs`, `write_csv` and `main`. Python
  runs in UTF-8 mode here and the names are the same codec.
- **`newline` when writing (2, `write_csv`).** With `newline=None` Python changes `\n` to the
  system line ending when writing; on Linux and macOS that is `\n`, so the file is identical. (On
  Windows it would not be, which is why `newline=""` stays.)
- **`newline` when `merge_programs` reads the header (2).** That `open()` only reads the column
  names; the rows are read by `kept_rows()`, whose `newline` mutants are killed by the
  line-break test. Column names never contain a line break.
- **`newline` when `main` reads `living_costs.csv` (2).** Only a line break inside a quoted cell
  would change, and only the two-letter state codes are used from that file.

## Checked imported rows in `apply_lookup.py`

After `apply_lookup` learned to add a row to `SOURCES.md` for a checked program from the official data
(`_add_imported_row`), the full run (2,040 mutants over all 11 modules) left **9 new survivors** in that
new code. Four showed real test gaps and were killed with three new tests at the end of
`tests/unit/test_apply_lookup.py`:

| Mutant | What changed | Test added |
|---|---|---|
| `_add_imported_row` 25, 26 | the `"|"` to `"/"` replacement in the notes was altered | `test_a_pipe_in_the_notes_of_an_imported_row_cannot_break_the_table` |
| `_add_imported_row` 32, 38 | `rstrip("\n")` became `lstrip("\n")` | `test_the_new_section_follows_one_blank_line_and_the_file_ends_with_one_newline`, `test_a_second_imported_row_is_added_on_the_next_line_without_a_blank_line` |

The other **5 are equivalent for real input** and are left on purpose:

| Mutant | Change | Why it cannot be noticed |
|---|---|---|
| `_set_status` 12 | `strip("|")` became `strip("XX|XX")` | differs only if a table line starts or ends with the letter X |
| `_add_imported_row` 31, 37 | `rstrip("\n")` became `rstrip(None)` | differs only if `SOURCES.md` ends with spaces or tabs |
| `_add_imported_row` 33, 39 | `rstrip("\n")` became `rstrip("XX\nXX")` | differs only if the file ends with the letter X |

Result for the whole `[tool.mutmut]` set at this point: cost, fit, funding, validation and search
had **no survivors**; the remaining survivors are the documented equivalents in `data_loader`,
`apply_lookup` and `ipeds_import`.

## Warning window, custom deadlines and starred items

`starred.py` was added to `source_paths` (the unit tests import it, so mutmut cannot start
without it). `deadlines.py` and `exports.py` were run again for the warning window, `glance_counts`,
`CustomDeadline` and the calendar events for custom deadlines.

| Module | Mutants | Killed (first run) | Survived (first run) | Killed (after new test) | Survived (after) |
|---|---:|---:|---:|---:|---:|
| `deadlines.py` | 95 | 93 | 2 | 95 | 0 |
| `exports.py` | 130 | 129 | 1 | 129 | **1** (equivalent) |
| `starred.py` | 22 | 22 | 0 | 22 | 0 |

- **The 2 survivors in `deadlines.py`** were `counts["passed"] += 1` and `counts["later"] += 1`
  becoming `= 1`. Every test had at most one passed and one later deadline. Added
  `test_glance_counts_adds_up_several_items_in_every_count` (two in each count).
- **The equivalent survivor in `exports.py`**: `_slug` ends with `.strip("-")`; the mutant is
  `.strip("XX-XX")`. `strip` removes a set of characters, and the slug is already lower case, so it
  never has an `X` at either end.

## Property-based tests and defect D-004 (2026-10-28)

Property-based tests (Hypothesis) were added for the loader, deadlines, scholarships and exports.
The calendar property found defect D-004 (a lone carriage return in a name was not escaped); the
fix added a few lines to `exports.py`. Mutation run after the fix: `exports.py` **111 of 111**
killed (6 new mutants, all killed). `data_loader.py` 476/479, `deadlines.py` 20/20 and
`scholarships.py` 35/35 are unchanged.

Each new property was also checked by breaking the code on purpose: the scholarship property fails
for a reversed GPA rule, an "any" instead of "all" special rule and a reversed "Any" check; the
deadline property fails for a misplaced cut-off; the calendar property fails when continuation
lines are folded at 76 bytes; the CSV property fails without quoting; the loader property fails
when a blank cell is read as 0. A property does not replace the example tests: for instance,
swapping `and` for `or` in the eligibility rule keeps "stricter never adds" true, and only the
decision-table tests catch it.

## Application requirements: `requirements.py`

`requirements.py` was added to `source_paths` (the unit tests import it, so mutmut cannot start
without it): **82 of 82 mutants killed** on the first run. The tests compare the whole loaded
object, check every error message exactly with its line number, and cover `yes`, `no`, blank and
wrongly written values of `required`.

After `essay_key`, `checklist` and `progress` were added for the Essays screen: **108 of 108
mutants killed**. The tests compare whole checklist lines, and the progress tests cover nothing
done, all done, an optional item that is done (never counted), and ticks for another program or
an unknown name.

## Cards: `presentation.py`

`presentation.py` was added to `source_paths`. The configuration also now copies
`data_report.py` and `api.py` into mutmut's work folder (the unit tests import the data report, and
without it the run could not start).

| Run | Mutants | Killed | Survived |
|---|---:|---:|---:|
| First run | 322 | 295 | 27 |
| After new tests | 322 | **319** | **3** (equivalent) |

The earlier card tests checked that words appeared somewhere in the HTML, so a changed label, a
missing colour or text glued between two pieces went unnoticed. The new tests at the end of
`tests/unit/test_presentation.py` compare exact pieces: the stats side by side, the chips with
their colours, the plain-text title when there is no safe link, half a SAT/ACT range (not shown),
the scholarship amount at 0 and 1, a quote in a scholarship link, the deadline row's link, any
minimum GPA above zero, and a citizenship code with no friendly wording.

Equivalent survivors (left on purpose):

| Mutant | Change | Why nothing can notice it |
|---|---|---|
| `safe_link` 3 | `url or ""` became `url or "XXXX"` | both give a value that is not an http(s) link, so the result is `None` either way |
| `result_card_html` 9, `_title_html` 6 (since removed with the old cards) | `escape(link, quote=True)` became `escape(link)` | `html.escape` escapes quotes by default, so the output is identical |

## New screens: `screens.py`, `components.py` and the smaller `presentation.py`

The redesign moved the cards out of `presentation.py` and into `components.py` (small pieces such as
a badge, a tile or a link) and `screens.py` (one row or card of each screen). The old card code was
removed, so `presentation.py` now holds only the shared text helpers. All three were run again
(unit tests only, as for the other modules).

| Module | First run | After new tests |
|---|---|---|
| `screens.py` | 371 mutants, 315 killed | 362 mutants, **362 killed** |
| `components.py` | 112 mutants, 106 killed | 112 mutants, **111 killed**, 1 equivalent |
| `presentation.py` | 83 mutants, 82 killed | 83 mutants, **82 killed**, 1 equivalent |

What the survivors showed, and the tests added for them (end of `tests/unit/test_screens.py` and
`tests/unit/test_components.py`):

- The fixed info cards (how cost is worked out, what the faces mean, the funding legend, the
  "At a glance" card) were only checked for a few words. They are now compared exactly.
- Deadline rows were not checked on the edges of the warning window. New boundary tests use
  -1, 0, 14 and 15 days, check that only passed rows are struck through, and check that a chosen
  window of 7 days changes the face as well as the tint.
- The due text and the scholarship amount had no test for 1 day, for an amount of $1, or for a
  chosen window being passed on.
- A stipend of $1 still counts as a stipend; the checklist lines, the TOEFL tag and the row cells
  are checked side by side, so text glued between them is noticed.
- Initials did not test a hyphenated name ("Winston-Salem State University" gives WSS), the
  progress bar did not test a total of 1, and the default sizes of the face and the star were not
  checked.
- `deadline_row_html` read the link with `getattr(item, "website", "")`. Every dated item has a
  website field, so the default could never be used; the code now reads `item.website`, and the
  three mutants on the unused default are gone (371 to 362 mutants).

Equivalent survivors (left on purpose):

| Mutant | Change | Why nothing can notice it |
|---|---|---|
| `components.official_link` 11 | `escape(link, quote=True)` became `escape(link)` | `html.escape` escapes quotes by default, so the output is identical |
| `presentation.safe_link` 3 | `url or ""` became `url or "XXXX"` | both give a value that is not an http(s) link, so the result is `None` either way |
