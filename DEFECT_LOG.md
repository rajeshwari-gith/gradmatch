# Defect Log

| ID | Date found | Module | Description | Severity | Found by (test) | Status |
|----|-----------|--------|-------------|----------|-----------------|--------|
| D-001 | 2026-10-23 | `cost.py` | A PhD program labeled "Fully Funded" still showed a yearly cost above $0 (Michigan $6,200, Illinois $23,400, CMU $26,600, Harvard $37,000, Minnesota $5,000), because the stipend was subtracted from tuition + living cost instead of treating tuition as waived. A student with a low budget would not see funded PhD programs at all. | Medium (wrong result, no crash) | `test_cost.py::test_funded_phd_pays_no_tuition` | Fixed 2026-10-23 (commit "Waive tuition for funded PhD programs") |
| D-002 | 2026-10-23 | `app/streamlit_app.py` | The cost-vs-GPA chart crashed the whole results page for every valid search ("encoding field is specified without a type"): the tooltip fields had no data type. Found while building the results page, before it was merged, so no user ever saw it. | High (page crash on every valid search) | `test_profile_form.py` (8 tests failed after the chart was added) | Fixed 2026-10-23 before merge (tooltip fields given explicit types) |
