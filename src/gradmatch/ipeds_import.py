"""Build program rows from the official US Department of Education (IPEDS) files.

Three files from https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx are needed:

  HD<year>        institution directory (name, state, website)
  COST1_<year>    undergraduate and graduate tuition and required fees
  C<year>_A       degrees awarded by field (CIP code) and award level

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

CIP_FIELDS = {"11.0701": "Computer Science", "30.7001": "Data Science"}
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
                  "source"]

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
    "directory": ["UNITID", "INSTNM", "STABBR", "WEBADDR"],
    "cost": ["UNITID", "TUITION2", "TUITION3", "FEE2", "FEE3", "TUITION6", "TUITION7", "FEE6", "FEE7"],
    "completions": ["UNITID", "CIPCODE", "AWLEVEL", "CTOTALT"],
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
        website = website_of(row["WEBADDR"])
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


def existing_keys(existing_rows) -> set[tuple[str, str, str]]:
    """(official school name, degree, field) of rows we already have, to avoid duplicates."""
    return {(normalize(OFFICIAL_NAMES.get(r["university"], r["university"])), r["degree"], r["field"])
            for r in existing_rows}


def build_rows(schools, tuition, awards, existing_rows) -> list[dict]:
    """New program rows, sorted by school then degree, skipping what we already have.

    tuition is {degree: {unit id: (in-state, out-of-state)}}. Bachelor's rows get a stipend
    of 0, because there is no stipend for a bachelor's degree.
    """
    have = existing_keys(existing_rows)
    rows = []
    for (unit, degree, field), _count in sorted(awards.items()):
        school, rates = schools.get(unit), tuition[degree].get(unit)
        if not school or not rates or (normalize(school["name"]), degree, field) in have:
            continue
        rows.append({
            "program_id": f"IPEDS-{unit}-{degree.upper()}-{''.join(w[0] for w in field.split())}",
            "university": school["name"],
            "program_name": f"{degree} in {field}",
            "field": field, "degree": degree, "state": school["state"],
            "tuition_in_state": round(rates[0]), "tuition_out_state": round(rates[1]),
            "duration_years": DEFAULT_YEARS[degree],
            "avg_gpa": "", "avg_gre": "", "acceptance_rate": "",
            "stipend": "0" if degree == "BS" else "",
            "min_toefl": "", "application_deadline": "",
            "website": school["website"], "source": SOURCE,
        })
    return rows


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
    parser.add_argument("--output", default="data/programs_ipeds.csv")
    parser.add_argument("--report", help="optional CSV: our tuition vs the official rates")
    parser.add_argument("--min-awards", type=int, default=DEFAULT_MIN_AWARDS)
    args = parser.parse_args(argv)

    data = Path(args.data)
    with open(data / "living_costs.csv", newline="", encoding="utf-8") as file:
        states = {row["state"] for row in csv.DictReader(file)}
    with open(data / "programs.csv", newline="", encoding="utf-8") as file:
        existing = list(csv.DictReader(file))

    schools = institutions(read_csv(args.hd, "directory"), states)
    cost_rows = read_csv(args.cost, "cost")
    tuition = {degree: tuition_rates(cost_rows, degree) for degree in DEFAULT_YEARS}
    awards = awarded_programs(read_csv(args.completions, "completions"), args.min_awards)

    rows = build_rows(schools, tuition, awards, existing)
    write_csv(args.output, rows)
    print(f"{len(rows)} new program row(s) written to {args.output}")
    if args.report:
        report = tuition_check(schools, tuition["MS"], existing)
        write_csv(args.report, report, list(report[0]) if report else ["program_id"])
        print(f"tuition check for {len(report)} existing row(s) written to {args.report}")
    return 0


if __name__ == "__main__":      # pragma: no cover
    raise SystemExit(main())
