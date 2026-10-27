"""Fixtures for the system tests: the app runs on the small fixed data in
tests/data_fixtures.py (see the tables there) with "today" fixed."""
import pytest

from data_fixtures import TODAY, write_fixture_data


@pytest.fixture(scope="session")
def data_dir(tmp_path_factory):
    return write_fixture_data(tmp_path_factory.mktemp("system_test_data"))


# autouse=True: this runs before EVERY test in the folder, pointing the app at the fixed test data
# and the fixed date, so no test can accidentally read the real data.
@pytest.fixture(autouse=True)
def fixed_app_environment(monkeypatch, data_dir):
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(data_dir))
    monkeypatch.setenv("GRADMATCH_TODAY", TODAY)
