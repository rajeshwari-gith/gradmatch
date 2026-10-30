from datetime import date
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from helpers import APP, make_program, open_app, search, table


def test_app_with_mocked_database_and_date():
    programs = Mock(return_value=[make_program(university="Mock University",
                                               deadline=date(2026, 11, 25))])
    with patch("database.get_programs", programs), \
         patch("database.get_scholarships", Mock(return_value=[])):
        at = search(open_app(), today=date(2026, 11, 20))
    assert list(table(at, "Programs")["University"]) == ["Mock University"]
    assert "No scholarships match your degree, field and GPA." in [i.value for i in at.info]
    assert "is due in 5 days" in at.warning[0].value

    with patch("database.get_programs", Mock(return_value=[])):
        at = AppTest.from_file(APP, default_timeout=30).run()
    assert at.error[0].value == "No programs found in the database."
