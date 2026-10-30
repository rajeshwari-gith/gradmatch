"""Week 4 - Test doubles: stubs, fakes, mocks and spies.

A test double stands in for a real part of the program, so a test can control it or watch it.
"""
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from gradmatch import search
from gradmatch.cost import yearly_cost
from gradmatch.data_loader import DataError, load_programs
from helpers import APP, DATA, GOOD_ROW, make_program, make_student, write_csv


def test_stub_programs_instead_of_the_real_file():
    # Stub: a hand-made list replaces the CSV file, so we know exactly what the search gets.
    stub = [make_program(university="A"), make_program(university="B", field="Data Science")]
    results = search.find_programs(stub, make_student())
    assert [r.program.university for r in results] == ["A"]


def test_fake_file_in_a_temporary_folder(tmp_path):
    # Fake: a small working CSV file in a temp folder replaces the real data file.
    programs = load_programs(write_csv(tmp_path, GOOD_ROW))
    assert programs[0].university == "Test University"


def test_spy_counts_how_often_the_cost_is_worked_out(monkeypatch):
    # Spy: wraps the real yearly_cost so it still works, but records every call.
    spy = Mock(wraps=yearly_cost)
    monkeypatch.setattr(search, "yearly_cost", spy)
    programs = [make_program(), make_program(field="Data Science"), make_program()]
    search.find_programs(programs, make_student())
    # The cost is only needed for the 2 programs in the student's field.
    assert spy.call_count == 2


def test_mock_loader_gives_the_app_our_own_programs():
    # Mock: the app gets a fake loader, and we check the app really called it.
    fake_loader = Mock(return_value=[make_program(university="Mock University")])
    with patch("gradmatch.data_loader.load_programs", fake_loader):
        at = AppTest.from_file(APP, default_timeout=30).run()
        at.button[0].click().run()
    # The app reads the data each time the page runs: once on opening, once after the click.
    assert fake_loader.call_count == 2
    fake_loader.assert_called_with(DATA)
    table = at.dataframe[0].value
    assert list(table["University"]) == ["Mock University"]


def test_mock_loader_that_fails_shows_an_error_message():
    # The mock raises an error, so we can test the error path without breaking the real file.
    broken_loader = Mock(side_effect=DataError("line 3: bad number"))
    with patch("gradmatch.data_loader.load_programs", broken_loader):
        at = AppTest.from_file(APP, default_timeout=30).run()
    assert "line 3: bad number" in at.error[0].value
    assert len(at.button) == 0  # the form is not shown
