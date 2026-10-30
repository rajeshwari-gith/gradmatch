"""Application requirements (essays, statements) from data/requirements.csv.

Columns: program_id, name, required, limit_text, prompt_text, source_url,
checked_by, checked_on. One row is one thing a program asks for, for example
"Statement of purpose". Every row must come from the program's official page,
checked by a person: source_url (https), checked_by and checked_on are required.
`required` is yes or no. A blank limit_text or prompt_text means the page does
not state it and becomes None; it is never filled in with a guess.

For the Essays screen, checklist() lists one program's requirements with a
done mark, and progress() counts the required ones that are done. The done
set holds essay_key(program_id, name) keys, so the same essay name at two
programs is ticked off separately.
"""

from dataclasses import dataclass, fields
from datetime import date
from typing import NamedTuple

from gradmatch.data_loader import _cell, _date, _load, _text

YES_NO = {"yes": True, "no": False}


# One row of requirements.csv. None means "not stated on the official page".
@dataclass(frozen=True)
class Requirement:
    program_id: str
    name: str                     # e.g. "Statement of purpose"
    required: bool                # False = optional
    limit_text: str | None        # e.g. "2 pages" or "1,000 words", as the page says it
    prompt_text: str | None       # the question, word for word
    source_url: str               # the official page it was copied from
    checked_by: str
    checked_on: date


COLUMNS = [f.name for f in fields(Requirement)]


# One line of the Essays checklist. A NamedTuple, so it can be unpacked as
# (name, required, limit_text, done) and also read as item.name, item.done, ...
class ChecklistItem(NamedTuple):
    name: str
    required: bool
    limit_text: str | None        # None = the official page does not state a limit
    done: bool


# Read requirements.csv with the same loader as the other files, so a bad row stops with the
# file name and line number.
def load_requirements(path) -> list[Requirement]:
    return _load(path, COLUMNS, _to_requirement)


# All requirements of one program, in file order.
def requirements_for(program_id: str, requirements: list[Requirement]) -> list[Requirement]:
    return [r for r in requirements if r.program_id == program_id]


def _to_requirement(row) -> Requirement:
    required = _text(row, "required")
    if required not in YES_NO:
        raise ValueError(f"required must be yes or no, got '{required}'")
    source_url = _text(row, "source_url")
    if not source_url.startswith("https://"):
        raise ValueError(f"source_url must start with https://, got '{source_url}'")
    return Requirement(
        program_id=_text(row, "program_id"),
        name=_text(row, "name"),
        required=YES_NO[required],
        limit_text=_cell(row, "limit_text") or None,      # blank = not stated
        prompt_text=_cell(row, "prompt_text") or None,
        source_url=source_url,
        checked_by=_text(row, "checked_by"),
        checked_on=_date(row, "checked_on"),
    )


# ---- The Essays checklist ----
# In plain words: the student ticks off each essay as it is written. The screen keeps the ticks
# as a set of keys; these functions only read that set, so they are easy to test and never
# change anything. A tick for an essay the program does not ask for is simply ignored.

# The key of one essay in the done set: "<program_id>:<name>".
def essay_key(program_id: str, name: str) -> str:
    return f"{program_id}:{name}"


# One program's requirements in the order of the data file, each with its done mark.
def checklist(program_id: str, requirements: list[Requirement], done: frozenset) -> list[ChecklistItem]:
    return [ChecklistItem(r.name, r.required, r.limit_text, essay_key(program_id, r.name) in done)
            for r in requirements_for(program_id, requirements)]


# (done_required, total_required) for one program. Optional items are left out on purpose: the
# progress bar shows what the student MUST still write, and an optional essay never blocks it.
def progress(program_id: str, requirements: list[Requirement], done: frozenset) -> tuple[int, int]:
    required = [item for item in checklist(program_id, requirements, done) if item.required]
    return sum(1 for item in required if item.done), len(required)
