"""Unit tests for data_loader.py.

Technique: equivalence partitioning. For each loader the input is split
into one valid class and several invalid classes (missing column, value
out of range, bad date, bad degree, not a number, empty required cell),
with at least one test per class. Range limits (GPA 0-4, rate 0-1) also
get boundary-value tests.

Tests never read the real CSVs in data/. Each test writes a tiny CSV into
pytest's tmp_path folder.
"""
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
# =====================================================================

# ---- Valid class ----

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

def test_programs_missing_column_is_rejected(tmp_path):
    columns = [c for c in valid_program_row() if c != "acceptance_rate"]
    path = write_csv(tmp_path, [valid_program_row()], columns=columns)

    with pytest.raises(DataError, match="missing column.*acceptance_rate"):
        load_programs(path)


# ---- GPA: valid boundaries and invalid classes (below 0, above 4) ----

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

@pytest.mark.parametrize("degree", ["MBA", "ms", "phd", "Masters"])
def test_programs_degree_not_ms_or_phd_is_rejected(tmp_path, degree):
    path = write_csv(tmp_path, [valid_program_row(degree=degree)])

    with pytest.raises(DataError, match="degree must be BS, MS or PhD"):
        load_programs(path)


# ---- Invalid classes: not a number, empty required cell ----

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
