"""Build program rows from the official US Department of Education (IPEDS) files.

Three files from https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx are needed:

  HD<year>        institution directory (name, state, website)
  COST1_<year>    undergraduate and graduate tuition and required fees
  C<year>_A       degrees awarded by field (CIP code) and award level
  ADM<year>       (optional) undergraduate applicants, admits and SAT/ACT percentiles

A school gets a row for a degree and field when it awarded at least
`min_awards` of those degrees in the year. Values the government does not
publish (admitted GPA, acceptance rate, stipend, deadline) are left blank,
which the app shows as "not published" (see CONTRIBUTING.md). Tuition is the
school-wide graduate rate, not a per-program price.

Run: python -m gradmatch.ipeds_import --hd HD2024.csv --cost cost1_2024.csv
         --completions C2024_a.csv --data data --output data/programs_ipeds.csv
"""
import argparse
import csv
import re
from pathlib import Path

CIP_FIELDS = {      # CIP code -> field name shown in the app
    "11.0102": "Artificial Intelligence", "11.0103": "Information Technology",
    "11.0401": "Information Science", "11.0701": "Computer Science",
    "11.1003": "Cybersecurity", "30.7001": "Data Science",
    "14.0201": "Aerospace Engineering", "14.0501": "Biomedical Engineering",
    "14.0701": "Chemical Engineering", "14.0801": "Civil Engineering",
    "14.0901": "Computer Engineering", "14.1001": "Electrical Engineering",
    "14.1901": "Mechanical Engineering", "14.3501": "Industrial Engineering",
    "26.0101": "Biology", "27.0101": "Mathematics", "27.0501": "Statistics",
    "40.0501": "Chemistry", "40.0801": "Physics", "03.0104": "Environmental Science",
    "52.0201": "Business Administration", "52.0301": "Accounting", "52.0801": "Finance",
    "52.1401": "Marketing", "45.0601": "Economics",
    "42.0101": "Psychology", "51.3801": "Nursing", "13.0101": "Education",
    "45.1001": "Political Science", "23.0101": "English",
    "51.2201": "Public Health", "44.0701": "Social Work", "04.0201": "Architecture",
    # more fields (each has at least 40 schools awarding it)
     "01.0901": "Animal Sciences", "01.1001": "Food Science", "03.0103": "Environmental Studies",
     "05.0201": "African American Studies", "09.0100": "Communication",
     "09.0101": "Speech Communication and Rhetoric", "09.0102": "Mass Communication", "09.0401": "Journalism",
     "09.0900": "Public Relations and Advertising", "11.0104": "Informatics", "11.0201": "Computer Programming",
     "11.0801": "Web and Digital Media Design", "11.0901": "Computer Networking",
     "13.0401": "Educational Leadership", "13.1001": "Special Education", "13.1101": "School Counseling",
     "13.1202": "Elementary Education", "13.1205": "Secondary Education", "13.1210": "Early Childhood Education",
     "13.1401": "Teaching English as a Second Language", "14.0101": "General Engineering",
     "14.0301": "Agricultural Engineering", "14.1201": "Engineering Physics",
     "14.1401": "Environmental Engineering", "14.1801": "Materials Engineering",
     "14.2701": "Systems Engineering", "14.4201": "Mechatronics and Robotics", "16.0102": "Linguistics",
     "16.0901": "French", "16.0905": "Spanish", "19.0501": "Nutrition",
     "19.0701": "Human Development and Family Studies", "24.0101": "Liberal Arts", "24.0102": "General Studies",
     "26.0102": "Biomedical Sciences", "26.0202": "Biochemistry", "26.0204": "Molecular Biology",
     "26.0701": "Zoology", "26.0908": "Exercise Physiology", "26.1201": "Biotechnology", "26.1301": "Ecology",
     "26.1501": "Neuroscience", "27.0301": "Applied Mathematics", "30.0101": "Biological and Physical Sciences",
     "30.1701": "Behavioral Sciences", "30.2501": "Cognitive Science",
     "31.0301": "Parks and Recreation Management", "31.0504": "Sport Management", "31.0505": "Kinesiology",
     "38.0101": "Philosophy", "38.0201": "Religious Studies", "40.0201": "Astronomy",
     "40.0401": "Atmospheric Science", "40.0601": "Geology", "42.2801": "Clinical Psychology",
     "42.2804": "Industrial-Organizational Psychology", "42.2813": "Counseling Psychology",
     "43.0104": "Criminal Justice", "44.0401": "Public Administration", "44.0501": "Public Policy",
     "45.0201": "Anthropology", "45.0401": "Criminology", "45.0701": "Geography",
     "45.0901": "International Relations", "45.1101": "Sociology", "50.0101": "Visual and Performing Arts",
     "50.0401": "Design", "50.0408": "Interior Design", "50.0409": "Graphic Design", "50.0501": "Theatre",
     "50.0601": "Film Studies", "50.0605": "Photography", "50.0702": "Fine Arts", "50.0901": "Music",
     "51.0201": "Communication Sciences and Disorders", "51.0701": "Health Care Administration",
     "51.0913": "Athletic Training", "51.1005": "Clinical Laboratory Science",
     "51.2010": "Pharmaceutical Sciences", "51.2706": "Medical Informatics", "51.3101": "Dietetics",
     "51.3808": "Nursing Science", "52.0101": "General Business", "52.0203": "Supply Chain Management",
     "52.0211": "Project Management", "52.0213": "Organizational Leadership", "52.0601": "Business Economics",
     "52.0701": "Entrepreneurship", "52.0901": "Hospitality Management", "52.1001": "Human Resources Management",
     "52.1101": "International Business", "52.1201": "Management Information Systems",
     "52.1302": "Business Statistics", "52.1304": "Actuarial Science", "52.1501": "Real Estate",
     "52.1902": "Fashion Merchandising", "54.0101": "History",
}
CIP_BY_FIELD = {field: cip for cip, field in CIP_FIELDS.items()}
AWARD_DEGREES = {"5": "BS", "7": "MS", "17": "PhD"}   # IPEDS award levels: 5 bachelor's, 7 master's, 17 doctor's research
DEFAULT_YEARS = {"BS": 4.0, "MS": 2.0, "PhD": 5.0}
# COST1 columns: in-state tuition, out-of-state tuition, in-state fees, out-of-state fees
TUITION_COLUMNS = {"BS": ("TUITION2", "TUITION3", "FEE2", "FEE3"),
                   "MS": ("TUITION6", "TUITION7", "FEE6", "FEE7"),
                   "PhD": ("TUITION6", "TUITION7", "FEE6", "FEE7")}
DEFAULT_MIN_AWARDS = 5
SOURCE = "ipeds"

OUTPUT_COLUMNS = ["program_id", "university", "program_name", "field", "degree", "state",
                  "tuition_in_state", "tuition_out_state", "duration_years", "avg_gpa", "avg_gre",
                  "acceptance_rate", "stipend", "min_toefl", "application_deadline", "website",
                  "source", "sat_25", "sat_75", "act_25", "act_75"]

# Existing rows use common names; IPEDS uses the official ones.
OFFICIAL_NAMES = {
    "University of California Berkeley": "University of California-Berkeley",
    "University of California San Diego": "University of California-San Diego",
    "Indiana University Bloomington": "Indiana University-Bloomington",
    "University of Michigan": "University of Michigan-Ann Arbor",
    "University of Minnesota": "University of Minnesota-Twin Cities",
    "University of Washington": "University of Washington-Seattle Campus",
    "Ohio State University": "Ohio State University-Main Campus",
    "Purdue University": "Purdue University-Main Campus",
    "University of Texas at Austin": "The University of Texas at Austin",
    "Arizona State University": "Arizona State University Campus Immersion",
    "Georgia Institute of Technology": "Georgia Institute of Technology-Main Campus",
    "Columbia University": "Columbia University in the City of New York",
}

REQUIRED_COLUMNS = {
    "directory": ["UNITID", "INSTNM", "STABBR", "WEBADDR", "ADMINURL"],
    "cost": ["UNITID", "TUITION2", "TUITION3", "FEE2", "FEE3", "TUITION6", "TUITION7", "FEE6", "FEE7"],
    "completions": ["UNITID", "CIPCODE", "AWLEVEL", "CTOTALT"],
    "admissions": ["UNITID", "APPLCN", "ADMSSN", "SATVR25", "SATVR75", "SATMT25", "SATMT75",
                   "ACTCM25", "ACTCM75"],
}


class ImportDataError(ValueError):
    """Raised when an official file does not have the columns we expect."""


def read_csv(path, kind) -> list[dict]:
    """Read an official file (UTF-8 with or without a BOM) and check its columns."""
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        header = [name.strip() for name in (reader.fieldnames or [])]
        missing = [c for c in REQUIRED_COLUMNS[kind] if c not in header]
        if missing:
            raise ImportDataError(f"{path}: missing column(s): {', '.join(missing)}")
        return [{key.strip(): (value or "").strip() for key, value in row.items() if key}
                for row in reader]


def normalize(name) -> str:
    """Lowercase letters and digits only, so 'California-Berkeley' == 'california berkeley'."""
    return " ".join(re.findall(r"[a-z0-9]+", name.lower()))


def website_of(address) -> str:
    address = address.strip()
    if not address:
        return ""
    return address if address.lower().startswith(("http://", "https://")) else f"https://{address}"


def money(text) -> float | None:
    """A non-negative amount, or None when the cell is blank, not a number or negative."""
    try:
        value = float(text)
    except ValueError:
        return None
    return value if value >= 0 else None


def institutions(directory_rows, states) -> dict[str, dict]:
    """{unit id: name/state/website} for schools in a state we have living costs for."""
    found = {}
    for row in directory_rows:
        website = website_of(row["ADMINURL"]) or website_of(row["WEBADDR"])   # admissions page first
        if row["STABBR"] in states and website and row["INSTNM"]:
            found[row["UNITID"]] = {"name": row["INSTNM"], "state": row["STABBR"],
                                    "website": website}
    return found


def tuition_rates(cost_rows, degree) -> dict[str, tuple[float, float]]:
    """{unit id: (in-state, out-of-state)} yearly tuition plus required fees for a degree level."""
    in_column, out_column, fee_in_column, fee_out_column = TUITION_COLUMNS[degree]
    rates = {}
    for row in cost_rows:
        in_state, out_state = money(row[in_column]), money(row[out_column])
        if in_state is None or out_state is None:
            continue
        fee_in = money(row[fee_in_column]) or 0.0
        fee_out = money(row[fee_out_column]) or 0.0
        rates[row["UNITID"]] = (in_state + fee_in, out_state + fee_out)
    return rates


def awarded_programs(completion_rows, min_awards) -> dict[tuple[str, str, str], int]:
    """{(unit id, degree, field): degrees awarded} for the fields and levels we cover."""
    totals = {}
    for row in completion_rows:
        field, degree = CIP_FIELDS.get(row["CIPCODE"]), AWARD_DEGREES.get(row["AWLEVEL"])
        count = money(row["CTOTALT"])
        if field and degree and count:
            key = (row["UNITID"], degree, field)
            totals[key] = totals.get(key, 0) + int(count)
    return {key: count for key, count in totals.items() if count >= min_awards}


def admissions(admission_rows) -> dict[str, dict]:
    """{unit id: acceptance rate and SAT/ACT percentiles} for undergraduate admissions.

    A value that is missing or makes no sense stays blank (None). The SAT total is the
    reading and math percentile added together.
    """
    found = {}
    for row in admission_rows:
        applicants, admitted = money(row["APPLCN"]), money(row["ADMSSN"])
        rate = None
        if applicants and admitted is not None and admitted <= applicants:
            rate = round(admitted / applicants, 3)
        found[row["UNITID"]] = {
            "acceptance_rate": rate,
            "sat_25": _sum_scores(row["SATVR25"], row["SATMT25"]),
            "sat_75": _sum_scores(row["SATVR75"], row["SATMT75"]),
            "act_25": _score(row["ACTCM25"]), "act_75": _score(row["ACTCM75"]),
        }
    return found


def _score(text) -> int | None:
    value = money(text)
    return int(value) if value else None


def _sum_scores(first, second) -> int | None:
    a, b = _score(first), _score(second)
    return a + b if a and b else None


def existing_keys(existing_rows) -> set[tuple[str, str, str]]:
    """(official school name, degree, field) of rows we already have, to avoid duplicates."""
    return {(normalize(OFFICIAL_NAMES.get(r["university"], r["university"])), r["degree"], r["field"])
            for r in existing_rows}


def build_rows(schools, tuition, awards, existing_rows, admission=None) -> list[dict]:
    """New program rows, sorted by school then degree, skipping what we already have.

    tuition is {degree: {unit id: (in-state, out-of-state)}}. Bachelor's rows get a stipend
    of 0, because there is no stipend for a bachelor's degree. admission is the result of
    admissions(); it fills the acceptance rate and test-score percentiles of bachelor's rows.
    """
    admission = admission or {}
    have = existing_keys(existing_rows)
    rows = []
    for (unit, degree, field), _count in sorted(awards.items()):
        school, rates = schools.get(unit), tuition[degree].get(unit)
        if not school or not rates or (normalize(school["name"]), degree, field) in have:
            continue
        rows.append({
            "program_id": f"IPEDS-{unit}-{degree.upper()}-{CIP_BY_FIELD[field]}",
            "university": school["name"],
            "program_name": f"{degree} in {field}",
            "field": field, "degree": degree, "state": school["state"],
            "tuition_in_state": round(rates[0]), "tuition_out_state": round(rates[1]),
            "duration_years": DEFAULT_YEARS[degree],
            "avg_gpa": "", "avg_gre": "", "acceptance_rate": "",
            "stipend": "0" if degree == "BS" else "",
            "min_toefl": "", "application_deadline": "",
            "website": school["website"], "source": SOURCE,
            "sat_25": "", "sat_75": "", "act_25": "", "act_75": "",
        })
        if degree == "BS":
            _fill_admissions(rows[-1], admission.get(unit, {}))
    return rows


def _fill_admissions(row, found) -> None:
    for name in ("acceptance_rate", "sat_25", "sat_75", "act_25", "act_75"):
        if found.get(name) is not None:
            row[name] = found[name]


def kept_rows(path) -> list[dict]:
    """The rows of the programs file that did not come from this importer."""
    with open(path, newline="", encoding="utf-8") as file:
        return [row for row in csv.DictReader(file) if row.get("source") != SOURCE]


def merge_programs(path, new_rows) -> None:
    """Replace every earlier imported row in the programs file at path with new_rows.

    Running the import again therefore gives the same file. Rows from other sources are
    untouched; missing columns are added and old rows get blanks in them."""
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        columns = list(reader.fieldnames or [])
    old_rows = kept_rows(path)
    columns += [name for name in OUTPUT_COLUMNS if name not in columns]
    write_csv(path, [{**{name: "" for name in columns}, **row} for row in old_rows + new_rows], columns)


def tuition_check(schools, tuition, existing_rows) -> list[dict]:
    """Compare the tuition typed into our own rows with the official school rates."""
    by_name = {normalize(s["name"]): unit for unit, s in schools.items()}
    report = []
    for row in existing_rows:
        unit = by_name.get(normalize(OFFICIAL_NAMES.get(row["university"], row["university"])))
        if unit in tuition:
            ours = (float(row["tuition_in_state"]), float(row["tuition_out_state"]))
            official = tuition[unit]
            report.append({"program_id": row["program_id"], "ours_in": ours[0], "ours_out": ours[1],
                           "official_in": round(official[0]), "official_out": round(official[1]),
                           "in_state_difference": round((ours[0] - official[0]) / official[0] * 100)
                           if official[0] else None})
    return report


def write_csv(path, rows, columns=OUTPUT_COLUMNS) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--hd", required=True, help="HD<year> directory CSV")
    parser.add_argument("--cost", required=True, help="COST1_<year> CSV")
    parser.add_argument("--completions", required=True, help="C<year>_A CSV")
    parser.add_argument("--data", default="data", help="folder with programs.csv and living_costs.csv")
    parser.add_argument("--admissions", help="optional ADM<year> CSV (bachelor's acceptance rate and SAT/ACT)")
    parser.add_argument("--output", default="data/programs_ipeds.csv")
    parser.add_argument("--merge", action="store_true",
                        help="also add the new rows to programs.csv in the data folder")
    parser.add_argument("--report", help="optional CSV: our tuition vs the official rates")
    parser.add_argument("--min-awards", type=int, default=DEFAULT_MIN_AWARDS)
    args = parser.parse_args(argv)

    data = Path(args.data)
    with open(data / "living_costs.csv", newline="", encoding="utf-8") as file:
        states = {row["state"] for row in csv.DictReader(file)}
    existing = kept_rows(data / "programs.csv")      # earlier imported rows are rebuilt, not kept

    schools = institutions(read_csv(args.hd, "directory"), states)
    cost_rows = read_csv(args.cost, "cost")
    tuition = {degree: tuition_rates(cost_rows, degree) for degree in DEFAULT_YEARS}
    awards = awarded_programs(read_csv(args.completions, "completions"), args.min_awards)

    admission = admissions(read_csv(args.admissions, "admissions")) if args.admissions else None
    rows = build_rows(schools, tuition, awards, existing, admission)
    write_csv(args.output, rows)
    print(f"{len(rows)} new program row(s) written to {args.output}")
    if args.merge:
        merge_programs(data / "programs.csv", rows)
        print(f"{len(rows)} row(s) added to {data / 'programs.csv'}")
    if args.report:
        report = tuition_check(schools, tuition["MS"], existing)
        write_csv(args.report, report, list(report[0]) if report else ["program_id"])
        print(f"tuition check for {len(report)} existing row(s) written to {args.report}")
    return 0


if __name__ == "__main__":      # pragma: no cover
    raise SystemExit(main())
