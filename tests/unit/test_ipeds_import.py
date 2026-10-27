"""Unit tests for ipeds_import.py.

Techniques: equivalence partitioning on each cell kind (blank, text, negative,
valid), boundary-value analysis on the minimum number of degrees awarded, and
an end-to-end run on tiny made-up files (never the real government files).
"""
import csv

import pytest

from gradmatch.ipeds_import import (DEFAULT_MIN_AWARDS, ImportDataError, awarded_programs,
                                    build_rows, existing_keys, tuition_rates, institutions, main,
                                    money, normalize, read_csv, tuition_check, website_of)

pytestmark = pytest.mark.unit

STATES = {"MI", "OH"}


def write(path, header, rows, encoding="utf-8-sig"):
    with open(path, "w", newline="", encoding=encoding) as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)
    return path


def directory(unit="1", name="Test University", state="MI", web="www.test.edu"):
    return {"UNITID": unit, "INSTNM": name, "STABBR": state, "WEBADDR": web}


def cost(unit="1", t6="10000", t7="20000", f6="500", f7="700", t2="6000", t3="15000", f2="300", f3="400"):
    return {"UNITID": unit, "TUITION6": t6, "TUITION7": t7, "FEE6": f6, "FEE7": f7,
            "TUITION2": t2, "TUITION3": t3, "FEE2": f2, "FEE3": f3}


def completion(unit="1", cip="11.0701", level="7", total="10"):
    return {"UNITID": unit, "CIPCODE": cip, "AWLEVEL": level, "CTOTALT": total}


# ---- reading a file ----

def test_read_csv_handles_a_byte_order_mark_and_trims_cells(tmp_path):
    path = write(tmp_path / "hd.csv", ["UNITID", "INSTNM", "STABBR", "WEBADDR"],
                 [[" 1 ", "A", "MI", "a.edu"]])
    assert read_csv(path, "directory") == [{"UNITID": "1", "INSTNM": "A", "STABBR": "MI",
                                            "WEBADDR": "a.edu"}]


def test_read_csv_names_the_missing_columns(tmp_path):
    path = write(tmp_path / "cost.csv", ["UNITID", "TUITION6"], [["1", "5"]])
    with pytest.raises(ImportDataError, match="TUITION7, FEE6, FEE7"):
        read_csv(path, "cost")


def test_read_csv_turns_blank_cells_into_empty_text(tmp_path):
    path = write(tmp_path / "c.csv", ["UNITID", "CIPCODE", "AWLEVEL", "CTOTALT"], [["1", "11.0701", "7"]])
    assert read_csv(path, "completions")[0]["CTOTALT"] == ""


# ---- small helpers ----

@pytest.mark.parametrize("a, b", [("University of California-Berkeley", "university of california berkeley"),
                                  ("  Ohio   State! ", "OHIO STATE")])
def test_normalize_ignores_case_and_punctuation(a, b):
    assert normalize(a) == normalize(b)


@pytest.mark.parametrize("address, expected", [
    ("www.a.edu", "https://www.a.edu"), ("https://a.edu", "https://a.edu"),
    ("HTTP://a.edu", "HTTP://a.edu"), ("  ", ""), ("", "")])
def test_website_of(address, expected):
    assert website_of(address) == expected


@pytest.mark.parametrize("text, expected", [("0", 0.0), ("100.5", 100.5), ("-1", None), ("", None), ("n/a", None)])
def test_money(text, expected):
    assert money(text) == expected


# ---- institutions ----

def test_institutions_keeps_schools_in_states_with_a_living_cost_and_a_website():
    rows = [directory("1"), directory("2", state="PR"), directory("3", web=""), directory("4", name="")]
    assert institutions(rows, STATES) == {"1": {"name": "Test University", "state": "MI",
                                                "website": "https://www.test.edu"}}


# ---- tuition ----

def test_tuition_adds_required_fees():
    assert tuition_rates([cost()], "MS") == {"1": (10500.0, 20700.0)}


def test_phd_uses_the_graduate_rate_and_bachelors_the_undergraduate_rate():
    assert tuition_rates([cost()], "PhD") == {"1": (10500.0, 20700.0)}
    assert tuition_rates([cost()], "BS") == {"1": (6300.0, 15400.0)}


def test_a_blank_fee_counts_as_zero():
    assert tuition_rates([cost(f6="", f7="")], "MS") == {"1": (10000.0, 20000.0)}


@pytest.mark.parametrize("t6, t7", [("", "20000"), ("10000", ""), ("-5", "20000"), ("x", "y")])
def test_a_school_without_a_graduate_rate_is_skipped(t6, t7):
    assert tuition_rates([cost(t6=t6, t7=t7)], "MS") == {}


# ---- degrees awarded: boundary at the minimum ----

@pytest.mark.parametrize("total, kept", [(DEFAULT_MIN_AWARDS - 1, False), (DEFAULT_MIN_AWARDS, True),
                                         (DEFAULT_MIN_AWARDS + 1, True)])
def test_minimum_number_of_degrees(total, kept):
    result = awarded_programs([completion(total=str(total))], DEFAULT_MIN_AWARDS)
    assert (("1", "MS", "Computer Science") in result) is kept


@pytest.mark.parametrize("cip, level, key", [
    ("11.0701", "7", ("1", "MS", "Computer Science")),
    ("11.0701", "17", ("1", "PhD", "Computer Science")),
    ("11.0701", "5", ("1", "BS", "Computer Science")),
    ("30.7001", "7", ("1", "MS", "Data Science")),
    ("30.7001", "17", ("1", "PhD", "Data Science"))])
def test_fields_and_levels_we_cover(cip, level, key):
    assert key in awarded_programs([completion(cip=cip, level=level)], 1)


@pytest.mark.parametrize("cip, level, total", [("11.0701", "6", "10"), ("52.0201", "7", "10"),
                                               ("11.0701", "7", "0"), ("11.0701", "7", "")])
def test_other_fields_levels_or_empty_counts_are_ignored(cip, level, total):
    assert awarded_programs([completion(cip=cip, level=level, total=total)], 1) == {}


def test_counts_for_the_same_program_are_added_up():
    rows = [completion(total="3"), completion(total="4")]
    assert awarded_programs(rows, 1) == {("1", "MS", "Computer Science"): 7}


# ---- building rows ----

SCHOOLS = {"1": {"name": "Test University", "state": "MI", "website": "https://www.test.edu"}}
TUITION = {"BS": {"1": (6300.0, 15400.0)}, "MS": {"1": (10500.0, 20700.0)},
           "PhD": {"1": (10500.0, 20700.0)}}
AWARDS = {("1", "MS", "Computer Science"): 10, ("1", "PhD", "Data Science"): 6,
          ("1", "BS", "Computer Science"): 50}


def test_a_new_row_has_official_values_and_blanks_for_unpublished_ones():
    [bs, ms, phd] = build_rows(SCHOOLS, TUITION, AWARDS, [])
    assert (bs["program_id"], bs["duration_years"], bs["stipend"]) == ("IPEDS-1-BS-CS", 4.0, "0")
    assert (bs["tuition_in_state"], bs["tuition_out_state"]) == (6300, 15400)
    assert ms["program_id"] == "IPEDS-1-MS-CS" and phd["program_id"] == "IPEDS-1-PHD-DS"
    assert ms["program_name"] == "MS in Computer Science"
    assert (ms["tuition_in_state"], ms["tuition_out_state"]) == (10500, 20700)
    assert (ms["duration_years"], phd["duration_years"]) == (2.0, 5.0)
    assert ms["source"] == "ipeds" and ms["state"] == "MI" and ms["website"] == "https://www.test.edu"
    for blank in ("avg_gpa", "avg_gre", "acceptance_rate", "stipend", "min_toefl", "application_deadline"):
        assert ms[blank] == ""


def test_a_program_we_already_have_is_not_added_again():
    existing = [{"university": "Test University", "degree": "MS", "field": "Computer Science"}]
    assert [r["program_id"] for r in build_rows(SCHOOLS, TUITION, AWARDS, existing)] == [
        "IPEDS-1-BS-CS", "IPEDS-1-PHD-DS"]


def test_an_existing_row_with_a_common_name_is_matched_to_the_official_name():
    schools = {"1": {"name": "Purdue University-Main Campus", "state": "IN", "website": "https://p.edu"}}
    existing = [{"university": "Purdue University", "degree": "MS", "field": "Computer Science"}]
    assert build_rows(schools, TUITION, {("1", "MS", "Computer Science"): 9}, existing) == []


@pytest.mark.parametrize("schools, tuition", [({}, TUITION), (SCHOOLS, {"BS": {}, "MS": {}, "PhD": {}})])
def test_a_school_without_directory_or_tuition_data_is_skipped(schools, tuition):
    assert build_rows(schools, tuition, AWARDS, []) == []


def test_existing_keys_use_the_official_name():
    keys = existing_keys([{"university": "Indiana University Bloomington", "degree": "MS",
                           "field": "Data Science"}])
    assert keys == {("indiana university bloomington", "MS", "Data Science")}


# ---- tuition check ----

def existing_row(**changes):
    row = {"program_id": "X", "university": "Test University", "tuition_in_state": "12000",
           "tuition_out_state": "24000"}
    row.update(changes)
    return row


def test_tuition_check_compares_our_numbers_with_the_official_ones():
    assert tuition_check(SCHOOLS, TUITION["MS"], [existing_row()]) == [{
        "program_id": "X", "ours_in": 12000.0, "ours_out": 24000.0, "official_in": 10500,
        "official_out": 20700, "in_state_difference": 14}]


def test_tuition_check_skips_unknown_schools_and_handles_a_zero_rate():
    assert tuition_check(SCHOOLS, TUITION["MS"], [existing_row(university="Nowhere College")]) == []
    [row] = tuition_check(SCHOOLS, {"1": (0.0, 0.0)}, [existing_row()])
    assert row["in_state_difference"] is None


# ---- the whole command ----

@pytest.fixture
def folder(tmp_path):
    write(tmp_path / "living_costs.csv", ["state", "annual_living_cost"], [["MI", "12000"]], "utf-8")
    write(tmp_path / "programs.csv", ["program_id", "university", "program_name", "field", "degree",
                                      "tuition_in_state", "tuition_out_state"],
          [["P1", "Test University", "MS in Computer Science", "Computer Science", "MS", "12000", "24000"]], "utf-8")
    write(tmp_path / "hd.csv", ["UNITID", "INSTNM", "STABBR", "WEBADDR"],
          [["1", "Test University", "MI", "test.edu"], ["2", "Other College", "MI", "other.edu"]])
    write(tmp_path / "cost.csv", ["UNITID", "TUITION6", "TUITION7", "FEE6", "FEE7", "TUITION2", "TUITION3",
                                  "FEE2", "FEE3"],
          [["1", "10000", "20000", "500", "700", "5000", "9000", "0", "0"],
           ["2", "8000", "16000", "0", "0", "4000", "8000", "0", "0"]])
    write(tmp_path / "c.csv", ["UNITID", "CIPCODE", "AWLEVEL", "CTOTALT"],
          [["1", "11.0701", "7", "20"], ["2", "11.0701", "7", "20"], ["2", "30.7001", "7", "2"]])
    return tmp_path


def run(folder, *extra):
    return main(["--hd", str(folder / "hd.csv"), "--cost", str(folder / "cost.csv"),
                 "--completions", str(folder / "c.csv"), "--data", str(folder),
                 "--output", str(folder / "out.csv"), *extra])


def test_command_writes_only_the_new_programs(folder, capsys):
    assert run(folder) == 0
    with open(folder / "out.csv", newline="") as file:
        rows = list(csv.DictReader(file))
    assert [r["program_id"] for r in rows] == ["IPEDS-2-MS-CS"]
    assert "1 new program row(s)" in capsys.readouterr().out


def test_command_can_write_the_tuition_report(folder, capsys):
    run(folder, "--report", str(folder / "report.csv"))
    with open(folder / "report.csv", newline="") as file:
        assert [r["program_id"] for r in csv.DictReader(file)] == ["P1"]
    assert "tuition check for 1 existing row(s)" in capsys.readouterr().out


def test_command_report_is_still_written_when_nothing_matches(folder):
    write(folder / "programs.csv", ["program_id", "university", "program_name", "field", "degree",
                                    "tuition_in_state", "tuition_out_state"], [], "utf-8")
    run(folder, "--report", str(folder / "report.csv"))
    assert (folder / "report.csv").read_text().strip() == "program_id"


def test_command_minimum_can_be_lowered(folder):
    run(folder, "--min-awards", "1")
    with open(folder / "out.csv", newline="") as file:
        assert {r["program_id"] for r in csv.DictReader(file)} == {"IPEDS-2-MS-CS", "IPEDS-2-MS-DS"}


def test_command_adds_bachelors_programs(folder):
    rows = list(csv.reader(open(folder / "c.csv", encoding="utf-8-sig")))
    rows.append(["2", "11.0701", "5", "30"])
    write(folder / "c.csv", rows[0], rows[1:])
    run(folder)
    with open(folder / "out.csv", newline="") as file:
        row = next(r for r in csv.DictReader(file) if r["degree"] == "BS")
    assert (row["tuition_in_state"], row["tuition_out_state"], row["duration_years"]) == ("4000", "8000", "4.0")
