"""Fixtures for the acceptance tests: the real app on the small fixed data in
tests/data_fixtures.py, with "today" fixed at 2026-10-24."""
import pytest

from data_fixtures import TODAY, write_fixture_data


@pytest.fixture(scope="session")
def data_dir(tmp_path_factory):
    return write_fixture_data(tmp_path_factory.mktemp("acceptance_test_data"))


@pytest.fixture(autouse=True)
def fixed_app_environment(monkeypatch, data_dir):
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(data_dir))
    monkeypatch.setenv("GRADMATCH_TODAY", TODAY)
