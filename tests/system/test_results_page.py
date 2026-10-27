"""System tests for the results page in app/streamlit_app.py.

The app runs on the small fixed data in conftest.py with "today" fixed at
2026-10-24 (see the tables in that file), so every number below is stable.

Techniques: equivalence partitioning (no results / some results, MS / PhD,
open / closed deadlines), boundary-value analysis on the budget and on a
scholarship's minimum GPA, a decision table for scholarship eligibility, and
regression tests for defect D-001.
"""
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

pytestmark = pytest.mark.system

# In plain words: these tests run the whole app on a tiny fixed data set, press "Find programs",
# and check the page: the cards, the numbers, the sorting, the scholarships and deadlines tabs,
# the charts and the downloads. Because the data and "today" are fixed, every answer is stable.

APP = str(Path(__file__).resolve().parents[2] / "app" / "streamlit_app.py")
PROGRAMS, SCHOLARSHIPS, DEADLINES = 0, 1, 2     # tab positions


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
    """Metric label -> shown text (the delta, such as '12 days left', is joined with ' · ')."""
    return {m.label: m.value + (f" · {m.delta}" if m.delta else "") for m in at.metric}


def tab_html(at, tab):
    """The HTML cards shown in one tab (the markdown that holds card markup)."""
    blocks = [m.value for m in at.tabs[tab].markdown if 'class="gm-card"' in m.value]
    return blocks[0] if blocks else ""


def cards(at):
    return tab_html(at, PROGRAMS)


def titles(at, tab=PROGRAMS):
    return re.findall(r'class="gm-title"[^>]*>([^<]+)<', tab_html(at, tab))


def card_titles(at):
    return titles(at, PROGRAMS)


def yearly_costs(at):
    return [int(c.replace(",", "")) for c in
            re.findall(r'gm-stat-value">\$([\d,]+)</div><div class="gm-stat-label">per year', cards(at))]


def captions(at, tab):
    return " ".join(c.value for c in at.tabs[tab].caption)


def search_for(at, degree="MS", field="Computer Science", budget=40_000, gpa=3.5, states=None,
               special=None):
    at.radio(key="degree").set_value(degree)
    at.selectbox(key="field").set_value(field)
    at.number_input(key="gpa").set_value(gpa)
    at.number_input(key="budget").set_value(budget)
    if states:
        at.multiselect(key="preferred_states").set_value(states)
    if special:
        at.multiselect(key="special").set_value(special)
    return submit(at)


# ---- Before searching ----

def test_nothing_is_listed_before_the_student_submits(app):
    assert not app.metric
    assert not app.tabs


# ---- Default profile: MS, Computer Science, GPA 3.5, MI, budget $40,000 ----

def test_default_profile_lists_the_two_affordable_programs(app):
    submit(app)
    assert card_titles(app) == ["Cheap State University – MS in Computer Science",
                                "Middle University – MS in Computer Science"]


def test_page_has_three_tabs(app):
    submit(app)
    assert [t.label for t in app.tabs] == ["Programs", "Scholarships", "Deadlines"]


def test_results_are_sorted_cheapest_first(app):
    submit(app)
    assert yearly_costs(app) == [25000, 35000]


def test_summary_numbers(app):
    submit(app)
    summary = metrics(app)
    assert summary["Programs found"] == "2"
    assert summary["Safety / Match / Reach"] == "1 / 1 / 0"
    assert summary["Scholarships you qualify for"] == "1"
    assert summary["Next deadline"] == "Nov 5, 2026 · 12 days left"


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


def test_cost_charts_are_shown_when_there_are_results(app):
    submit(app)
    assert len(app.get("vega_lite_chart")) == 2     # fit chart and cost breakdown


# ---- Boundary-value analysis on the budget (cheapest program costs $25,000) ----

@pytest.mark.parametrize("budget, found", [(24_999, 0), (25_000, 1), (25_001, 1)])
def test_budget_boundary(app, budget, found):
    search_for(app, budget=budget)
    assert len(card_titles(app)) == found


# ---- No results ----

def test_zero_budget_shows_a_helpful_message(app):
    search_for(app, budget=0)
    assert "No programs match" in app.tabs[PROGRAMS].info[0].value
    assert not app.metric
    assert cards(app) == ""
    assert len(app.get("vega_lite_chart")) == 0


def test_scholarships_are_still_listed_when_no_program_matches(app):
    search_for(app, budget=0)
    assert titles(app, SCHOLARSHIPS) == ["Michigan Fee Waiver"]


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


# ---- Regression tests for defect D-001: funded PhD programs cost $0 ----
# Why: a regression test makes sure a bug we fixed once can never silently come back.

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
# Why: deadlines depend on the date, so we move "today" (GRADMATCH_TODAY) to test the future.

def test_every_deadline_is_closed_after_the_last_one_has_passed(app, monkeypatch):
    monkeypatch.setenv("GRADMATCH_TODAY", "2027-12-01")
    app.run()
    submit(app)
    assert metrics(app)["Next deadline"] == "All closed"
    assert cards(app).count("Closed ") == 2
    assert "No open deadlines" in app.tabs[DEADLINES].info[0].value or \
           "no open deadlines" in app.tabs[DEADLINES].info[0].value


# ---- Invalid profiles never reach the results ----

def test_invalid_profile_shows_errors_and_no_results(app):
    app.number_input(key="gpa").set_value(5.0)
    submit(app)
    assert app.error and not app.metric
    assert not app.tabs


def test_a_bad_submission_removes_the_old_results(app):
    submit(app)
    assert app.tabs
    app.number_input(key="gpa").set_value(5.0)
    submit(app)
    assert app.error and not app.tabs


# ---- Notes and warnings added after review ----

def test_a_note_explains_that_the_numbers_are_estimates_and_fees_are_left_out(app):
    submit(app)
    notes = captions(app, PROGRAMS)
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


# ---- Scholarships tab ----

def test_default_student_sees_only_the_open_scholarship_they_qualify_for(app):
    submit(app)
    assert titles(app, SCHOLARSHIPS) == ["Michigan Fee Waiver"]
    assert "Non-monetary" in tab_html(app, SCHOLARSHIPS)
    assert "1 open scholarship or opportunity you qualify for (1 already closed and hidden)" \
        in captions(app, SCHOLARSHIPS)


def test_scholarship_amounts_are_not_called_yearly_and_the_note_explains(app):
    submit(app)
    assert "per year" not in tab_html(app, SCHOLARSHIPS)
    assert "may be a yearly amount or a one-time total" in captions(app, SCHOLARSHIPS)


def test_expired_scholarships_are_hidden(app):
    submit(app)
    assert "Expired Award" not in tab_html(app, SCHOLARSHIPS)


def test_special_group_unlocks_more_scholarships_sorted_by_deadline(app):
    search_for(app, special=["first_gen"])
    assert titles(app, SCHOLARSHIPS) == ["First-Gen Grant", "Michigan Fee Waiver"]   # Nov 1, Jan 10
    assert metrics(app)["Scholarships you qualify for"] == "2"


def test_special_group_the_student_did_not_tick_stays_hidden(app):
    submit(app)
    assert "Women in STEM Award" not in tab_html(app, SCHOLARSHIPS)
    search_for(app, special=["women_stem"])
    assert "Women in STEM Award" in tab_html(app, SCHOLARSHIPS)


def test_phd_student_sees_the_phd_fellowship_but_not_ms_only_awards(app):
    search_for(app, degree="PhD", gpa=3.9)
    assert titles(app, SCHOLARSHIPS) == ["Funded PhD Fellowship"]


# Boundary-value analysis on the fellowship's minimum GPA of 3.5
@pytest.mark.parametrize("gpa, listed", [(3.45, False), (3.5, True), (3.55, True)])
def test_scholarship_minimum_gpa_boundary(app, gpa, listed):
    search_for(app, degree="PhD", gpa=gpa)
    assert ("Funded PhD Fellowship" in tab_html(app, SCHOLARSHIPS)) is listed


def test_international_student_does_not_see_us_only_fellowships(app):
    app.selectbox(key="citizenship").set_value("International")
    app.number_input(key="toefl").set_value(100)
    search_for(app, degree="PhD", gpa=3.9)
    assert "Funded PhD Fellowship" not in tab_html(app, SCHOLARSHIPS)
    assert "No scholarships match" in app.tabs[SCHOLARSHIPS].info[0].value


# ---- Deadlines tab ----

def test_deadlines_tab_lists_programs_and_scholarships_soonest_first(app):
    submit(app)
    assert titles(app, DEADLINES) == ["Cheap State University – MS in Computer Science",   # Nov 5
                                      "Michigan Fee Waiver",                               # Jan 10
                                      "Middle University – MS in Computer Science"]        # Jan 15


def test_deadlines_tab_marks_programs_and_scholarships(app):
    submit(app)
    html = tab_html(app, DEADLINES)
    assert html.count(">Program<") == 2 and html.count(">Scholarship<") == 1


def test_closed_items_are_left_out_of_the_deadlines_tab(app):
    search_for(app, budget=100_000)
    html = tab_html(app, DEADLINES)
    assert "Pricey Tech" not in html and "Expired Award" not in html


# ---- Downloads ----

def test_results_and_calendar_can_be_downloaded(app):
    submit(app)
    assert len(app.get("download_button")) == 2


def test_no_download_buttons_without_results(app):
    search_for(app, budget=0)
    assert len(app.get("download_button")) == 1     # only the calendar (the scholarship deadline)


# ---- Cost breakdown ----

def test_cost_breakdown_starts_with_the_first_program(app):
    submit(app)
    summary = metrics(app)
    assert summary["Tuition per year"] == "$10,000"
    assert summary["Living costs per year"] == "$15,000"
    assert summary["Stipend per year"] == "$0"
    assert summary["Total for 2 years"] == "$50,000"


def test_choosing_another_program_changes_the_breakdown_and_keeps_the_results(app):
    submit(app)
    app.selectbox(key="cost_choice").set_value(1).run()
    assert not app.exception
    assert metrics(app)["Tuition per year"] == "$20,000"
    assert metrics(app)["Total for 2 years"] == "$70,000"
    assert len(card_titles(app)) == 2           # the results did not disappear


def test_breakdown_of_a_funded_phd_shows_no_tuition_and_the_waiver_note(app):
    search_for(app, degree="PhD", gpa=3.9, budget=100_000)
    summary = metrics(app)
    assert summary["Tuition per year"] == "$0"
    assert summary["Stipend per year"] == "$30,000"
    assert any("tuition is assumed to be waived" in c.value for c in app.tabs[PROGRAMS].caption)


def test_old_results_do_not_come_back_when_the_page_reruns_after_a_bad_submission(app):
    submit(app)
    app.number_input(key="gpa").set_value(5.0)
    submit(app)
    app.run()                                  # a rerun with no new click
    assert not app.exception
    assert not app.tabs and not app.metric


# ---- Defect D-003: international students pay out-of-state tuition ----

def test_international_student_sees_the_out_of_state_cost_even_with_a_matching_home_state(app):
    app.selectbox(key="citizenship").set_value("International")
    app.number_input(key="toefl").set_value(100)
    app.selectbox(key="home_state").set_value("MI")
    search_for(app, budget=100_000)
    # Cheap State University is in MI: in-state $10,000, out-of-state $20,000, living $15,000
    assert yearly_costs(app)[0] == 20000 + 15000
    assert metrics(app)["Tuition per year"] == "$20,000"     # the cost breakdown agrees


def test_us_student_with_the_same_home_state_still_gets_the_in_state_cost(app):
    search_for(app, budget=100_000)
    assert yearly_costs(app)[0] == 10000 + 15000
    assert metrics(app)["Tuition per year"] == "$10,000"
