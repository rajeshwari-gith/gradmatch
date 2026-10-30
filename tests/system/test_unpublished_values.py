"""System test: programs from official data leave GPA, acceptance rate, stipend and
deadline blank. The page must still show them, labelled as not published.

The data loader is replaced here by a fixed list, so this test does not depend on
how the CSV files store blanks.
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from conftest import make_program
from app_pages import DEADLINES, chances, deadline_rows, go
from gradmatch import data_loader

pytestmark = pytest.mark.system

# In plain words: a program from government data has blanks (no GPA, stipend or deadline). The app
# must still show it, with a chance estimated from its acceptance rate, instead of crashing.

APP = str(Path(__file__).resolve().parents[2] / "app" / "streamlit_app.py")


def test_the_page_shows_programs_with_unpublished_values(monkeypatch, tmp_path_factory):
    from data_fixtures import write_fixture_data
    folder = write_fixture_data(tmp_path_factory.mktemp("unpublished"))
    program = make_program(avg_gpa=None, stipend=None, application_deadline=None, source="ipeds")
    monkeypatch.setattr(data_loader, "load_programs", lambda path: [program])
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(folder))

    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    at.button[0].click().run()

    assert not at.exception
    assert chances(at) == ["Match"]           # estimated: 40% accepted, GPA 3.5
    assert any("nothing to chart" in i.value for i in at.info)
    go(at, DEADLINES)                       # no published deadline: the program is not listed, no crash
    assert not any("Test University" in row for row in deadline_rows(at))
