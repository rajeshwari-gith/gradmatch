# Defect log

| ID | Found | Where | What went wrong | Severity | Found by | Fixed |
|----|-------|-------|-----------------|----------|----------|-------|
| D-001 | Oct 23 | `cost.py` | Funded PhD programs still showed a yearly cost above $0, because we subtracted the stipend instead of waiving tuition. Students with a small budget didn't see them. | Medium | `test_funded_phd_pays_no_tuition` | Oct 23 |
| D-002 | Oct 23 | app | The cost vs GPA chart crashed the results page on every search (the tooltip fields had no type). We caught it before merging. | High | `test_profile_form.py` (8 tests failed) | Oct 23 |
| D-003 | Oct 26 | `search.py` | International students got in-state tuition if they picked the program's state as home state. Sai spotted it in review. | Medium | `test_international_student_pays_out_of_state_tuition_even_with_a_matching_home_state` | Oct 26 |
| D-004 | Oct 28 | `exports.py` | A lone `\r` in a name broke a line in the calendar file. Hypothesis found it. | Low | `test_every_calendar_line_is_at_most_75_bytes_and_ends_with_crlf` | Oct 28 |
