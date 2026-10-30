# Mutation testing

We used mutmut to check our tests. It makes small changes to the code (like `>` to `>=`, or
`continue` to `break`) and runs the unit tests. If a test fails, the change is "killed". If no
test notices, it "survived", which usually means a test is missing.

```
mutmut run
mutmut results
```

## Results (full run, Oct 30)

| Module | Mutants | Killed | Survived |
|---|---:|---:|---:|
| `cost.py` | 74 | 74 | 0 |
| `fit.py` | 76 | 76 | 0 |
| `funding.py` | 4 | 4 | 0 |
| `search.py` | 86 | 86 | 0 |
| `validation.py` | 84 | 84 | 0 |
| `scholarships.py` | 44 | 44 | 0 |
| `deadlines.py` | 95 | 95 | 0 |
| `starred.py` | 22 | 22 | 0 |
| `requirements.py` | 108 | 108 | 0 |
| `screens.py` | 371 | 371 | 0 |
| `components.py` | 112 | 111 | 1 |
| `presentation.py` | 83 | 82 | 1 |
| `exports.py` | 130 | 129 | 1 |
| `data_loader.py` | 479 | 476 | 3 |
| `apply_lookup.py` | 477 | 451 | 26 |
| `ipeds_import.py` | 652 | 633 | 19 |
| **Total** | **2,897** | **2,846** | **51** |

## What it found

Every time we ran it, it found tests we were missing. Some examples:

- `continue` changed to `break` in the search wasn't caught, because in all our tests the matching
  program came first. We added tests where a non-matching program comes first.
- The GPA difference is rounded to 2 decimals, but no test used a GPA with more decimals.
- Text on the screens was only checked for a few words, so changed labels went unnoticed. Now the
  tests compare the exact text.
- Deadline edges (0, 14 and 15 days left), a $1 stipend, and a weak GPA at an easy school were
  not tested.

## The 51 that are left

We looked at each one. They can't change what the program does, so no test can catch them:

- `encoding="utf-8"` changed to `"UTF-8"` or removed (20). Same thing on our machines.
- `escape(link, quote=True)` changed to `escape(link)` (1). `escape` quotes by default.
- An empty value changed to a different empty-looking value, a temp file name, or `strip`
  characters that never appear at the ends of our lines (about 11).
- `ipeds_import.py` (19): file reading options and column name variants that give the same rows
  for the real IPEDS files.
