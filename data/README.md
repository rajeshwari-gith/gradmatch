# GradMatch data files

`programs.csv` holds two kinds of rows. Check the `source` column to see which kind a row is:

- **24 hand-entered rows** (`source` blank or `estimate`, or `official-page` once a person has
  checked the row on the program's official page). Computer Science and Data Science, MS and PhD.
  Their numbers are estimates for the Fall 2027 admission cycle unless `data/SOURCES.md` says the
  row was verified.
- **45,400 imported rows** (`source=ipeds`) from the official 2024 US Department of Education
  data (IPEDS). See [Imported rows](#imported-rows-ipeds-2024) below.

Always verify on the official site before relying on a number. Formats follow `CONTRIBUTING.md`.

| File | Rows | Notes |
|------|------|-------|
| `programs.csv` | 45,424 (24 hand-entered + 45,400 imported; 29,829 BS, 12,441 MS, 3,154 PhD) | Tuition is per year. In hand-entered rows, `avg_gpa` and `acceptance_rate` are estimates (most schools do not publish exact values) and the app labels them "(est.)". Empty `avg_gre` = GRE optional / not reported. Empty `min_toefl` = no published minimum. PhD tuition is usually waived for funded students; the posted rate is still listed. A PhD row with `stipend` > 0 means funded students get a tuition waiver, so the cost calculation charges no tuition; enter a stipend only if the official page says funding includes a tuition waiver. |
| `programs.csv` (rules) | – | `degree` is `BS`, `MS` or `PhD`. `degree` is `MS` for every master's program (Master of Data Science, Master of Computer Science, MEng, …) and `BS` for every bachelor's program (BA, BS, BBA, …); the exact degree name goes in `program_name`. `field` must be one of the 130 field names listed [below](#the-130-fields) (the `CIP_FIELDS` in `src/gradmatch/ipeds_import.py`), or `Electrical and Computer Engineering` / `Business Analytics` for hand-entered rows. A blank cell in `avg_gpa`, `acceptance_rate`, `stipend`, `application_deadline`, `avg_gre`, `min_toefl` or the test-score columns means **"not published"**, never a guess or 0. |
| `scholarships.csv` | 13 (scholarships, fellowships, assistantships, research, fee waiver) | `amount` is the yearly stipend or award. `special` tags: `first_gen`, `women_stem`, `new_american`, `underrepresented_minority`, `mcnair_scholar`. |
| `undergrad_scholarship_sheet.csv` | 10 (not loaded by the app) | A fill-in sheet for undergraduate scholarships, in the same style as the program lookup sheet. Only the name, the official URL (found by a web search on each organization's own domain, not yet opened) and `degree_levels` = `BS` are filled in; a person must open each page and fill in every other value, then `checked_by` and `checked_on`, before rows are copied into `scholarships.csv`. |
| `living_costs.csv` | 51 (50 states + DC) | Estimated yearly living cost for one graduate student (rent, food, transport, personal). Derived from a state cost-of-living index (US average = 100) × $200. Source: MERIC Cost of Living Data Series, https://meric.mo.gov/data/cost-living-data-series |
| `requirements.csv` | 0 (no requirement has been checked yet) | Essays and statements each program asks for: `program_id,name,required,limit_text,prompt_text,source_url,checked_by,checked_on`. One row per requirement. Every row must be copied from the official page by a person: `source_url` (https), `checked_by` and `checked_on` are required, `required` is `yes` or `no`. A blank `limit_text` or `prompt_text` means the page does not state it. Prompts are copied word for word and never written from memory. Loaded by `src/gradmatch/requirements.py`. |
| `requirements_sheet.csv` | 10 (not loaded by the app) | A blank sheet for the 10 programs already checked on official pages. Only `program_id`, `university` and `program_name` are filled in. A person opens the program's official page, fills one row per requirement (add rows for a program with several), then copies the checked rows into `requirements.csv` without the `university`, `program_name` and `notes` columns. |

## Imported rows (IPEDS 2024)

Built by `src/gradmatch/ipeds_import.py` from four IPEDS 2024 files
(https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx; how to run it: `docs/official-data-import.md`):

| IPEDS file | What it gives |
|---|---|
| `HD2024` (institution directory) | school name, state, main website and admissions page |
| `COST1_2024` (cost) | yearly tuition and required fees, undergraduate and graduate |
| `C2024_A` (completions) | degrees awarded per school, field (CIP code) and award level |
| `ADM2024` (admissions) | undergraduate applicants and admits, SAT and ACT percentiles |

A school gets a row for a degree and field when it awarded at least 5 of those degrees in 2024,
in a state that has a row in `living_costs.csv`. Programs already in the hand-entered rows are
skipped. Running the import again with `--merge` replaces the earlier imported rows, so the file
comes out the same; hand-entered rows are never changed.

What each column means in an imported row:

| Column | Value |
|---|---|
| `program_id` | `IPEDS-<school id>-<degree>-<CIP code>`, e.g. `IPEDS-498924-BS-52.0201` |
| `university`, `state` | official school name and state from HD |
| `program_name` | `<degree> in <field>`, e.g. `BS in Business Administration` (IPEDS has no program names) |
| `field` | one of the 130 fields, from the CIP code in C_A |
| `degree` | from the C_A award level: 5 → `BS`, 7 → `MS`, 17 (doctor's, research) → `PhD` |
| `tuition_in_state`, `tuition_out_state` | COST1 tuition plus required fees: undergraduate rates (`TUITION2`+`FEE2`, `TUITION3`+`FEE3`) for `BS`, graduate rates (`TUITION6`+`FEE6`, `TUITION7`+`FEE7`) for `MS` and `PhD`. **This is a school-wide rate, not a price for the program.** |
| `duration_years` | a default: 4 (BS), 2 (MS), 5 (PhD) |
| `stipend` | `0` for BS (there is no stipend for a bachelor's degree); blank (not published) for MS and PhD |
| `acceptance_rate` | BS only: admits ÷ applicants from ADM, 3 decimals; blank if not published or if the numbers make no sense |
| `sat_25`, `sat_75` | BS only: 25th and 75th percentile SAT of enrolled students (reading + math) from ADM; blank if not published |
| `act_25`, `act_75` | BS only: 25th and 75th percentile ACT composite from ADM; blank if not published |
| `avg_gpa`, `avg_gre`, `min_toefl`, `application_deadline` | always blank: the government data does not publish them |
| `website` | the school's admissions page from HD (`ADMINURL`), or its main website (`WEBADDR`) when there is none; never a program page |
| `source` | `ipeds` |

**Blank means "not published".** The app shows these values as "not published" or "n/a", never as
0, and leaves programs without a deadline out of the Deadlines tab and the calendar file.

### The 130 fields
Accounting, Actuarial Science, Aerospace Engineering, African American Studies, Agricultural Engineering, Animal Sciences, Anthropology, Applied Mathematics, Architecture, Artificial Intelligence, Astronomy, Athletic Training, Atmospheric Science, Behavioral Sciences, Biochemistry, Biological and Physical Sciences, Biology, Biomedical Engineering, Biomedical Sciences, Biotechnology, Business Administration, Business Economics, Business Statistics, Chemical Engineering, Chemistry, Civil Engineering, Clinical Laboratory Science, Clinical Psychology, Cognitive Science, Communication, Communication Sciences and Disorders, Computer Engineering, Computer Networking, Computer Programming, Computer Science, Counseling Psychology, Criminal Justice, Criminology, Cybersecurity, Data Science, Design, Dietetics, Early Childhood Education, Ecology, Economics, Education, Educational Leadership, Electrical Engineering, Elementary Education, Engineering Physics, English, Entrepreneurship, Environmental Engineering, Environmental Science, Environmental Studies, Exercise Physiology, Fashion Merchandising, Film Studies, Finance, Fine Arts, Food Science, French, General Business, General Engineering, General Studies, Geography, Geology, Graphic Design, Health Care Administration, History, Hospitality Management, Human Development and Family Studies, Human Resources Management, Industrial Engineering, Industrial-Organizational Psychology, Informatics, Information Science, Information Technology, Interior Design, International Business, International Relations, Journalism, Kinesiology, Liberal Arts, Linguistics, Management Information Systems, Marketing, Mass Communication, Materials Engineering, Mathematics, Mechanical Engineering, Mechatronics and Robotics, Medical Informatics, Molecular Biology, Music, Neuroscience, Nursing, Nursing Science, Nutrition, Organizational Leadership, Parks and Recreation Management, Pharmaceutical Sciences, Philosophy, Photography, Physics, Political Science, Project Management, Psychology, Public Administration, Public Health, Public Policy, Public Relations and Advertising, Real Estate, Religious Studies, School Counseling, Secondary Education, Social Work, Sociology, Spanish, Special Education, Speech Communication and Rhetoric, Sport Management, Statistics, Supply Chain Management, Systems Engineering, Teaching English as a Second Language, Theatre, Visual and Performing Arts, Web and Digital Media Design, Zoology.

## Verification status
The hand-entered rows must be checked by hand against their official pages; `data/SOURCES.md`
counts them. The imported rows are official data and are not part of that count. Tick a file off
when every hand-entered row has been checked.

- [ ] `programs.csv` (24 hand-entered rows) – tuition, deadline, TOEFL minimum checked on each website
- [ ] `scholarships.csv` – amount, eligibility, deadline checked on each website
- [ ] `living_costs.csv` – index values checked against the MERIC table
