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
