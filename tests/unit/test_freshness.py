"""Unit tests for app/freshness.py.

They use small fake dictionaries instead of the real sys.modules, so the test run itself is
never disturbed. Equivalence partitioning on the state of the loaded package: not loaded,
up to date, changed on disk, and loaded by an older version that had no signature.
"""
from pathlib import Path
from types import SimpleNamespace

import pytest

import gradmatch
from freshness import forget_stale_gradmatch, source_signature

pytestmark = pytest.mark.unit

PACKAGE_DIR = Path(gradmatch.__file__).parent


def fake_modules(signature="MISSING"):
    package = SimpleNamespace() if signature == "MISSING" else SimpleNamespace(SOURCE_SIGNATURE=signature)
    return {"gradmatch": package, "gradmatch.search": object(), "gradmatch.cost": object(),
            "gradmatch_other": object(), "streamlit": object()}


def test_the_package_fingerprint_matches_the_files_on_disk():
    assert gradmatch.SOURCE_SIGNATURE == source_signature(PACKAGE_DIR)


def test_nothing_happens_when_gradmatch_is_not_loaded_yet():
    modules = {"streamlit": object()}
    assert forget_stale_gradmatch(PACKAGE_DIR, modules) is False
    assert list(modules) == ["streamlit"]


def test_up_to_date_modules_are_kept():
    modules = fake_modules(source_signature(PACKAGE_DIR))
    assert forget_stale_gradmatch(PACKAGE_DIR, modules) is False
    assert len(modules) == 5


def test_changed_source_files_drop_every_gradmatch_module_and_nothing_else():
    modules = fake_modules(signature=(("search.py", 1, 1),))      # differs from the disk
    assert forget_stale_gradmatch(PACKAGE_DIR, modules) is True
    assert sorted(modules) == ["gradmatch_other", "streamlit"]


def test_a_package_loaded_by_an_older_version_without_a_signature_counts_as_stale():
    modules = fake_modules()                                       # no SOURCE_SIGNATURE at all
    assert forget_stale_gradmatch(PACKAGE_DIR, modules) is True
    assert "gradmatch" not in modules and "gradmatch.search" not in modules


def test_the_fingerprint_changes_when_a_file_changes(tmp_path):
    (tmp_path / "a.py").write_text("x = 1")
    before = source_signature(tmp_path)
    (tmp_path / "a.py").write_text("x = 22")                       # different size
    assert source_signature(tmp_path) != before


def test_the_fingerprint_changes_when_a_file_is_added(tmp_path):
    (tmp_path / "a.py").write_text("x = 1")
    before = source_signature(tmp_path)
    (tmp_path / "b.py").write_text("y = 2")
    assert source_signature(tmp_path) != before


def test_non_python_files_do_not_change_the_fingerprint(tmp_path):
    (tmp_path / "a.py").write_text("x = 1")
    before = source_signature(tmp_path)
    (tmp_path / "notes.txt").write_text("hello")
    assert source_signature(tmp_path) == before
