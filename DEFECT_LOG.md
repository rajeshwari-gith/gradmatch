# Defect log

| ID | Found | Where | What went wrong | Severity | Found by | Fixed |
|----|-------|-------|-----------------|----------|----------|-------|
| D-001 | Oct 30 | `data_loader.py` | A row with too few values crashed with `AttributeError` instead of giving our "line N" error. A row with too many values was not caught at all. | Medium | `test_bad_rows_stop_loading_with_a_clear_message` | Oct 30 |
