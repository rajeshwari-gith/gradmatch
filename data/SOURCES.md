# Program data sources

**Verified: 3 of 24 rows (programs) · Scholarships verified: 0 of 13**
(This count covers only the **24 hand-entered rows** listed below. The 45,400 rows imported from
official government data are not checked by hand and are not part of it; see
[Imported rows](#imported-rows-ipeds-2024). 25 more programs are listed below but not yet in
`programs.csv`.)

One entry per program. Status is one of:
- **needs lookup** – the official page has not been opened yet; no value in `programs.csv` may be trusted
- **drafted** – values were copied from the official page, waiting for a second check
- **drafted (partly checked)** – only some values were checked on the official page; the Notes column says which
- **verified by &lt;name&gt; on &lt;date&gt;** – a team member opened the official page and checked every value

Rules: only real programs, and `website` must be the official program page (not a department home page).
If a value is not on the official page, leave an optional field (`avg_gre`, `min_toefl`) blank;
for a required number, put a clearly labeled estimate and note it in `data/README.md`.

## Values to copy from each official page
`program_name` (exact degree name) · `degree` (MS/PhD) · `tuition_in_state` and `tuition_out_state` (per year) ·
`duration_years` · `avg_gpa` and `acceptance_rate` (often not published → estimate) · `avg_gre` · `stipend` (PhD) ·
`min_toefl` · `application_deadline` for Fall 2027 · `website` (URL of the page used)

For PhD programs, also check that funding includes a **tuition waiver**. If it does not, or the page
does not say, note it in the row's Notes column before entering a `stipend`.

## Existing rows in `programs.csv` (24)
All values in these rows are estimates. Most `website` values are department home pages and must be
replaced by the program page.

| program_id | University | Program | Status | Source (official page) | Notes |
|---|---|---|---|---|---|
| GVSU-MSCS | Grand Valley State University | MS in Applied Computer Science | needs lookup |  | Name fixed: GVSU's degree is the MS in Applied Computer Science, not an MS in Computer Science. Catalog page found by search: https://www.gvsu.edu/catalog/department/master-of-science-in-computer-information-systems.htm |
| UMICH-MSCSE | University of Michigan | MS in Computer Science and Engineering | needs lookup |  | website is the department home page |
| UMICH-PHDCSE | University of Michigan | PhD in Computer Science and Engineering | needs lookup |  | website is the department home page |
| MSU-MSCS | Michigan State University | MS in Computer Science | needs lookup |  | website is the department page |
| WSU-MSCS | Wayne State University | MS in Computer Science | needs lookup |  | website is the department page |
| UIUC-MSCS | University of Illinois Urbana-Champaign | MS in Computer Science | needs lookup |  | website is the department home page |
| UIUC-PHDCS | University of Illinois Urbana-Champaign | PhD in Computer Science | needs lookup |  | website is the department home page |
| GT-MSCS | Georgia Institute of Technology | MS in Computer Science | needs lookup |  | website is the college home page |
| GT-PHDCS | Georgia Institute of Technology | PhD in Computer Science | verified by Rajeshwari Galugu on 2026-10-26 | https://www.cc.gatech.edu/phd-cs-admissions-requirements | Official page lists old-scale TOEFL minimum 100; confirm all fields before submission |
| UTA-MSCS | University of Texas at Austin | MS in Computer Science | needs lookup |  | website is the department home page |
| PURDUE-MSCS | Purdue University | MS in Computer Science | verified by Rajeshwari Galugu on 2026-10-26 | https://cs.purdue.edu/graduate/admission/steps.html | Official page confirms deadline; preferred old-scale TOEFL 100; confirm all fields before submission |
| PURDUE-PHDCS | Purdue University | PhD in Computer Science | verified by Rajeshwari Galugu on 2026-10-26 | https://cs.purdue.edu/graduate/admission/steps.html | Official page confirms deadline; preferred old-scale TOEFL 100; confirm all fields before submission |
| UW-PHDCSE | University of Washington | PhD in Computer Science and Engineering | needs lookup |  | website is the school home page |
| BERKELEY-PHDEECS | University of California Berkeley | PhD in Electrical Engineering and Computer Sciences | needs lookup |  | website is the department home page |
| CMU-PHDCS | Carnegie Mellon University | PhD in Computer Science | needs lookup |  | website is the department home page |
| HARVARD-PHDCS | Harvard University | PhD in Computer Science | needs lookup |  | website is the school home page |
| STANFORD-MSCS | Stanford University | MS in Computer Science | needs lookup |  | website is the department home page |
| UMN-PHDCS | University of Minnesota | PhD in Computer Science | needs lookup |  | website is the department page |
| OSU-MSCSE | Ohio State University | MS in Computer Science and Engineering | needs lookup |  | website is the department home page |
| ASU-MSCS | Arizona State University | MS in Computer Science | needs lookup |  | website is the school home page |
| COLUMBIA-MSDS | Columbia University | MS in Data Science | needs lookup |  | website is the institute home page |
| NYU-MSDS | New York University | MS in Data Science | needs lookup |  | website is the center home page |
| UCSD-MSDS | University of California San Diego | MS in Data Science | needs lookup |  | website is the institute home page |
| IU-MSDS | Indiana University Bloomington | MS in Data Science | needs lookup |  | website is the school home page |

## New programs to add (not in `programs.csv` yet)
The links below came from a web search on the university's own domain. They have **not been opened**
yet: confirm each one is the right, current program page before copying values.

| University | State | Program | Field | Degree | Status | Official page to open | Notes |
|---|---|---|---|---|---|---|---|
| University of Maryland, College Park | MD | MS in Computer Science | Computer Science | MS | needs lookup | https://www.cs.umd.edu/grad/ms-catalog |  |
| University of Maryland, College Park | MD | PhD in Computer Science | Computer Science | PhD | needs lookup | https://www.cs.umd.edu/grad/phd-catalog |  |
| University of California, Los Angeles | CA | MS in Computer Science | Computer Science | MS | needs lookup | https://www.cs.ucla.edu/graduate-admissions/ |  |
| University of California, Los Angeles | CA | PhD in Computer Science | Computer Science | PhD | needs lookup | https://www.cs.ucla.edu/graduate-admissions/ |  |
| University of Wisconsin–Madison | WI | MS in Computer Sciences | Computer Science | MS | needs lookup | https://www.cs.wisc.edu/grad/programs/traditional/ |  |
| University of Wisconsin–Madison | WI | PhD in Computer Sciences | Computer Science | PhD | needs lookup | https://www.cs.wisc.edu/grad/programs/traditional/ |  |
| University of Wisconsin–Madison | WI | MS in Data Science | Data Science | MS | needs lookup | https://guide.wisc.edu/graduate/statistics/data-science-ms/ |  |
| University of Southern California | CA | MS in Computer Science | Computer Science | MS | needs lookup | https://www.cs.usc.edu/academic-programs/masters/ |  |
| University of Southern California | CA | MS in Applied Data Science | Data Science | MS | needs lookup | https://viterbigradadmission.usc.edu/programs/masters/msprograms/data-science/ms-applied-data-science/ |  |
| University of Southern California | CA | PhD in Computer Science | Computer Science | PhD | needs lookup | no official page found by search – find it by hand |  |
| Northeastern University | MA | MS in Computer Science | Computer Science | MS | needs lookup | https://www.khoury.northeastern.edu/programs/computer-science-ms/ |  |
| Northeastern University | MA | MS in Data Science | Data Science | MS | needs lookup | https://www.khoury.northeastern.edu/programs/data-science-ms/ |  |
| Northeastern University | MA | PhD in Computer Science | Computer Science | PhD | needs lookup | https://www.khoury.northeastern.edu/phd-programs/ |  |
| Virginia Tech | VA | MS in Computer Science and Applications | Computer Science | MS | needs lookup | https://students.cs.vt.edu/Graduate/Degrees/MSThesis.html (deadlines: https://students.cs.vt.edu/Graduate/ApplicationDeadlines.html) |  |
| Virginia Tech | VA | PhD in Computer Science and Applications | Computer Science | PhD | needs lookup | https://students.cs.vt.edu/Graduate/Degrees/Doctorate.html |  |
| Texas A&M University | TX | MS in Computer Science | Computer Science | MS | needs lookup | https://engineering.tamu.edu/cse/academics/degrees/graduate/ms-cs.html |  |
| Texas A&M University | TX | PhD in Computer Science | Computer Science | PhD | needs lookup | https://engineering.tamu.edu/cse/academics/degrees/graduate/program-requirements/phd-deadlines/index.html |  |
| Texas A&M University | TX | MS in Data Science | Data Science | MS | needs lookup | https://catalog.tamu.edu/graduate/colleges-schools-interdisciplinary/interdisciplinary/data-science-ms/ |  |
| Penn State University Park | PA | MS in Computer Science and Engineering | Computer Science | MS | needs lookup | https://www.eecs.psu.edu/students/graduate/Graduate-Degree-Programs-CSE.aspx (deadlines: https://www.eecs.psu.edu/students/graduate/EECS-graduate-deadlines.aspx) |  |
| Penn State University Park | PA | PhD in Computer Science and Engineering | Computer Science | PhD | needs lookup | https://www.eecs.psu.edu/students/graduate/Graduate-Degree-Programs-CSE.aspx |  |
| Rutgers University–New Brunswick | NJ | MS in Computer Science | Computer Science | MS | needs lookup | https://www.cs.rutgers.edu/academics/graduate |  |
| Rutgers University–New Brunswick | NJ | PhD in Computer Science | Computer Science | PhD | needs lookup | https://grad.rutgers.edu/academics/programs/computer-science |  |
| Rutgers University–New Brunswick | NJ | MS in Data Science | Data Science | MS | needs lookup | https://msds-stat.rutgers.edu/ (the CS department also runs a Data Science MS – pick one and note which) |  |
| Rice University | TX | PhD in Computer Science | Computer Science | PhD | needs lookup | https://csweb.rice.edu/academics/graduate-programs/phd-program |  |
| Rice University | TX | Master of Data Science | Data Science | MS | needs lookup | https://csweb.rice.edu/academics/graduate-programs/master-data-science |  |

Notes for the lookup:
- Program names above are working names; copy the exact degree name from the official page.
- Some master's degrees are not called "MS" (Rice "Master of Data Science", Texas A&M "Master of Computer Science").
  They go in `programs.csv` with `degree` = `MS`, and the exact name goes in `program_name`.
- Rice's thesis MS in Computer Science is not admitted to directly, so it is not listed.

## Imported rows (IPEDS 2024)

`programs.csv` also has **45,400 rows with `source=ipeds`**, built by
`src/gradmatch/ipeds_import.py` from the US Department of Education's 2024 IPEDS files
(https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx):

- **HD2024** (institution directory): school name, state, main website and admissions page.
- **COST1_2024** (cost): yearly tuition plus required fees, undergraduate rates for `BS` and
  graduate rates for `MS` and `PhD`. This is a **school-wide rate**, not a price for one program.
- **C2024_A** (completions): degrees awarded per school, field (CIP code) and award level; a row is
  made when a school awarded at least 5 degrees in a field and level.
- **ADM2024** (admissions): for `BS` rows only, the acceptance rate and the 25th/75th percentile
  SAT and ACT scores.

A blank cell in these rows means **"not published"**: the government data has no admitted GPA,
GRE, TOEFL minimum or application deadline, no stipend for graduate programs, and no admissions
numbers for some schools. Blanks are never guesses. The `website` is the school's admissions page (or its
main site when there is none), not the program page. Column by column: `data/README.md`; how to run the import:
`docs/official-data-import.md`.

These rows are official data, so they are not listed one by one here and are not counted in the
"Verified" line above. A row that a person later checks on the official program page should be
added to the table above, so that it is counted.

