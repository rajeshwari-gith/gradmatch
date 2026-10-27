"""System tests for the results page in app/streamlit_app.py.

The app runs on the small fixed data in conftest.py with "today" fixed at
2026-10-24 (see the table in that file), so every number below is stable.

Techniques: equivalence partitioning (no results / some results, MS / PhD,
open / closed deadlines), boundary-value analysis on the budget (just under
and exactly at a program's cost) and a regression test for defect D-001.
"""
import re

import pytest
from streamlit.testing.v1 import AppTest


pytestmark = pytest.mark.system

APP = str(__import__("pathlib").Path(__file__).resolve().parents[2] / "app" / "streamlit_app.py")


@pytest.fixture
def app():
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception
    return at


def submit(at):
    at.button[0].click().run()
    assert not at.exception
    return at


def metrics(at):
    return {m.label: m.value for m in at.metric}


def cards(at):
    """The HTML of the result cards (the markdown block that is not the stylesheet)."""
    blocks = [m.value for m in at.markdown if 'class="gm-card"' in m.value and "<style>" not in m.value]
    return blocks[0] if blocks else ""


def card_titles(at):
    return re.findall(r'class="gm-title"[^>]*>([^<]+)<', cards(at))


def yearly_costs(at):
    return [int(c.replace(",", "")) for c in
            re.findall(r'gm-stat-value">\$([\d,]+)</div><div class="gm-stat-label">per year', cards(at))]


def search_for(at, degree="MS", field="Computer Science", budget=40_000, gpa=3.5, states=None):
    at.radio(key="degree").set_value(degree)
    at.selectbox(key="field").set_value(field)
    at.number_input(key="gpa").set_value(gpa)
    at.number_input(key="budget").set_value(budget)
    if states:
        at.multiselect(key="preferred_states").set_value(states)
    return submit(at)


# ---- Before searching ----

def test_nothing_is_listed_before_the_student_submits(app):
    assert not app.metric
    assert cards(app) == ""


# ---- Default profile: MS, Computer Science, GPA 3.5, MI, budget $40,000 ----

def test_default_profile_lists_the_two_affordable_programs(app):
    submit(app)
    assert card_titles(app) == ["Cheap State University – MS in Computer Science",
                                "Middle University – MS in Computer Science"]


def test_results_are_sorted_cheapest_first(app):
    submit(app)
    assert yearly_costs(app) == [25000, 35000]


def test_summary_numbers(app):
    submit(app)
    assert metrics(app) == {
        "Programs found": "2",
        "Safety / Match / Reach": "1 / 1 / 0",
        "Next deadline": "Nov 5, 2026 · 12 days left",
    }


def test_cards_show_fit_funding_and_deadline_labels(app):
    submit(app)
    html = cards(app)
    for text in ["Safety", "Match", "Self-Funded", "Nov 5, 2026 · 12 days left", "Jan 15, 2027 · 83 days left"]:
        assert text in html


def test_urgent_deadline_is_colored_coral(app):
    submit(app)
    assert '--chip:#F0705F">Nov 5, 2026' in cards(app)


def test_each_card_links_to_the_official_website(app):
    submit(app)
    assert 'href="https://example.edu/cheap"' in cards(app)
    assert cards(app).count('target="_blank"') == 2


def test_cost_chart_is_shown_when_there_are_results(app):
    submit(app)
    assert len(app.get("vega_lite_chart")) == 1


# ---- Boundary-value analysis on the budget (cheapest program costs $25,000) ----

@pytest.mark.parametrize("budget, found", [(24_999, 0), (25_000, 1), (25_001, 1)])
def test_budget_boundary(app, budget, found):
    search_for(app, budget=budget)
    assert len(card_titles(app)) == found


# ---- No results ----

def test_zero_budget_shows_a_helpful_message(app):
    search_for(app, budget=0)
    assert "No programs match" in app.info[0].value
    assert not app.metric
    assert cards(app) == ""
    assert len(app.get("vega_lite_chart")) == 0


# ---- Other searches ----

def test_bigger_budget_adds_the_expensive_program_with_a_closed_deadline(app):
    search_for(app, budget=100_000)
    assert len(card_titles(app)) == 3
    assert "Closed Oct 1, 2026" in cards(app)
    assert metrics(app)["Safety / Match / Reach"] == "1 / 1 / 1"
    assert metrics(app)["Next deadline"] == "Nov 5, 2026 · 12 days left"


def test_preferred_state_limits_the_results(app):
    search_for(app, budget=100_000, states=["CA"])
    assert card_titles(app) == ["Pricey Tech – MS in Computer Science"]


def test_other_field_shows_only_that_field(app):
    search_for(app, field="Data Science", budget=100_000)
    assert card_titles(app) == ["Texas Data Institute – MS in Data Science"]
    assert yearly_costs(app) == [38000]  # out-of-state tuition 24,000 + living cost 14,000


# ---- Regression test for defect D-001: funded PhD programs cost $0 ----

def test_funded_phd_is_listed_at_zero_cost_even_with_zero_budget(app):
    search_for(app, degree="PhD", budget=0, gpa=3.9)
    assert card_titles(app) == ["Funded University – PhD in Computer Science"]
    assert yearly_costs(app) == [0]
    assert "Fully Funded" in cards(app)


def test_phd_results_are_ordered_by_funding_left_after_living_costs(app):
    search_for(app, degree="PhD", budget=100_000, gpa=3.9)
    assert card_titles(app) == ["Funded University – PhD in Computer Science",
                                "Partly Funded Institute – PhD in Computer Science"]
    assert yearly_costs(app) == [0, 15000]
    assert "Partially Funded" in cards(app)


# ---- A different "today" ----

def test_every_deadline_is_closed_after_the_last_one_has_passed(app, monkeypatch):
    monkeypatch.setenv("GRADMATCH_TODAY", "2027-12-01")
    app.run()
    submit(app)
    assert metrics(app)["Next deadline"] == "All closed"
    assert cards(app).count("Closed ") == 2


# ---- Invalid profiles never reach the results ----

def test_invalid_profile_shows_errors_and_no_results(app):
    app.number_input(key="gpa").set_value(5.0)
    submit(app)
    assert app.error and not app.metric
    assert cards(app) == ""


# ---- Notes and warnings added after review ----

def test_a_note_explains_that_the_numbers_are_estimates_and_fees_are_left_out(app):
    submit(app)
    notes = " ".join(c.value for c in app.caption)
    assert "estimates" in notes
    assert "mandatory student fees" in notes


def test_cards_label_gpa_and_acceptance_rate_as_estimates(app):
    submit(app)
    assert cards(app).count("avg GPA (est.)") == 2
    assert cards(app).count("accepted (est.)") == 2


def test_international_student_with_a_low_toefl_sees_a_warning_on_programs_that_need_more(app):
    app.selectbox(key="citizenship").set_value("International")
    app.number_input(key="toefl").set_value(80)
    search_for(app, budget=100_000)
    html = cards(app)
    assert "TOEFL min 85 · you 80" in html      # Middle University needs 85
    assert "TOEFL min 100 · you 80" in html     # Pricey Tech needs 100
    assert html.count("TOEFL min") == 2         # Cheap State needs exactly 80: no warning


def test_us_student_without_a_toefl_score_sees_no_toefl_warning(app):
    search_for(app, budget=100_000)
    assert "TOEFL" not in cards(app)
