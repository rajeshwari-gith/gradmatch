from datetime import date
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from gradmatch import search
from gradmatch.cost import yearly_cost
from helpers import APP, make_program, make_student, open_app, search as search_page, table


def test_spy_on_cost():
    # a spy keeps the real function but counts the calls
    spy = Mock(wraps=yearly_cost)
    with patch.object(search, "yearly_cost", spy):
        search.find_programs([make_program(), make_program(degree="PhD"), make_program()],
                             make_student())
    assert spy.call_count == 2


def test_mock_database_programs():
    programs = Mock(return_value=[make_program(university="Mock University")])
    with patch("gradmatch.database.get_programs", programs):
        at = search_page(open_app())
    programs.assert_called()
    assert list(table(at, "Programs")["University"]) == ["Mock University"]


def test_mock_today_for_a_program_deadline():
    programs = Mock(return_value=[make_program(deadline=date(2026, 11, 25))])
    with patch("gradmatch.database.get_programs", programs):
        at = search_page(open_app(), today=date(2026, 11, 20))
    assert "Test University (MS in Computer Science) is due in 5 days" in at.warning[0].value


def test_mock_empty_scholarships():
    with patch("gradmatch.database.get_scholarships", Mock(return_value=[])):
        at = search_page(open_app())
    assert "No scholarships match your degree, field and GPA." in [i.value for i in at.info]


def test_mock_empty_database():
    with patch("gradmatch.database.get_programs", Mock(return_value=[])):
        at = AppTest.from_file(APP, default_timeout=30).run()
    assert at.error[0].value == "No programs found in the database."
    assert len(at.button) == 0
