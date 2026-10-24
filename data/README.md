# GradMatch data files

**All numbers are estimates for the Fall 2027 admission cycle.** Always verify on the
official site linked in each row before relying on them. Formats follow `CONTRIBUTING.md`.

| File | Rows | Notes |
|------|------|-------|
| `programs.csv` | 24 (MS and PhD, Computer Science / Data Science) | Tuition is per year. `avg_gpa` and `acceptance_rate` are estimates – most schools do not publish exact values. Empty `avg_gre` = GRE optional / not reported. Empty `min_toefl` = no published minimum. PhD tuition is usually waived for funded students; the posted rate is still listed. A PhD row with `stipend` > 0 means funded students get a tuition waiver, so the cost calculation charges no tuition; enter a stipend only if the official page says funding includes a tuition waiver. |
| `programs.csv` (rules) | – | `degree` is `MS` for every master's program (Master of Data Science, Master of Computer Science, MEng, …); the exact degree name goes in `program_name`. `field` must be exactly one of: `Computer Science`, `Data Science`, `Electrical and Computer Engineering`, `Business Analytics`. |
| `scholarships.csv` | 13 (scholarships, fellowships, assistantships, research, fee waiver) | `amount` is the yearly stipend or award. `special` tags: `first_gen`, `women_stem`, `new_american`, `underrepresented_minority`, `mcnair_scholar`. |
| `living_costs.csv` | 51 (50 states + DC) | Estimated yearly living cost for one graduate student (rent, food, transport, personal). Derived from a state cost-of-living index (US average = 100) × $200. Source: MERIC Cost of Living Data Series, https://meric.mo.gov/data/cost-living-data-series |

## Verification status
Each row must be checked by hand against
its website. Tick a file off when every row has been checked.

- [ ] `programs.csv` – tuition, deadline, TOEFL minimum checked on each website
- [ ] `scholarships.csv` – amount, eligibility, deadline checked on each website
- [ ] `living_costs.csv` – index values checked against the MERIC table
