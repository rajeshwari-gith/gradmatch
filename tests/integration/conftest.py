"""Shared fixtures for the integration tests that use the real data files."""

from pathlib import Path

import pytest

import gradmatch.api as api
from gradmatch.data_loader import load_living_costs, load_programs, load_scholarships

REAL_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


# scope="session": pytest runs these once per test run and hands the same result to every test.
# The model objects are frozen (read-only), so one test cannot change them for the next.
@pytest.fixture(scope="session")
def real_programs():
    return load_programs(REAL_DATA_DIR / "programs.csv")


@pytest.fixture(scope="session")
def real_scholarships():
    return load_scholarships(REAL_DATA_DIR / "scholarships.csv")


@pytest.fixture(scope="session")
def real_living_costs():
    return load_living_costs(REAL_DATA_DIR / "living_costs.csv")


# The API normally reads the CSV files on every request. For the real-data tests we hand it the
# rows loaded above instead, so an API test measures the search, not the disk.
# Each replacement first checks that the API asked for the REAL file, so the test still proves
# the API uses data/ when GRADMATCH_DATA_DIR is not set.
# It is function-scoped (monkeypatch), so the other API tests still read their own small files.
@pytest.fixture
def real_data_api(monkeypatch, real_programs, real_scholarships, real_living_costs):
    def serve(rows, filename):
        def load(path):
            assert Path(path) == REAL_DATA_DIR / filename
            # A fresh list each time, so a caller that changes the list cannot change the cache.
            return list(rows) if isinstance(rows, list) else dict(rows)
        return load

    monkeypatch.delenv("GRADMATCH_DATA_DIR", raising=False)      # use the real data/ folder
    monkeypatch.setattr(api, "load_programs", serve(real_programs, "programs.csv"))
    monkeypatch.setattr(api, "load_scholarships", serve(real_scholarships, "scholarships.csv"))
    monkeypatch.setattr(api, "load_living_costs", serve(real_living_costs, "living_costs.csv"))
    return api.app
