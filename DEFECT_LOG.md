# Defects

| ID | Date | File | Problem | Found by | Fixed |
|----|------|------|---------|----------|-------|
| 1 | Oct 30 | data_loader.py | A row with too few values crashed with AttributeError instead of our error message, and a row with too many values was accepted. | test_bad_row | Oct 30 |
