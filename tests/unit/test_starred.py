"""Unit tests for starred.py.

Techniques: equivalence partitioning on the kind of item (program,
scholarship, custom deadline, something else) and on keys (good, each kind
of bad key); toggling twice gives back the starting set.
"""
# In plain words: these tests check that every kind of item gets its own key, that a star can
# be added and taken away without changing the old set, and that filtering keeps the order.

from datetime import date

import pytest
from hypothesis import given, strategies as st

from conftest import make_program
from gradmatch.deadlines import CustomDeadline
from gradmatch.models import Scholarship
from gradmatch.starred import is_star_key, only_starred, star_key, toggle

pytestmark = pytest.mark.unit


def make_scholarship(scholarship_id="S1") -> Scholarship:
    return Scholarship(scholarship_id=scholarship_id, name="Test", type="fellowship", amount=1.0,
                       degree_levels=("MS",), fields=("Any",), min_gpa=0.0, citizenship=("Any",),
                       states=("Any",), special=(), deadline=date(2026, 12, 1),
                       website="https://example.org/s")


# ---- star_key() ----
# Why: each kind of item needs its own prefix, so equal ids of different kinds never clash.

def test_star_key_for_each_kind_of_item():
    assert star_key(make_program(program_id="X1")) == "program:X1"
    assert star_key(make_scholarship("X1")) == "scholarship:X1"
    assert star_key(CustomDeadline("Essay draft", date(2026, 11, 2))) == "deadline:Essay draft"


@pytest.mark.parametrize("item", ["program:X1", None, 5])
def test_star_key_of_something_else_is_an_error(item):
    with pytest.raises(TypeError, match=f"cannot star a {type(item).__name__}"):
        star_key(item)


# ---- is_star_key() ----

@pytest.mark.parametrize("key", ["program:X1", "scholarship:S1", "deadline:Essay: draft 2"])
def test_good_keys(key):
    assert is_star_key(key) is True


@pytest.mark.parametrize("key", ["", "program", "program:", "program:  ", "progam:X1", ":X1",
                                 "Program:X1", None, 5])
def test_bad_keys(key):
    assert is_star_key(key) is False


# ---- toggle() ----

def test_toggle_adds_then_removes_and_never_changes_the_old_set():
    empty = frozenset()

    one = toggle(empty, "program:X1")
    back = toggle(one, "program:X1")

    assert (empty, one, back) == (frozenset(), frozenset({"program:X1"}), frozenset())
    assert isinstance(one, frozenset) and isinstance(back, frozenset)


def test_toggle_leaves_other_stars_alone():
    starred = frozenset({"program:A", "scholarship:B"})

    assert toggle(starred, "program:A") == frozenset({"scholarship:B"})
    assert toggle(starred, "deadline:C") == starred | {"deadline:C"}


# Why (property-based): toggling the same key twice must always give back the starting set.
@given(starred=st.frozensets(st.text(max_size=5)), key=st.text(max_size=5))
def test_toggle_twice_gives_back_the_same_set(starred, key):
    assert toggle(toggle(starred, key), key) == starred


# ---- only_starred() ----

def test_only_starred_keeps_the_given_order_and_mixes_kinds():
    program_b, program_a = make_program(program_id="B"), make_program(program_id="A")
    scholarship = make_scholarship("A")
    custom = CustomDeadline("Essay draft", date(2026, 11, 2))
    starred = frozenset({"program:A", "program:B", "deadline:Essay draft", "program:GONE"})

    assert only_starred([program_b, scholarship, custom, program_a], starred) == [program_b, custom, program_a]


def test_only_starred_with_no_stars_or_no_items_is_empty():
    assert only_starred([make_program()], frozenset()) == []
    assert only_starred([], frozenset({"program:P1"})) == []
