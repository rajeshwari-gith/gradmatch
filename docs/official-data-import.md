# Importing official government data (IPEDS)

`src/gradmatch/ipeds_import.py` builds program rows from three files published by the
US Department of Education (https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx), 2024 data:

| File | What it gives us |
|---|---|
| `HD2024` | school name, state, website |
| `COST1_2024` | graduate tuition and required fees (`TUITION6`/`FEE6` in-state, `TUITION7`/`FEE7` out-of-state) |
| `C2024_A` | degrees awarded by field (CIP 11.0701 Computer Science, 30.7001 Data Science) and award level (7 master's, 17 doctoral) |

```
python -m gradmatch.ipeds_import --hd HD2024.csv --cost cost1_2024.csv \
    --completions C2024_a.csv --data data --output data/programs_ipeds.csv \
    --report data/tuition_check.csv
```

Rules
- A school gets a row for a degree and field when it awarded at least 5 of those degrees in the year (`--min-awards`).
- Only states that have a row in `living_costs.csv` are used.
- Programs already in `programs.csv` from other sources are skipped (matched by official school name, degree and field).
- With `--merge`, earlier imported rows (`source=ipeds`) are replaced, so running the import again gives the same file. Hand-entered and verified rows are never touched.
- The website of each row is the school's admissions page (HD column `ADMINURL`), or its home page when there is none.
- Tuition is the school-wide graduate rate plus required fees. It is not a per-program price.
- Admitted GPA, acceptance rate, stipend and deadline are not published. They are left blank and shown as "not published".
- Duration is a default (MS 2 years, PhD 5 years).
- Every new row has `source=ipeds`.
- `--report` compares the tuition typed into our own rows with the official rates, so wrong estimates can be corrected.
