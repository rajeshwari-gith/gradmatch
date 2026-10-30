"""Application requirements (essays, statements) from data/requirements.csv.

Columns: program_id, name, required, limit_text, prompt_text, source_url,
checked_by, checked_on. One row is one thing a program asks for, for example
"Statement of purpose". Every row must come from the program's official page,
checked by a person: source_url (https), checked_by and checked_on are required.
`required` is yes or no. A blank limit_text or prompt_text means the page does
not state it and becomes None; it is never filled in with a guess.
"""
# In plain words: students want to know which essays each program asks for, how long they may
# be and what the question is. Nobody may make that up, so this file only reads rows that a
# person copied from the official page, and it refuses a row without the page link, the
# checker's name or the date. The prompt is kept word for word as it was typed.

from dataclasses import dataclass, fields
from datetime import date

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
