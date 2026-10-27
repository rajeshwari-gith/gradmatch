"""System test: programs from official data leave GPA, acceptance rate, stipend and
deadline blank. The page must still show them, labelled as not published.

The data loader is replaced here by a fixed list, so this test does not depend on
how the CSV files store blanks.
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from conftest import make_program
from gradmatch import data_loader

pytestmark = pytest.mark.system

APP = str(Path(__file__).resolve().parents[2] / "app" / "streamlit_app.py")


def test_the_page_shows_programs_with_unpublished_values(monkeypatch, tmp_path_factory):
    from data_fixtures import write_fixture_data
    folder = write_fixture_data(tmp_path_factory.mktemp("unpublished"))
    program = make_program(avg_gpa=None, acceptance_rate=None, stipend=None,
                           application_deadline=None, source="ipeds")
    monkeypatch.setattr(data_loader, "load_programs", lambda path: [program])
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(folder))

    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    at.button[0].click().run()

    assert not at.exception
    html = " ".join(m.value for m in at.markdown if 'class="gm-card"' in m.value)
    assert "Unknown" in html and "Funding unknown" in html
    assert "Deadline: check program page" in html and "n/a" in html
    assert any("nothing to chart" in i.value for i in at.info)
