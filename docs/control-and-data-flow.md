# Control-flow and data-flow (weeks 5 and 6)

## chance(gpa, avg_gpa) in fit.py

```
1  check_gpa(gpa)                 -- bad GPA --> raise ValueError
2  diff = round(gpa - avg_gpa, 2)
3  if diff >= 0.20:
4      return "Safety"
5  if diff >= -0.15:
6      return "Match"
7  return "Reach"
```

```
      (1) --bad--> raise
       |
      (2)
       |
      (3) --true--> (4) Safety
       | false
      (5) --true--> (6) Match
       | false
      (7) Reach
```

Paths (tests in `test_control_flow.py`):

| Path | Nodes | Test input |
|---|---|---|
| 1 | 1 → raise | gpa 5.0 |
| 2 | 1 → 2 → 3 → 4 | gpa 3.8, avg 3.5 |
| 3 | 1 → 2 → 3 → 5 → 6 | gpa 3.5, avg 3.5 |
| 4 | 1 → 2 → 3 → 5 → 7 | gpa 3.0, avg 3.5 |

## find_programs(programs, student) in search.py

```
1  check_gpa(student.gpa)                          -- bad GPA --> raise
2  if student.budget < 0: raise
3  results = []
4  for program in programs:                       -- no more programs --> 9
5      if program.field != student.field: continue    (back to 4)
6      cost = yearly_cost(program, student.home_state)
7      if cost > student.budget: continue             (back to 4)
8      results.append(Result(program, cost, chance(student.gpa, program.avg_gpa)))
9  results.sort(...); return results
```

```
 (1) --bad--> raise
  |
 (2) --true--> raise
  | false
 (3)
  |
 (4) <-----------+----------+----------+
  | \ done       |          |          |
  |  `--> (9)    |          |          |
 (5) --true------+          |          |
  | false                   |          |
 (6)                        |          |
  |                         |          |
 (7) --true-----------------+          |
  | false                              |
 (8) ----------------------------------+
```

Branches covered: 1 (bad/ok), 2 (true/false), 4 (zero times/more), 5 (true/false), 7 (true/false).
A test with 3 programs runs the loop 3 times and takes each of 5, 7 and 8 once.

## Def-use table

| Variable | Def (node) | Use (node) | Kind of use | Test in `test_data_flow.py` |
|---|---|---|---|---|
| diff (chance) | 2 | 3 | decision | `test_diff_def_2_use_3` |
| diff (chance) | 2 | 5 (true) | decision | `test_diff_def_2_use_5_true` |
| diff (chance) | 2 | 5 (false) | decision | `test_diff_def_2_use_5_false` |
| cost | 6 | 7 | decision | `test_cost_def_6_use_7_over_budget` |
| cost | 6 | 8 | computation | `test_cost_def_6_use_8_stored_in_result` |
| student.home_state | start | 6 | computation | `test_student_home_state_used_at_node_6` |
| student.gpa | start | 8 | computation | `test_student_gpa_used_at_node_8` |
| results | 3 | 9 | computation | `test_results_def_3_use_9_empty` |
| results | 8 | 9 | computation | `test_results_def_8_use_9_sorted` |

`student.gpa` at node 1, `student.budget` at nodes 2 and 7 and `student.field` at node 5 are
covered by the control-flow tests.
