# Defects

| ID | Date | File | Problem | Found by | Fixed |
|----|------|------|---------|----------|-------|
| 1 | Oct 30 | data_loader.py | A row with too few values crashed with AttributeError instead of our error message, and a row with too many values was accepted. | test_bad_program_row | Oct 30 |
| 2 | Oct 30 | streamlit_app.py | The app crashed on start with "No module named gradmatch" when run with `streamlit run`, because Python couldn't find the src folder. The tests passed because pytest adds src itself. | Running the app by hand | Oct 30 |
| 3 | Oct 30 | streamlit_app.py | The MS results table showed a Funding column saying "Not listed" for every program. Hiding the column only changed what was shown, not the table's data. | test_ms_table_has_no_funding_column | Oct 30 |
