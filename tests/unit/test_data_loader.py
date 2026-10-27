"""Unit tests for data_loader.py.

Technique: equivalence partitioning. For each loader the input is split
into one valid class and several invalid classes (missing column, value
out of range, bad date, bad degree, not a number, empty required cell),
with at least one test per class. Range limits (GPA 0-4, rate 0-1) also
get boundary-value tests.

Tests never read the real CSVs in data/. Each test writes a tiny CSV into
pytest's tmp_path folder.
"""
# In plain words: these tests feed the loader small, hand-made CSV files, some correct and
# some broken on purpose, and check that good rows load with the right types and bad rows are
# stopped with a clear message. We never use the real data here, so a change to the real data
# can never break these tests, and every test is fast and repeatable.

import csv
from datetime import date

import pytest

from gradmatch.data_loader import (
    DataError,
    load_living_costs,
    load_programs,
    load_scholarships,
)
from gradmatch.models import Program, Scholarship

pytestmark = pytest.mark.unit


# ---- Helpers that build small CSV files ----
# Each helper makes one valid row; a test changes only the cell it is about, so it is obvious what is being tested.

def valid_program_row(**changes) -> dict:
    row = dict(
        program_id="P1",
        university="Test University",
        program_name="MS in Computer Science",
        field="Computer Science",
        degree="MS",
        state="MI",
        tuition_in_state="15000",
        tuition_out_state="30000",
        duration_years="2",
        avg_gpa="3.40",
        avg_gre="315",
        acceptance_rate="0.40",
        stipend="0",
        min_toefl="80",
        application_deadline="2027-01-15",
        website="https://example.edu/ms-cs",
    )
    row.update(changes)
    return row


def valid_scholarship_row(**changes) -> dict:
    row = dict(
        scholarship_id="S1",
        name="Test Fellowship",
        type="fellowship",
        amount="10000",
        degree_levels="MS;PhD",
        fields="Any",
        min_gpa="3.0",
        citizenship="US;PR",
        states="Any",
        special="",
        deadline="2026-12-01",
        website="https://example.org/fellowship",
    )
    row.update(changes)
    return row


def write_csv(tmp_path, rows, name="data.csv", columns=None):
    """Write rows (a list of dicts) to tmp_path/name and return the path."""
    path = tmp_path / name
    columns = columns or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


# =====================================================================
# load_programs
# Why: programs.csv feeds every search, so each kind of bad cell gets its own test (equivalence classes).
# =====================================================================

# ---- Valid class ----
# Why: first prove that a correct row loads and every cell gets the right Python type.

def test_programs_valid_row_is_loaded_with_correct_types(tmp_path):
    path = write_csv(tmp_path, [valid_program_row()])

    [program] = load_programs(path)

    assert program.program_id == "P1"
    assert program.degree == "MS"
    assert program.tuition_in_state == 15000.0
    assert program.avg_gpa == 3.40
    assert program.avg_gre == 315
    assert program.min_toefl == 80
    assert program.acceptance_rate == 0.40
    assert program.application_deadline == date(2027, 1, 15)


def test_programs_empty_optional_cells_become_none(tmp_path):
    path = write_csv(tmp_path, [valid_program_row(avg_gre="", min_toefl="")])

    [program] = load_programs(path)

    assert program.avg_gre is None
    assert program.min_toefl is None


def test_programs_several_rows_keep_file_order(tmp_path):
    rows = [valid_program_row(program_id="A"), valid_program_row(program_id="B", degree="PhD")]
    path = write_csv(tmp_path, rows)

    programs = load_programs(path)

    assert [p.program_id for p in programs] == ["A", "B"]
    assert programs[1].degree == "PhD"


def test_programs_header_only_gives_empty_list(tmp_path):
    path = write_csv(tmp_path, [], columns=list(valid_program_row().keys()))

    assert load_programs(path) == []


# ---- Invalid class: missing column ----
# Why: a missing column must fail once, at the header, not later on row 5,000.

def test_programs_missing_column_is_rejected(tmp_path):
    columns = [c for c in valid_program_row() if c != "acceptance_rate"]
    path = write_csv(tmp_path, [valid_program_row()], columns=columns)

    with pytest.raises(DataError, match="missing column.*acceptance_rate"):
        load_programs(path)


# ---- GPA: valid boundaries and invalid classes (below 0, above 4) ----
# Why (boundary values): 0.0 and 4.0 are the edges and must be accepted; just outside them must not.

@pytest.mark.parametrize("gpa", ["0.0", "4.0"])
def test_programs_gpa_boundaries_are_accepted(tmp_path, gpa):
    path = write_csv(tmp_path, [valid_program_row(avg_gpa=gpa)])

    assert load_programs(path)[0].avg_gpa == float(gpa)


@pytest.mark.parametrize("gpa", ["-0.1", "4.1"])
def test_programs_gpa_outside_0_to_4_is_rejected(tmp_path, gpa):
    path = write_csv(tmp_path, [valid_program_row(avg_gpa=gpa)])

    with pytest.raises(DataError, match="avg_gpa must be between 0.0 and 4.0"):
        load_programs(path)


# ---- Acceptance rate: valid boundaries and invalid classes ----
# Why (boundary values): a rate is a share from 0 to 1. "40" (meant as 40%) is a common typo and must be caught.

@pytest.mark.parametrize("rate", ["0.0", "1.0"])
def test_programs_acceptance_rate_boundaries_are_accepted(tmp_path, rate):
    path = write_csv(tmp_path, [valid_program_row(acceptance_rate=rate)])

    assert load_programs(path)[0].acceptance_rate == float(rate)


@pytest.mark.parametrize("rate", ["-0.01", "1.01", "40"])
def test_programs_acceptance_rate_outside_0_to_1_is_rejected(tmp_path, rate):
    path = write_csv(tmp_path, [valid_program_row(acceptance_rate=rate)])

    with pytest.raises(DataError, match="acceptance_rate must be between 0.0 and 1.0"):
        load_programs(path)


# ---- Invalid class: bad date ----
# Why: a wrong deadline is worse than none, so impossible dates (Feb 30, Feb 29 in 2027) are rejected.

@pytest.mark.parametrize("bad_date", [
    "01/15/2027",   # wrong format
    "2027-13-01",   # month 13
    "2027-02-30",   # day does not exist
    "2027-02-29",   # 2027 is not a leap year
    "soon",         # not a date at all
])
def test_programs_bad_date_is_rejected(tmp_path, bad_date):
    path = write_csv(tmp_path, [valid_program_row(application_deadline=bad_date)])

    with pytest.raises(DataError, match="application_deadline must be a real date"):
        load_programs(path)


def test_programs_leap_day_in_leap_year_is_accepted(tmp_path):
    path = write_csv(tmp_path, [valid_program_row(application_deadline="2028-02-29")])

    assert load_programs(path)[0].application_deadline == date(2028, 2, 29)


# ---- Invalid class: degree not MS/PhD ----
# Why: the search compares the exact text, so "ms" or "Masters" would silently match nothing. (BS is also valid now.)

@pytest.mark.parametrize("degree", ["MBA", "ms", "phd", "Masters"])
def test_programs_degree_not_ms_or_phd_is_rejected(tmp_path, degree):
    path = write_csv(tmp_path, [valid_program_row(degree=degree)])

    with pytest.raises(DataError, match="degree must be BS, MS or PhD"):
        load_programs(path)


# ---- Invalid classes: not a number, empty required cell ----
# Why: "free" in a tuition cell or an empty website must stop the load, and the message must show the file and line.

def test_programs_text_in_number_column_is_rejected(tmp_path):
    path = write_csv(tmp_path, [valid_program_row(tuition_in_state="free")])

    with pytest.raises(DataError, match="tuition_in_state must be a number, got 'free'"):
        load_programs(path)


def test_programs_decimal_in_whole_number_column_is_rejected(tmp_path):
    path = write_csv(tmp_path, [valid_program_row(min_toefl="80.5")])

    with pytest.raises(DataError, match="min_toefl must be a whole number"):
        load_programs(path)


def test_programs_empty_required_cell_is_rejected(tmp_path):
    path = write_csv(tmp_path, [valid_program_row(website="")])

    with pytest.raises(DataError, match="website is required"):
        load_programs(path)


def test_programs_error_message_names_file_and_line(tmp_path):
    # Line 1 = header, line 2 = good row, line 3 = bad row.
    rows = [valid_program_row(), valid_program_row(degree="MBA")]
    path = write_csv(tmp_path, rows)

    with pytest.raises(DataError, match=r"data\.csv, line 3:"):
        load_programs(path)


# =====================================================================
# load_scholarships
# Why: the ";" lists (degree levels, fields, ...) must split into tuples, and bad levels or GPAs must be rejected.
# =====================================================================

def test_scholarships_valid_row_splits_list_fields(tmp_path):
    path = write_csv(tmp_path, [valid_scholarship_row(special="first_gen;women_stem")])

    [scholarship] = load_scholarships(path)

    assert scholarship.amount == 10000.0
    assert scholarship.degree_levels == ("MS", "PhD")
    assert scholarship.fields == ("Any",)
    assert scholarship.citizenship == ("US", "PR")
    assert scholarship.special == ("first_gen", "women_stem")
    assert scholarship.min_gpa == 3.0
    assert scholarship.deadline == date(2026, 12, 1)


def test_scholarships_empty_special_means_no_requirement(tmp_path):
    path = write_csv(tmp_path, [valid_scholarship_row(special="")])

    assert load_scholarships(path)[0].special == ()


def test_scholarships_missing_column_is_rejected(tmp_path):
    columns = [c for c in valid_scholarship_row() if c != "deadline"]
    path = write_csv(tmp_path, [valid_scholarship_row()], columns=columns)

    with pytest.raises(DataError, match="missing column.*deadline"):
        load_scholarships(path)


@pytest.mark.parametrize("levels", ["MBA", "MS;MBA", ""])
def test_scholarships_bad_degree_levels_are_rejected(tmp_path, levels):
    path = write_csv(tmp_path, [valid_scholarship_row(degree_levels=levels)])

    with pytest.raises(DataError, match="degree"):
        load_scholarships(path)


@pytest.mark.parametrize("gpa", ["-1", "4.5"])
def test_scholarships_min_gpa_outside_0_to_4_is_rejected(tmp_path, gpa):
    path = write_csv(tmp_path, [valid_scholarship_row(min_gpa=gpa)])

    with pytest.raises(DataError, match="min_gpa must be between 0.0 and 4.0"):
        load_scholarships(path)


def test_scholarships_bad_deadline_is_rejected(tmp_path):
    path = write_csv(tmp_path, [valid_scholarship_row(deadline="2026-11-31")])

    with pytest.raises(DataError, match="deadline must be a real date"):
        load_scholarships(path)


# =====================================================================
# load_living_costs
# Why: every program's cost uses this file, so a missing column, a negative cost or text is rejected.
# =====================================================================

def test_living_costs_valid_rows_become_a_dict(tmp_path):
    rows = [{"state": "MI", "annual_living_cost": "18200"},
            {"state": "CA", "annual_living_cost": "27800"}]
    path = write_csv(tmp_path, rows)

    assert load_living_costs(path) == {"MI": 18200.0, "CA": 27800.0}


def test_living_costs_missing_column_is_rejected(tmp_path):
    path = write_csv(tmp_path, [{"state": "MI", "cost": "18200"}])

    with pytest.raises(DataError, match="missing column.*annual_living_cost"):
        load_living_costs(path)


def test_living_costs_negative_cost_is_rejected(tmp_path):
    path = write_csv(tmp_path, [{"state": "MI", "annual_living_cost": "-1"}])

    with pytest.raises(DataError, match="cannot be negative"):
        load_living_costs(path)


def test_living_costs_text_cost_is_rejected(tmp_path):
    path = write_csv(tmp_path, [{"state": "MI", "annual_living_cost": "cheap"}])

    with pytest.raises(DataError, match="must be a number"):
        load_living_costs(path)


# =====================================================================
# Tests added after mutation testing (see docs/mutation-testing.md)
# Why (mutation testing): the tool changed the code in small ways and some changes went unnoticed.
# Each test below catches one of those changes, for example a field silently dropped.
# =====================================================================

def test_programs_every_field_is_loaded(tmp_path):
    # Compares the whole object, so no field can be dropped or swapped unnoticed.
    path = write_csv(tmp_path, [valid_program_row(tuition_out_state="31000", duration_years="1.5",
                                                  stipend="1200", state="OH")])

    [program] = load_programs(path)

    assert program == Program(
        program_id="P1", university="Test University", program_name="MS in Computer Science",
        field="Computer Science", degree="MS", state="OH", tuition_in_state=15000.0,
        tuition_out_state=31000.0, duration_years=1.5, avg_gpa=3.40, avg_gre=315,
        acceptance_rate=0.40, stipend=1200.0, min_toefl=80,
        application_deadline=date(2027, 1, 15), website="https://example.edu/ms-cs")


def test_scholarships_every_field_is_loaded(tmp_path):
    path = write_csv(tmp_path, [valid_scholarship_row(states="MI;OH", special="first_gen")])

    [scholarship] = load_scholarships(path)

    assert scholarship == Scholarship(
        scholarship_id="S1", name="Test Fellowship", type="fellowship", amount=10000.0,
        degree_levels=("MS", "PhD"), fields=("Any",), min_gpa=3.0, citizenship=("US", "PR"),
        states=("MI", "OH"), special=("first_gen",), deadline=date(2026, 12, 1),
        website="https://example.org/fellowship")


def test_scholarships_empty_degree_levels_message(tmp_path):
    path = write_csv(tmp_path, [valid_scholarship_row(degree_levels="")])

    with pytest.raises(DataError, match="line 2: degree_levels is required$"):
        load_scholarships(path)


def test_missing_columns_are_listed_with_comma_and_space(tmp_path):
    columns = [c for c in valid_program_row() if c not in ("avg_gpa", "acceptance_rate")]
    path = write_csv(tmp_path, [valid_program_row()], columns=columns)

    with pytest.raises(DataError, match="missing column\\(s\\): avg_gpa, acceptance_rate$"):
        load_programs(path)


def test_living_cost_of_zero_is_accepted(tmp_path):
    # Boundary value: the rule rejects negative costs only.
    path = write_csv(tmp_path, [{"state": "MI", "annual_living_cost": "0"},
                                {"state": "OH", "annual_living_cost": "0.5"}])

    assert load_living_costs(path) == {"MI": 0.0, "OH": 0.5}


def test_line_break_inside_a_quoted_cell_is_kept_exactly(tmp_path):
    # The file is opened with newline="" as the csv module requires, so a
    # quoted cell keeps its own \r\n instead of having it changed to \n.
    path = write_csv(tmp_path, [valid_program_row(program_name="MS in\r\nComputer Science")])

    assert load_programs(path)[0].program_name == "MS in\r\nComputer Science"


# =====================================================================
# Values that are not published (CONTRIBUTING.md): blank -> None
# Why: government data leaves some cells empty. Blank must become None ("not published"), never 0,
# and blank vs 0 is tested as a boundary because a 0 stipend and an unknown stipend mean different things.
# =====================================================================

@pytest.mark.parametrize("column", ["avg_gpa", "acceptance_rate", "stipend",
                                    "application_deadline"])
@pytest.mark.parametrize("blank", ["", "   "])
def test_programs_blank_optional_value_becomes_none(tmp_path, column, blank):
    path = write_csv(tmp_path, [valid_program_row(**{column: blank})])

    assert getattr(load_programs(path)[0], column) is None


@pytest.mark.parametrize("column", ["avg_gpa", "acceptance_rate", "stipend"])
def test_programs_zero_is_a_value_not_blank(tmp_path, column):
    # Boundary between "not published" (blank) and a real value of 0.
    path = write_csv(tmp_path, [valid_program_row(**{column: "0"})])

    assert getattr(load_programs(path)[0], column) == 0.0


def test_programs_all_unpublished_values_blank_in_one_row(tmp_path):
    row = valid_program_row(avg_gpa="", avg_gre="", acceptance_rate="", stipend="", min_toefl="",
                            application_deadline="")

    [program] = load_programs(write_csv(tmp_path, [row]))

    assert (program.avg_gpa, program.avg_gre, program.acceptance_rate, program.stipend,
            program.min_toefl, program.application_deadline) == (None,) * 6


@pytest.mark.parametrize("column, value, message", [
    ("avg_gpa", "4.01", "avg_gpa must be between 0.0 and 4.0"),
    ("acceptance_rate", "1.5", "acceptance_rate must be between 0.0 and 1.0"),
    ("stipend", "some", "stipend must be a number, got 'some'"),
    ("application_deadline", "2027-02-29", "application_deadline must be a real date"),
])
def test_programs_present_optional_value_is_still_checked(tmp_path, column, value, message):
    path = write_csv(tmp_path, [valid_program_row(**{column: value})])

    with pytest.raises(DataError, match=message):
        load_programs(path)


@pytest.mark.parametrize("column", ["tuition_in_state", "tuition_out_state", "state", "field",
                                    "degree", "website", "duration_years"])
def test_programs_required_columns_still_cannot_be_blank(tmp_path, column):
    path = write_csv(tmp_path, [valid_program_row(**{column: ""})])

    with pytest.raises(DataError, match=f"{column} is required|degree must be MS or PhD"):
        load_programs(path)


# ---- The optional `source` column ----
# Why: only three sources exist; a typo like "IPEDS" must be rejected with the file and line.

def test_programs_without_source_column_are_estimates(tmp_path):
    path = write_csv(tmp_path, [valid_program_row()])      # no source column at all

    assert load_programs(path)[0].source == "estimate"


@pytest.mark.parametrize("value, expected", [
    ("", "estimate"),
    ("estimate", "estimate"),
    ("official-page", "official-page"),
    ("ipeds", "ipeds"),
    (" ipeds ", "ipeds"),
])
def test_programs_source_values(tmp_path, value, expected):
    path = write_csv(tmp_path, [valid_program_row(source=value)])

    assert load_programs(path)[0].source == expected


@pytest.mark.parametrize("value", ["official", "IPEDS", "guess", "official page"])
def test_programs_bad_source_is_rejected_with_file_and_line(tmp_path, value):
    rows = [valid_program_row(source="ipeds"), valid_program_row(source=value)]
    path = write_csv(tmp_path, rows)

    with pytest.raises(DataError, match=rf"data\.csv, line 3: source must be estimate, "
                                        rf"official-page or ipeds, got '{value}'$"):
        load_programs(path)


# ---- Test-score percentiles (sat_25, sat_75, act_25, act_75): optional columns ----
# Why: score ranges drive the Safety/Match/Reach label for colleges, so both ends, their limits and their order are checked.

def test_programs_without_test_score_columns_have_none(tmp_path):
    [program] = load_programs(write_csv(tmp_path, [valid_program_row()]))
    assert (program.sat_25, program.sat_75, program.act_25, program.act_75) == (None, None, None, None)


def test_programs_test_score_percentiles_are_loaded(tmp_path):
    row = valid_program_row(sat_25="1110", sat_75="1350", act_25="24", act_75="31")
    [program] = load_programs(write_csv(tmp_path, [row]))
    assert (program.sat_25, program.sat_75, program.act_25, program.act_75) == (1110, 1350, 24, 31)


def test_programs_blank_test_score_cells_are_none(tmp_path):
    row = valid_program_row(sat_25="", sat_75="", act_25="", act_75="")
    [program] = load_programs(write_csv(tmp_path, [row]))
    assert program.sat_25 is None and program.act_75 is None


@pytest.mark.parametrize("sat_25, sat_75", [("400", "400"), ("1600", "1600"), ("400", "1600")])
def test_programs_sat_boundaries_are_accepted(tmp_path, sat_25, sat_75):
    [program] = load_programs(write_csv(tmp_path, [valid_program_row(sat_25=sat_25, sat_75=sat_75)]))
    assert program.sat_25 == int(sat_25)


@pytest.mark.parametrize("changes, message", [
    (dict(sat_25="399", sat_75="1200"), "sat_25 must be between"),
    (dict(sat_25="1000", sat_75="1601"), "sat_75 must be between"),
    (dict(act_25="0", act_75="30"), "act_25 must be between"),
    (dict(act_25="20", act_75="37"), "act_75 must be between"),
    (dict(sat_25="1300", sat_75="1200"), "sat_25 cannot be above sat_75"),
    (dict(act_25="30", act_75="20"), "act_25 cannot be above act_75"),
    (dict(sat_25="1000", sat_75=""), "must both be filled in or both left blank"),
    (dict(act_25="", act_75="30"), "must both be filled in or both left blank"),
    (dict(sat_25="high", sat_75="1200"), "sat_25 must be a whole number"),
])
def test_programs_bad_test_scores_are_rejected(tmp_path, changes, message):
    with pytest.raises(DataError, match=message):
        load_programs(write_csv(tmp_path, [valid_program_row(**changes)]))


# ---- Exact messages for the test-score percentiles (added after mutation testing) ----
# Why (mutation testing): these check the whole message, so swapping the two column names in it is caught.

def test_programs_one_sided_sat_range_message_names_both_columns(tmp_path):
    path = write_csv(tmp_path, [valid_program_row(sat_25="", sat_75="1300")])

    with pytest.raises(DataError, match="line 2: sat_25 and sat_75 must both be filled in or both left blank$"):
        load_programs(path)


def test_programs_reversed_act_range_message_gives_both_values(tmp_path):
    path = write_csv(tmp_path, [valid_program_row(act_25="30", act_75="24")])

    with pytest.raises(DataError, match="line 2: act_25 cannot be above act_75, got 30 and 24$"):
        load_programs(path)
