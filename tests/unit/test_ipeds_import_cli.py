"""More unit tests for ipeds_import.py, added after mutation testing.

They cover the command line (required files, default folders, help text,
printed messages) and value rules the first tests did not pin down: a
missing rate before a known one, an acceptance rate of exactly 100%,
rounding, every test-score column, extra columns kept by a merge, and the
tuition report. See docs/mutation-testing.md. The helpers come from
test_ipeds_import.py; nothing here reads the real government files.
"""

import csv

import pytest

import gradmatch.ipeds_import as ipeds_import
from gradmatch.ipeds_import import (admissions, build_rows, main, merge_programs, read_csv,
                                    tuition_check, tuition_rates)
from test_ipeds_import import (AWARDS, SCHOOLS, TUITION, admission, cost, existing_row,
                               folder, run, write)  # noqa: F401  (folder is a fixture)

pytestmark = pytest.mark.unit


# argparse wraps the help text to the terminal width, so we compare words, not exact line breaks.
def words(text: str) -> str:
    """Collapse whitespace, because argparse re-wraps the help text."""
    return " ".join(text.split())


# ---- value rules ----
# Why (mutation testing + boundary values): an acceptance rate of exactly 100%, rounding, every score column,
# extra columns kept by a merge and the tuition report each had a code change no test noticed.

def test_a_school_without_a_rate_does_not_stop_the_others():
    rates = tuition_rates([cost(unit="1", t6=""), cost(unit="2")], "MS")
    assert list(rates) == ["2"]


def test_an_acceptance_rate_of_exactly_100_percent_is_kept():
    # Boundary: admitted == applicants is allowed (admitted <= applicants).
    assert admissions([admission(applicants="400", admitted="400")])["1"]["acceptance_rate"] == 1.0


def test_the_acceptance_rate_is_rounded_to_three_decimals():
    assert admissions([admission(applicants="3", admitted="1")])["1"]["acceptance_rate"] == 0.333


def test_bachelors_rows_get_every_test_score_column():
    rows = {r["degree"]: r for r in build_rows(SCHOOLS, TUITION, AWARDS, [], admissions([admission()]))}
    bs = rows["BS"]
    assert (bs["sat_25"], bs["sat_75"], bs["act_25"], bs["act_75"]) == (1110, 1350, 24, 31)


def test_rows_without_test_scores_have_empty_score_cells():
    rows = {r["degree"]: r for r in build_rows(SCHOOLS, TUITION, AWARDS, [], {})}
    for degree in ("BS", "MS", "PhD"):
        assert [rows[degree][c] for c in ("sat_25", "sat_75", "act_25", "act_75")] == [""] * 4


def test_read_csv_keeps_a_line_break_inside_a_quoted_cell(tmp_path):
    path = write(tmp_path / "hd.csv", ["UNITID", "INSTNM", "STABBR", "WEBADDR", "ADMINURL"],
                 [["1", "Line one\r\nLine two", "MI", "a.edu", "a.edu/apply"]])
    assert read_csv(path, "directory")[0]["INSTNM"] == "Line one\r\nLine two"


def test_merge_keeps_extra_columns_and_line_breaks_in_old_rows(tmp_path):
    path = tmp_path / "programs.csv"
    write(path, ["program_id", "notes", "university"], [["OLD", "first\r\nsecond", "Old U"]], "utf-8")

    merge_programs(path, [{"program_id": "NEW", "university": "New U"}])

    with open(path, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert list(rows[0])[:3] == ["program_id", "notes", "university"]   # old order first
    assert rows[0]["notes"] == "first\r\nsecond"
    assert rows[1]["notes"] == "" and rows[1]["program_id"] == "NEW"


def test_tuition_check_matches_a_common_name_to_the_official_name():
    schools = {"9": {"name": "Purdue University-Main Campus", "state": "IN", "website": "https://p.edu"}}
    [row] = tuition_check(schools, {"9": (10000.0, 20000.0)},
                          [existing_row(university="Purdue University", tuition_in_state="16000")])
    assert row["official_in"] == 10000
    assert row["in_state_difference"] == 60          # (16000 - 10000) / 10000 * 100


def test_tuition_check_zero_in_state_rate_with_a_known_out_of_state_rate():
    # Only the in-state rate decides whether the difference can be worked out.
    [row] = tuition_check(SCHOOLS, {"1": (0.0, 5000.0)}, [existing_row()])
    assert row["in_state_difference"] is None


# ---- the command line ----
# Why: people run the importer from the terminal, so required files, default folders, the printed
# messages and the --help text are part of what it does.

@pytest.mark.parametrize("left_out", ["--hd", "--cost", "--completions"])
def test_command_needs_all_three_official_files(folder, left_out, capsys):
    args = {"--hd": folder / "hd.csv", "--cost": folder / "cost.csv",
            "--completions": folder / "c.csv"}
    del args[left_out]
    argv = [part for name, path in args.items() for part in (name, str(path))] + ["--data", str(folder)]

    with pytest.raises(SystemExit) as stop:
        main(argv)
    assert stop.value.code == 2
    assert f"the following arguments are required: {left_out}" in capsys.readouterr().err


def test_command_default_data_folder_and_output(folder, tmp_path, monkeypatch, capsys):
    # Run from a folder whose data/ subfolder holds programs.csv and living_costs.csv.
    work = tmp_path / "work"
    (work / "data").mkdir(parents=True)
    for name in ("programs.csv", "living_costs.csv"):
        (work / "data" / name).write_bytes((folder / name).read_bytes())
    monkeypatch.chdir(work)

    assert main(["--hd", str(folder / "hd.csv"), "--cost", str(folder / "cost.csv"),
                 "--completions", str(folder / "c.csv")]) == 0

    assert (work / "data" / "programs_ipeds.csv").exists()
    assert "written to data/programs_ipeds.csv" in capsys.readouterr().out


def test_command_merge_message_names_the_programs_file(folder, capsys):
    run(folder, "--merge")
    assert f"1 row(s) added to {folder / 'programs.csv'}\n" in capsys.readouterr().out


def test_command_help_text(capsys):
    with pytest.raises(SystemExit) as stop:
        main(["--help"])
    assert stop.value.code == 0
    text = words(capsys.readouterr().out)

    assert "XX" not in text                       # each help text appears exactly, with nothing added
    first, second = ipeds_import.__doc__.split("\n\n")[:2]
    assert words(first) in text                   # the description is the first paragraph only
    assert words(second) not in text
    for help_text in ["HD<year> directory CSV", "COST1_<year> CSV", "C<year>_A CSV",
                      "folder with programs.csv and living_costs.csv",
                      "optional ADM<year> CSV (bachelor's acceptance rate and SAT/ACT)",
                      "also add the new rows to programs.csv in the data folder",
                      "optional CSV: our tuition vs the official rates"]:
        assert help_text in text, help_text
