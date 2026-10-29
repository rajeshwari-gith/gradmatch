"""Starred items: the programs, scholarships and deadlines a student marks to keep.

Every item gets a key: "program:<program_id>", "scholarship:<scholarship_id>" or
"deadline:<name>" for a deadline the student added. The starred set is a
frozenset of keys; toggle() returns a new set and never changes the old one.
These are plain functions with no screen code, so the website and the API use
the same rules and the tests need no browser.
"""
# In plain words: a student can star the things they care about and then show only those.
# Each item becomes a short text key, because a key is easy to store (in the page's memory, in
# the API, or in a file) and two kinds of item can never get the same key thanks to the prefix.
# The set of stars is frozen: toggling gives back a new set, so an old set held somewhere else
# never changes behind its back.

from gradmatch.deadlines import CustomDeadline
from gradmatch.models import Program, Scholarship

PREFIXES = ("program", "scholarship", "deadline")


# The key of one item. A program and a scholarship with the same id get different keys.
def star_key(item: Program | Scholarship | CustomDeadline) -> str:
    if isinstance(item, Program):
        return f"program:{item.program_id}"
    if isinstance(item, Scholarship):
        return f"scholarship:{item.scholarship_id}"
    if isinstance(item, CustomDeadline):
        return f"deadline:{item.name}"
    raise TypeError(f"cannot star a {type(item).__name__}")


# True if the text looks like a key: one of the three prefixes, a colon, and something after it.
# The API uses this to refuse keys such as "progam:X" or "program:".
def is_star_key(key) -> bool:
    if not isinstance(key, str):
        return False
    prefix, colon, rest = key.partition(":")
    return prefix in PREFIXES and colon == ":" and rest.strip() != ""


# Star the key if it is not starred yet, otherwise take the star away. Returns a new set.
def toggle(starred: frozenset, key: str) -> frozenset:
    return starred - {key} if key in starred else starred | {key}


# Keep only the starred items, in the order they were given (so a sorted list stays sorted).
def only_starred(items: list, starred: frozenset) -> list:
    return [item for item in items if star_key(item) in starred]
