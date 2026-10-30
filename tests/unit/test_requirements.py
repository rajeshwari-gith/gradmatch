"""Unit tests for requirements.py.

Technique: equivalence partitioning on each cell (good value, blank, each
kind of bad value) and on the file (no rows, several programs). The tests
write tiny files in tmp_path and never read the real data folder.
"""
# In plain words: these tests check that a row copied from an official page loads exactly as
# typed, that blank limits and prompts become None (never a made-up text), and that a row
# without its page link, checker or date is refused with the file name and line number.

from datetime import date

import pytest

from gradmatch.data_loader import DataError
from gradmatch.requirements import (COLUMNS, Requirement, checklist, essay_key, load_requirements, progress,
                                    requirements_for)

pytestmark = pytest.mark.unit

HEADER = ",".join(COLUMNS)
GOOD = ('P1,Statement of purpose,yes,"1,000 words","Why this program, and why now?",'
        "https://example.edu/apply,Sai Nishith Jangili,2026-10-29")


def write(tmp_path, *rows) -> str:
    path = tmp_path / "requirements.csv"
    path.write_text("\n".join([HEADER, *rows]) + "\n", encoding="utf-8")
    return path


def row(**cells) -> str:
    values = dict(program_id="P1", name="Writing sample", required="no", limit_text="",
                  prompt_text="", source_url="https://example.edu/apply", checked_by="R. Galugu",
                  checked_on="2026-10-29")
    values.update(cells)
    return ",".join(values[name] for name in COLUMNS)


# ---- Valid rows ----

def test_good_row_loads_exactly_as_typed(tmp_path):
    assert load_requirements(write(tmp_path, GOOD)) == [Requirement(
        program_id="P1", name="Statement of purpose", required=True, limit_text="1,000 words",
        prompt_text="Why this program, and why now?", source_url="https://example.edu/apply",
        checked_by="Sai Nishith Jangili", checked_on=date(2026, 10, 29))]


def test_blank_limit_and_prompt_are_none_and_no_means_optional(tmp_path):
    [requirement] = load_requirements(write(tmp_path, row()))

    assert (requirement.required, requirement.limit_text, requirement.prompt_text) == (False, None, None)


def test_file_with_only_the_header_has_no_requirements(tmp_path):
    assert load_requirements(write(tmp_path)) == []


def test_requirements_for_one_program_keeps_file_order(tmp_path):
    loaded = load_requirements(write(tmp_path, row(name="B"), row(program_id="P2"), row(name="A")))

    assert [r.name for r in requirements_for("P1", loaded)] == ["B", "A"]
    assert requirements_for("NONE", loaded) == []


# ---- Invalid rows: one mistake each ----
# Why: a row that cannot be traced to an official page and a person must never load.

@pytest.mark.parametrize("cells, message", [
    (dict(program_id=""), "program_id is required"),
    (dict(name=""), "name is required"),
    (dict(required=""), "required is required"),
    (dict(required="Yes"), "required must be yes or no, got 'Yes'"),
    (dict(required="optional"), "required must be yes or no, got 'optional'"),
    (dict(source_url=""), "source_url is required"),
    (dict(source_url="http://example.edu"), "source_url must start with https://, got 'http://example.edu'"),
    (dict(checked_by=""), "checked_by is required"),
    (dict(checked_on=""), "checked_on is required"),
    (dict(checked_on="2026-02-30"), "checked_on must be a real date in YYYY-MM-DD format, got '2026-02-30'"),
])
def test_bad_row_is_refused_with_line_number(tmp_path, cells, message):
    path = write(tmp_path, GOOD, row(**cells))

    with pytest.raises(DataError) as error:
        load_requirements(path)

    assert str(error.value) == f"{path}, line 3: {message}"


def test_missing_column_is_reported(tmp_path):
    path = tmp_path / "requirements.csv"
    path.write_text("program_id,name\nP1,Essay\n")

    with pytest.raises(DataError, match="missing column\\(s\\): required, limit_text"):
        load_requirements(path)


# ---- The Essays checklist: checklist() and progress() ----
# Why (boundary values): nothing done, everything done, and optional items that never count;
# (equivalence classes): ticks for this program, for another program and for unknown names.
# The requirements are made in the test; none is real data.

def req(name, required=True, program_id="P1", limit_text=None) -> Requirement:
    return Requirement(program_id=program_id, name=name, required=required, limit_text=limit_text,
                       prompt_text=None, source_url="https://example.edu/apply", checked_by="Tester",
                       checked_on=date(2026, 10, 29))


ESSAYS = [req("Statement", limit_text="2 pages"), req("Writing sample", required=False),
          req("Statement", program_id="P2"), req("Diversity essay", limit_text="500 words")]


def test_essay_key():
    assert essay_key("P1", "Statement") == "P1:Statement"


def test_checklist_lists_one_program_in_file_order_with_done_marks():
    items = checklist("P1", ESSAYS, frozenset({"P1:Diversity essay"}))

    assert items == [("Statement", True, "2 pages", False), ("Writing sample", False, None, False),
                     ("Diversity essay", True, "500 words", True)]
    assert (items[0].name, items[0].required, items[0].limit_text, items[0].done) == items[0]


def test_a_tick_for_the_same_name_at_another_program_does_not_count():
    assert [i.done for i in checklist("P1", ESSAYS, frozenset({"P2:Statement"}))] == [False, False, False]
    assert [i.done for i in checklist("P2", ESSAYS, frozenset({"P2:Statement"}))] == [True]


def test_checklist_of_a_program_without_requirements_is_empty():
    assert checklist("NONE", ESSAYS, frozenset({"NONE:Statement"})) == []


@pytest.mark.parametrize("done, expected", [
    (frozenset(), (0, 2)),                                              # boundary: nothing done
    (frozenset({"P1:Statement"}), (1, 2)),
    (frozenset({"P1:Statement", "P1:Diversity essay"}), (2, 2)),        # boundary: all done
    (frozenset({"P1:Statement", "P1:Diversity essay", "P1:Writing sample"}), (2, 2)),
    (frozenset({"P1:Writing sample"}), (0, 2)),                         # optional never counts
    (frozenset({"P2:Statement", "P1:Unknown"}), (0, 2)),                # other program, unknown name
])
def test_progress_counts_only_required_items(done, expected):
    assert progress("P1", ESSAYS, done) == expected


def test_progress_with_only_optional_or_no_requirements_is_zero_of_zero():
    assert progress("P1", [req("Writing sample", required=False)], frozenset({"P1:Writing sample"})) == (0, 0)
    assert progress("NONE", ESSAYS, frozenset()) == (0, 0)
