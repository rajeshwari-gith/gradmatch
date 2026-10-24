# Defect Log

| ID | Date found | Module | Description | Severity | Found by (test) | Status |
|----|-----------|--------|-------------|----------|-----------------|--------|
| D-001 | 2026-10-23 | `cost.py` | A PhD program labeled "Fully Funded" still showed a yearly cost above $0 (Michigan $6,200, Illinois $23,400, CMU $26,600, Harvard $37,000, Minnesota $5,000), because the stipend was subtracted from tuition + living cost instead of treating tuition as waived. A student with a low budget would not see funded PhD programs at all. | Medium (wrong result, no crash) | `test_cost.py::test_funded_phd_pays_no_tuition` | Fixed 2026-10-23 (commit "Waive tuition for funded PhD programs") |
