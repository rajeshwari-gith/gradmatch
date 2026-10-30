# Data quality report (snapshot)

Made on **2026-10-30** from `main` at `f8277c8` with:

```
PYTHONPATH=src python -m gradmatch.data_report
```

In plain words: this is a picture of the data on one day. Run the command again for the current
numbers. A blank cell in an imported row means the government does not publish that value; it is
not an error. "Checked by hand" counts only the hand-entered rows listed in `data/SOURCES.md`.

```
Programs: 45,424    Scholarships: 13

Programs by source:
  ipeds                                     45,393
  estimate                                      24
  official-page                                  7

Programs by degree:
  BS                                        29,829
  MS                                        12,441
  PhD                                        3,154

Programs by field (130 fields):
  Business Administration                    2,240
  Biology                                    1,520
  Psychology                                 1,503
  Nursing                                    1,253
  Accounting                                 1,237
  English                                    1,161
  History                                    1,094
  Political Science                            996
  Elementary Education                         945
  Computer Science                             930
  Mathematics                                  913
  Social Work                                  884
  Chemistry                                    875
  Sociology                                    830
  Marketing                                    733
  Educational Leadership                       712
  Kinesiology                                  689
  Finance                                      682
  Mechanical Engineering                       678
  Physics                                      639
  Sport Management                             614
  Electrical Engineering                       604
  Special Education                            579
  Health Care Administration                   578
  Speech Communication and Rhetoric            576
  Music                                        567
  Criminal Justice                             550
  Education                                    540
  Civil Engineering                            507
  Philosophy                                   478
  Public Health                                472
  Anthropology                                 468
  Early Childhood Education                    461
  Theatre                                      461
  Fine Arts                                    452
  Biochemistry                                 435
  Spanish                                      420
  Environmental Science                        418
  Economics                                    417
  Liberal Arts                                 407
  General Business                             400
  Geology                                      400
  Public Administration                        391
  Organizational Leadership                    388
  School Counseling                            378
  Biomedical Engineering                       376
  Information Technology                       370
  Secondary Education                          366
  Cybersecurity                                358
  Environmental Studies                        340
  Computer Engineering                         326
  Chemical Engineering                         320
  Neuroscience                                 315
  Human Resources Management                   285
  Information Science                          285
  Communication                                261
  International Relations                      257
  Statistics                                   251
  Graphic Design                               251
  Journalism                                   243
  Mass Communication                           240
  Biomedical Sciences                          235
  General Studies                              223
  International Business                       221
  Criminology                                  218
  Athletic Training                            212
  Industrial Engineering                       208
  General Engineering                          198
  Communication Sciences and Disorders         187
  Entrepreneurship                             185
  Management Information Systems               181
  Linguistics                                  174
  Materials Engineering                        173
  Supply Chain Management                      172
  Clinical Laboratory Science                  169
  Human Development and Family Studies         167
  Geography                                    167
  Clinical Psychology                          165
  Aerospace Engineering                        161
  Hospitality Management                       160
  Data Science                                 159
  Exercise Physiology                          156
  Religious Studies                            155
  Environmental Engineering                    154
  Film Studies                                 151
  Teaching English as a Second Language        145
  Applied Mathematics                          144
  Public Policy                                144
  Business Economics                           140
  Dietetics                                    138
  Animal Sciences                              137
  Interior Design                              133
  Design                                       128
  French                                       127
  Biotechnology                                113
  Architecture                                 111
  Public Relations and Advertising             106
  Industrial-Organizational Psychology         102
  Medical Informatics                           96
  Visual and Performing Arts                    92
  Nursing Science                               90
  Parks and Recreation Management               89
  Systems Engineering                           86
  Biological and Physical Sciences              82
  Food Science                                  79
  Behavioral Sciences                           78
  Business Statistics                           73
  Pharmaceutical Sciences                       72
  Real Estate                                   72
  Counseling Psychology                         71
  Actuarial Science                             68
  African American Studies                      67
  Project Management                            67
  Nutrition                                     66
  Photography                                   66
  Atmospheric Science                           66
  Informatics                                   61
  Cognitive Science                             60
  Ecology                                       60
  Astronomy                                     56
  Engineering Physics                           54
  Agricultural Engineering                      53
  Molecular Biology                             51
  Mechatronics and Robotics                     49
  Zoology                                       48
  Fashion Merchandising                         47
  Artificial Intelligence                       44
  Web and Digital Media Design                  42
  Computer Programming                          41
  Computer Networking                           40

Blank cells in the 45,393 imported (ipeds) rows (blank = not published):
  program_id                   0  0%
  university                   0  0%
  program_name                 0  0%
  field                        0  0%
  degree                       0  0%
  state                        0  0%
  tuition_in_state             0  0%
  tuition_out_state            0  0%
  duration_years               0  0%
  avg_gpa                 45,393  100%
  avg_gre                 45,393  100%
  acceptance_rate         17,517  39%
  stipend                 15,564  34%
  min_toefl               45,393  100%
  application_deadline    45,393  100%
  website                      0  0%
  source                       0  0%
  sat_25                  24,975  55%
  sat_75                  24,975  55%
  act_25                  25,019  55%
  act_75                  25,019  55%

Duplicate program ids: none
Duplicate scholarship ids: none
Websites not starting with https://: none

Checked by hand on official pages (from SOURCES.md):
  programs:     10 of 31 hand-entered rows
  scholarships: 0 of 13
```

What it shows on this date:
- All 45,424 programs have a unique id and an https website; the 13 scholarships too.
- The government data never has an admitted GPA, GRE, TOEFL minimum or application deadline
  (100% blank), so the app shows "not published" for those.
- Acceptance rates are blank in 39% of imported rows: graduate programs never have one, and some
  colleges do not report admissions. SAT/ACT ranges are blank in about 55% (graduate rows, and
  colleges that do not report scores). Stipends are blank in 34%: graduate stipends are not published, while
  bachelor's rows have a stipend of 0.
- 10 of the 31 hand-entered programs are checked on official pages; no scholarship is checked yet.
