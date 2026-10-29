"""Helpers the system and acceptance tests share to drive the app and read its screens.

In plain words: the app draws its rows and cards as HTML. These helpers open the app, press
buttons, switch screens and pull out what a student would read (names, costs, chance labels,
days left), so each test can say what it checks in one line.
"""
import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")
SEARCH, PHD, SCHOLARSHIPS, DEADLINES = "Program search", "PhD funding", "Scholarships", "Deadlines"


def open_app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception
    return at


def go(at, page: str) -> AppTest:
    at.radio(key="page").set_value(page).run()
    assert not at.exception
    return at


def find_programs(at) -> AppTest:
    if at.radio(key="page").value != SEARCH:
        go(at, SEARCH)
    next(b for b in at.button if b.label == "Find programs").click().run()
    assert not at.exception
    return at


def search_for(at, degree="MS", field="Computer Science", budget=40_000, gpa=3.5, states=None,
               special=None, citizenship=None, toefl=None) -> AppTest:
    if at.radio(key="page").value != SEARCH:
        go(at, SEARCH)
    at.radio(key="degree").set_value(degree)
    at.selectbox(key="field").set_value(field)
    at.number_input(key="gpa").set_value(gpa)
    at.number_input(key="budget").set_value(budget)
    if states:
        at.multiselect(key="preferred_states").set_value(states)
    if special:
        at.multiselect(key="special").set_value(special)
    if citizenship:
        at.selectbox(key="citizenship").set_value(citizenship)
    if toefl is not None:
        at.number_input(key="toefl").set_value(toefl)
    return find_programs(at)


def _blocks(at, marker: str) -> list[str]:
    return [m.value for m in at.markdown if marker in m.value]


# ---- Program search ----

def rows(at) -> list[str]:
    return _blocks(at, 'class="gm-grid gm-row"')


def row_names(at) -> list[str]:
    names = []
    for row in rows(at):
        school, program = re.search(r'class="gm-name">([^<]+)</div><div class="gm-sub">([^<]+?) ·', row).groups()
        names.append(f"{school} – {program}")
    return names


def yearly_costs(at) -> list[int]:
    return [int(re.search(r'gm-money"[^>]*>\$([\d,]+)<', row).group(1).replace(",", "")) for row in rows(at)]


def chances(at) -> list[str]:
    return [re.findall(r"<span>([^<]+)</span></span>", row)[-1] for row in rows(at)]


def chance_filter(at) -> list[str]:
    return list(at.radio(key="chance").options)


def captions(at) -> str:
    return " ".join(c.value for c in at.caption)


def infos(at) -> str:
    return " ".join(i.value for i in at.info)


def metrics(at) -> dict:
    return {m.label: m.value for m in at.metric}


# ---- PhD funding ----

def phd_cards(at) -> list[str]:
    return _blocks(at, 'class="gm-fundbar"')


def phd_names(at) -> list[str]:
    return [re.search(r'class="gm-name gm-serif">([^<]+)<', card).group(1) for card in phd_cards(at)]


# ---- Scholarships ----

def scholarship_cards(at) -> list[str]:
    return [b for b in _blocks(at, 'class="gm-name gm-serif"') if 'class="gm-tag"' in b]


def scholarship_names(at) -> list[str]:
    return [re.search(r'class="gm-name gm-serif">([^<]+)<', card).group(1) for card in scholarship_cards(at)]


def scholarship_amounts(at) -> list[str]:
    return [re.search(r'gm-money gm-big">([^<]+)<', b).group(1) for b in _blocks(at, 'class="gm-amount"')]


# ---- Deadlines ----

def deadline_rows(at) -> list[str]:
    return [b for b in _blocks(at, 'class="gm-datetile"') if 'class="gm-cell-name"' in b]


def deadline_names(at) -> list[str]:
    return [re.search(r'class="gm-name(?: gm-passed)?">([^<]+)<', row).group(1) for row in deadline_rows(at)]


def days_left(at) -> list[str]:
    return [re.findall(r"<span>([^<]+)</span></span>", row)[-1] for row in deadline_rows(at)]


def banner(at) -> str:
    found = _blocks(at, 'role="alert"')
    return found[0] if found else ""


def header_pills(at) -> str:
    return _blocks(at, 'class="gm-pill gm-pill-star"')[0]
