"""System tests for what the app shows when the data files are broken.

Equivalence partitioning on the kinds of data problem: a missing folder
(a file cannot be read) and a bad row (the loader rejects it with a line
number).
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from .conftest import LIVING_COSTS, PROGRAM_HEADER, PROGRAM_ROWS, SCHOLARSHIP_HEADER

pytestmark = pytest.mark.system

APP = str(Path(__file__).resolve().parents[2] / "app" / "streamlit_app.py")


def run_app(monkeypatch, folder):
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(folder))
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception
    return at


def test_missing_data_folder_shows_a_clear_message_and_no_form(monkeypatch, tmp_path):
    at = run_app(monkeypatch, tmp_path / "does_not_exist")
    assert "The program data could not be loaded" in at.error[0].value
    assert not at.button                      # the form is not shown


def test_bad_row_names_the_file_and_line(monkeypatch, tmp_path):
    bad_row = PROGRAM_ROWS[0].replace(",3.30,", ",9.99,")      # average GPA 9.99 is out of range
    (tmp_path / "programs.csv").write_text(PROGRAM_HEADER + bad_row + "\n")
    (tmp_path / "living_costs.csv").write_text(LIVING_COSTS)
    (tmp_path / "scholarships.csv").write_text(SCHOLARSHIP_HEADER)
    at = run_app(monkeypatch, tmp_path)
    message = at.error[0].value
    assert "could not be loaded" in message
    assert "programs.csv" in message and "line 2" in message


def test_good_data_shows_the_form(monkeypatch, data_dir):
    at = run_app(monkeypatch, data_dir)
    assert not at.error
    assert at.button[0].label == "Find programs"
