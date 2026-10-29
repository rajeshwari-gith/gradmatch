"""System tests for the four screens of app/streamlit_app.py.

The app runs on the small fixed data in tests/data_fixtures.py with "today" fixed at
2026-10-24 (see the tables in that file), so every number below is stable.

Techniques: equivalence partitioning (no results / some results, MS / PhD, open / closed
deadlines), boundary-value analysis on the budget, a scholarship's minimum GPA and the warning
window, a decision table for scholarship eligibility, and regression tests for defects D-001
and D-003.
"""
from datetime import date

import pytest

from app_pages import (DEADLINES, PHD, SCHOLARSHIPS, SEARCH, banner, captions, chance_filter, chances,
                       days_left, deadline_names, find_programs, go, header_pills, infos, metrics,
                       open_app, phd_cards, phd_names, row_names, rows, scholarship_amounts,
                       scholarship_names, search_for, yearly_costs)

pytestmark = pytest.mark.system

# In plain words: these tests run the whole app on a tiny fixed data set, press "Find programs",
# and check each screen: the results table, the PhD cards, the scholarships, the deadlines, the
# stars, the charts and the downloads. Because the data and "today" are fixed, every answer is stable.

CHEAP = "Cheap State University – MS in Computer Science"
MIDDLE = "Middle University – MS in Computer Science"
PRICEY = "Pricey Tech – MS in Computer Science"


@pytest.fixture
def app():
    return open_app()


def page_text(at) -> str:
    return " ".join(m.value for m in at.markdown)


# ---- Before searching ----

def test_nothing_is_listed_before_the_student_submits(app):
    assert rows(app) == []
    assert "Fill in your profile" in infos(app)


def test_the_four_screens_are_in_the_navigation(app):
    assert list(app.radio(key="page").options) == [SEARCH, PHD, SCHOLARSHIPS, DEADLINES]


def test_other_screens_ask_for_a_profile_first(app):
    go(app, PHD)
    assert "Fill in your profile" in infos(app) and phd_cards(app) == []
    go(app, SCHOLARSHIPS)
    assert "Fill in your profile" in infos(app) and scholarship_names(app) == []
    go(app, DEADLINES)
    assert "no deadlines" in infos(app)


# ---- Default profile: MS, Computer Science, GPA 3.5, MI, budget $40,000 ----

def test_default_profile_lists_the_two_affordable_programs_cheapest_first(app):
    find_programs(app)
    assert row_names(app) == [CHEAP, MIDDLE]
    assert yearly_costs(app) == [25000, 35000]
    assert chances(app) == ["Safety", "Match"]


def test_the_chance_filter_counts_each_label(app):
    find_programs(app)
    assert chance_filter(app) == ["All 2", "Safety 1", "Match 1"]
    app.radio(key="chance").set_value("Match").run()
    assert row_names(app) == [MIDDLE]


def test_rows_show_state_tuition_living_and_the_rate(app):
    find_programs(app)
    first = rows(app)[0]
    for text in ['MI <span class="gm-sub">in-state</span>', '<div data-label="Tuition">$10,000</div>', '<div data-label="Living">$15,000</div>']:
        assert text in first


def test_each_row_links_to_the_official_website_in_a_new_tab(app):
    find_programs(app)
    assert 'href="https://example.edu/cheap"' in rows(app)[0]
    assert all('target="_blank"' in row for row in rows(app))


def test_header_counts_stars_and_close_deadlines(app):
    find_programs(app)
    assert "★ Starred 0" in header_pills(app)
    assert "1 deadline in 14 days" in header_pills(app)    # Cheap State, 12 days away


def test_cost_charts_are_shown_when_there_are_results(app):
    find_programs(app)
    assert len(app.get("vega_lite_chart")) == 2     # cost breakdown and fit chart


# ---- Boundary-value analysis on the budget (cheapest program costs $25,000) ----

@pytest.mark.parametrize("budget, found", [(24_999, 0), (25_000, 1), (25_001, 1)])
def test_budget_boundary(app, budget, found):
    search_for(app, budget=budget)
    assert len(rows(app)) == found


# ---- No results ----

def test_zero_budget_shows_a_helpful_message(app):
    search_for(app, budget=0)
    assert "No programs match" in infos(app)
    assert rows(app) == []
    assert len(app.get("vega_lite_chart")) == 0
    assert len(app.get("download_button")) == 0


def test_scholarships_are_still_listed_when_no_program_matches(app):
    search_for(app, budget=0)
    go(app, SCHOLARSHIPS)
    assert scholarship_names(app) == ["Michigan Fee Waiver"]


# ---- Other searches ----

def test_bigger_budget_adds_the_expensive_reach_program(app):
    search_for(app, budget=100_000)
    assert row_names(app) == [CHEAP, MIDDLE, PRICEY]
    assert chance_filter(app) == ["All 3", "Safety 1", "Match 1", "Reach 1"]


def test_preferred_state_limits_the_results(app):
    search_for(app, budget=100_000, states=["CA"])
    assert row_names(app) == [PRICEY]
    assert "out-of-state" in rows(app)[0]


def test_other_field_shows_only_that_field(app):
    search_for(app, field="Data Science", budget=100_000)
    assert row_names(app) == ["Texas Data Institute – MS in Data Science"]
    assert yearly_costs(app) == [38000]  # out-of-state tuition 24,000 + living cost 14,000


# ---- Regression tests for defect D-001: funded PhD programs cost $0 ----
# Why: a regression test makes sure a bug we fixed once can never silently come back.

def test_funded_phd_is_listed_at_zero_cost_even_with_zero_budget(app):
    search_for(app, degree="PhD", budget=0, gpa=3.9)
    assert row_names(app) == ["Funded University – PhD in Computer Science"]
    assert yearly_costs(app) == [0]


def test_phd_results_are_ordered_by_funding_left_after_living_costs(app):
    search_for(app, degree="PhD", budget=100_000, gpa=3.9)
    assert row_names(app) == ["Funded University – PhD in Computer Science",
                              "Partly Funded Institute – PhD in Computer Science"]
    assert yearly_costs(app) == [0, 15000]


# ---- Invalid profiles never reach the results ----

def test_invalid_profile_shows_errors_and_no_results(app):
    app.number_input(key="gpa").set_value(5.0)
    find_programs(app)
    assert app.error and rows(app) == []


def test_a_bad_submission_removes_the_old_results(app):
    find_programs(app)
    assert rows(app)
    app.number_input(key="gpa").set_value(5.0)
    find_programs(app)
    assert app.error and rows(app) == []


def test_old_results_do_not_come_back_when_the_page_reruns_after_a_bad_submission(app):
    find_programs(app)
    app.number_input(key="gpa").set_value(5.0)
    find_programs(app)
    app.run()                                  # a rerun with no new click
    assert not app.exception
    assert rows(app) == [] and not app.metric


# ---- Notes and warnings ----

def test_a_note_explains_that_the_numbers_are_estimates_and_fees_are_left_out(app):
    find_programs(app)
    assert "estimates" in captions(app)
    assert "mandatory student fees" in captions(app)


def test_international_student_with_a_low_toefl_sees_a_warning_on_programs_that_need_more(app):
    search_for(app, budget=100_000, citizenship="International", toefl=80)
    html = " ".join(rows(app))
    assert "TOEFL min 85 · you 80" in html      # Middle University needs 85
    assert "TOEFL min 100 · you 80" in html     # Pricey Tech needs 100
    assert html.count("TOEFL min") == 2         # Cheap State needs exactly 80: no warning


def test_us_student_without_a_toefl_score_sees_no_toefl_warning(app):
    search_for(app, budget=100_000)
    assert "TOEFL" not in " ".join(rows(app))


# ---- Stars ----

def test_starring_a_program_counts_in_the_header_and_filters_the_table(app):
    find_programs(app)
    app.button(key="star-program:MID").click().run()
    assert "★ Starred 1" in header_pills(app)
    app.toggle(key="results_starred").set_value(True).run()
    assert row_names(app) == [MIDDLE]


def test_clicking_a_star_again_removes_it(app):
    find_programs(app)
    app.button(key="star-program:CHEAP").click().run()
    app.button(key="star-program:CHEAP").click().run()
    assert "★ Starred 0" in header_pills(app)


# ---- Downloads ----

def test_results_can_be_downloaded(app):
    find_programs(app)
    assert len(app.get("download_button")) == 1


# ---- Cost breakdown ----

def test_cost_breakdown_starts_with_the_first_program(app):
    find_programs(app)
    summary = metrics(app)
    assert summary["Tuition per year"] == "$10,000"
    assert summary["Living costs per year"] == "$15,000"
    assert summary["Stipend per year"] == "$0"
    assert summary["Total for 2 years"] == "$50,000"


def test_choosing_another_program_changes_the_breakdown_and_keeps_the_results(app):
    find_programs(app)
    app.selectbox(key="cost_choice").set_value(1).run()
    assert not app.exception
    assert metrics(app)["Tuition per year"] == "$20,000"
    assert metrics(app)["Total for 2 years"] == "$70,000"
    assert len(rows(app)) == 2           # the results did not disappear


def test_breakdown_of_a_funded_phd_shows_no_tuition_and_the_waiver_note(app):
    search_for(app, degree="PhD", gpa=3.9, budget=100_000)
    summary = metrics(app)
    assert summary["Tuition per year"] == "$0"
    assert summary["Stipend per year"] == "$30,000"
    assert "tuition is assumed to be waived" in captions(app)


# ---- Defect D-003: international students pay out-of-state tuition ----

def test_international_student_sees_the_out_of_state_cost_even_with_a_matching_home_state(app):
    app.selectbox(key="home_state").set_value("MI")
    search_for(app, budget=100_000, citizenship="International", toefl=100)
    # Cheap State University is in MI: in-state $10,000, out-of-state $20,000, living $15,000
    assert yearly_costs(app)[0] == 20000 + 15000
    assert "out-of-state" in rows(app)[0]
    assert metrics(app)["Tuition per year"] == "$20,000"     # the cost breakdown agrees


def test_us_student_with_the_same_home_state_still_gets_the_in_state_cost(app):
    search_for(app, budget=100_000)
    assert yearly_costs(app)[0] == 10000 + 15000
    assert metrics(app)["Tuition per year"] == "$10,000"


# ---- PhD funding screen ----

def test_phd_screen_lists_programs_by_stipend_with_funding_bars(app):
    search_for(app, degree="PhD", gpa=3.9)
    go(app, PHD)
    assert phd_names(app) == ["Funded University", "Partly Funded Institute"]   # $30,000, $10,000
    assert "background:#5E7D63" in phd_cards(app)[0]                          # fully funded bar
    assert "$30,000" in phd_cards(app)[0] and "Stipend covers living costs" in phd_cards(app)[0]
    assert "Stipend below living costs" in phd_cards(app)[1]


def test_phd_screen_ignores_the_budget(app):
    search_for(app, degree="PhD", gpa=3.9, budget=0)
    go(app, PHD)
    assert len(phd_cards(app)) == 2


def test_phd_screen_can_sort_by_school_name_and_show_starred_only(app):
    search_for(app, degree="PhD", gpa=3.9)
    go(app, PHD)
    app.selectbox(key="phd_sort").set_value("School name").run()
    assert phd_names(app) == ["Funded University", "Partly Funded Institute"]
    app.button(key="star-program:PHD2").click().run()
    app.toggle(key="phd_starred").set_value(True).run()
    assert phd_names(app) == ["Partly Funded Institute"]


def test_phd_screen_points_to_the_fellowships_and_opens_scholarships(app):
    search_for(app, degree="PhD", gpa=3.9)
    go(app, PHD)
    note = app.button(key="phd_fellowships")
    assert note.label == "1 fellowship or assistantship you can apply for →"
    note.click().run()
    assert app.radio(key="page").value == SCHOLARSHIPS
    assert scholarship_names(app) == ["Funded PhD Fellowship"]


def test_phd_screen_says_so_when_no_fellowship_matches(app):
    search_for(app, degree="PhD", gpa=3.4)                  # the fellowship needs 3.5
    go(app, PHD)
    assert app.button(key="phd_fellowships").disabled


# ---- Scholarships screen ----

def test_default_student_sees_only_the_open_scholarship_they_qualify_for(app):
    find_programs(app)
    go(app, SCHOLARSHIPS)
    assert scholarship_names(app) == ["Michigan Fee Waiver"]
    assert scholarship_amounts(app) == ["Non-monetary"]
    assert "1 you can apply for" in page_text(app)


def test_scholarship_amounts_are_not_called_yearly_and_the_note_explains(app):
    find_programs(app)
    go(app, SCHOLARSHIPS)
    assert "per year" not in page_text(app)
    assert "may be yearly or one-time" in page_text(app)


def test_expired_scholarships_are_hidden_unless_the_student_asks_for_everything(app):
    find_programs(app)
    go(app, SCHOLARSHIPS)
    assert "Expired Award" not in scholarship_names(app)
    app.radio(key="sch_show").set_value("Everything").run()
    assert scholarship_names(app) == ["Expired Award", "First-Gen Grant", "Funded PhD Fellowship",
                                      "Michigan Fee Waiver", "Women in STEM Award"]   # by deadline


def test_special_group_unlocks_more_scholarships_sorted_by_deadline(app):
    search_for(app, special=["first_gen"])
    go(app, SCHOLARSHIPS)
    assert scholarship_names(app) == ["First-Gen Grant", "Michigan Fee Waiver"]   # Nov 1, Jan 10
    assert scholarship_amounts(app)[0] == "$5,000"


def test_special_group_the_student_did_not_tick_stays_hidden(app):
    find_programs(app)
    go(app, SCHOLARSHIPS)
    assert "Women in STEM Award" not in scholarship_names(app)
    search_for(app, special=["women_stem"])
    go(app, SCHOLARSHIPS)
    assert "Women in STEM Award" in scholarship_names(app)


def test_phd_student_sees_the_phd_fellowship_but_not_ms_only_awards(app):
    search_for(app, degree="PhD", gpa=3.9)
    go(app, SCHOLARSHIPS)
    assert scholarship_names(app) == ["Funded PhD Fellowship"]


# Boundary-value analysis on the fellowship's minimum GPA of 3.5
@pytest.mark.parametrize("gpa, listed", [(3.45, False), (3.5, True), (3.55, True)])
def test_scholarship_minimum_gpa_boundary(app, gpa, listed):
    search_for(app, degree="PhD", gpa=gpa)
    go(app, SCHOLARSHIPS)
    assert ("Funded PhD Fellowship" in scholarship_names(app)) is listed


def test_international_student_does_not_see_us_only_fellowships(app):
    search_for(app, degree="PhD", gpa=3.9, citizenship="International", toefl=100)
    go(app, SCHOLARSHIPS)
    assert scholarship_names(app) == []
    assert "No scholarships match" in infos(app)


def test_a_kind_can_be_switched_off(app):
    find_programs(app)
    go(app, SCHOLARSHIPS)
    app.radio(key="sch_show").set_value("Everything").run()
    app.checkbox(key="type-scholarship").uncheck().run()      # the fee waiver counts as a scholarship
    assert scholarship_names(app) == ["Funded PhD Fellowship"]


def test_tracking_a_scholarship_adds_it_to_the_deadlines(app):
    find_programs(app)
    go(app, SCHOLARSHIPS)
    app.radio(key="sch_show").set_value("Everything").run()
    app.button(key="track-SCH4").click().run()
    assert app.button(key="track-SCH4").label == "✓ Tracking"
    go(app, DEADLINES)
    assert "Women in STEM Award" in deadline_names(app)


# ---- Deadlines screen ----

def test_deadlines_list_programs_and_scholarships_soonest_first(app):
    find_programs(app)
    go(app, DEADLINES)
    assert deadline_names(app) == ["Expired Award", CHEAP, "Michigan Fee Waiver", MIDDLE]
    assert days_left(app) == ["Passed", "12 days left", "78 days left", "83 days left"]


def test_a_deadline_within_14_days_gets_a_warning_banner(app):
    find_programs(app)
    go(app, DEADLINES)
    assert "1 deadline is coming up in the next 14 days" in banner(app)
    assert "Cheap State University" in banner(app)


# Boundary-value analysis on the warning window: Cheap State is 12 days away.
@pytest.mark.parametrize("window, warned", [(7, False), (14, True), (30, True)])
def test_the_warning_window_can_be_changed(app, window, warned):
    find_programs(app)
    go(app, DEADLINES)
    app.selectbox(key="warn_days").set_value(window).run()
    assert (banner(app) != "") is warned
    assert f"Within {window} days" in page_text(app)
    assert f"in {window} days" in header_pills(app)


def test_closed_items_are_marked_passed_and_left_out_of_the_calendar(app):
    search_for(app, budget=100_000)
    go(app, DEADLINES)
    names, labels = deadline_names(app), days_left(app)
    assert labels[names.index(PRICEY)] == "Passed"
    assert len(app.get("download_button")) == 1          # the calendar holds the open ones


def test_every_deadline_has_passed_after_the_last_one(app, monkeypatch):
    monkeypatch.setenv("GRADMATCH_TODAY", "2027-12-01")
    app.run()
    find_programs(app)
    go(app, DEADLINES)
    assert set(days_left(app)) == {"Passed"}
    assert "No open deadlines left" in infos(app)
    assert len(app.get("download_button")) == 0


def test_starred_only_on_the_deadlines_screen(app):
    find_programs(app)
    go(app, DEADLINES)
    app.button(key="star-program:MID").click().run()
    app.toggle(key="dl_starred").set_value(True).run()
    assert deadline_names(app) == [MIDDLE]


# ---- Your own deadlines ----

def add_deadline(at, name, day, link=""):
    at.text_input(key="custom_name").input(name)
    if day is not None:
        at.date_input(key="custom_date").set_value(day)
    at.text_input(key="custom_link").input(link)
    next(b for b in at.button if b.label == "Add deadline").click().run()
    assert not at.exception


def test_a_student_can_add_their_own_deadline(app):
    find_programs(app)
    go(app, DEADLINES)
    add_deadline(app, "Recommendation letters", date(2026, 10, 30), "https://example.edu/letters")
    assert deadline_names(app)[1] == "Recommendation letters"           # 6 days away, after the passed one
    assert "2 deadlines are coming up" in banner(app)
    assert "2 deadlines in 14 days" in header_pills(app)


def test_an_own_deadline_needs_a_name_and_a_date(app):
    go(app, DEADLINES)
    add_deadline(app, "", None)
    assert [e.value for e in app.error] == ["Name is required.", "Date must be a real date (YYYY-MM-DD)."]
    assert app.session_state["custom_deadlines"] == []


def test_two_own_deadlines_cannot_share_a_name(app):
    go(app, DEADLINES)
    add_deadline(app, "Transcripts", date(2026, 11, 20))
    add_deadline(app, "Transcripts", date(2026, 12, 1))
    assert "You already have a deadline with this name." in [e.value for e in app.error]
    assert len(app.session_state["custom_deadlines"]) == 1


# ---- Filters that leave nothing, and the other PhD options ----

def test_starred_only_with_nothing_starred_says_so(app):
    find_programs(app)
    app.toggle(key="results_starred").set_value(True).run()
    assert rows(app) == [] and "No programs match these filters." in infos(app)


def test_full_waiver_only_keeps_programs_that_pay_a_stipend(app, monkeypatch, tmp_path):
    from data_fixtures import PROGRAM_HEADER, PROGRAM_ROWS, write_fixture_data
    folder = write_fixture_data(tmp_path)
    no_stipend = "PHD3,Unfunded College,PhD in Computer Science,Computer Science,PhD,TX,9000,9000,5,3.60,,0.20,0,90,2027-02-01,https://example.edu/phd3"
    (folder / "programs.csv").write_text(PROGRAM_HEADER + "\n".join(PROGRAM_ROWS + [no_stipend]) + "\n")
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(folder))
    app = open_app()
    search_for(app, degree="PhD", gpa=3.9)
    go(app, PHD)
    assert "Unfunded College" in phd_names(app)
    app.checkbox(key="phd_full").check().run()
    assert phd_names(app) == ["Funded University", "Partly Funded Institute"]


def test_phd_screen_can_sort_by_money_left_after_living_costs(app):
    search_for(app, degree="PhD", gpa=3.9)
    go(app, PHD)
    app.selectbox(key="phd_sort").set_value("Money left after living costs").run()
    assert phd_names(app) == ["Funded University", "Partly Funded Institute"]
    assert "sorted by money left after living costs" in page_text(app)


def test_only_the_first_30_phd_cards_are_drawn(monkeypatch, tmp_path):
    from data_fixtures import PROGRAM_HEADER, write_fixture_data
    folder = write_fixture_data(tmp_path)
    many = [f"P{i:02d},PhD School {i:02d},PhD in Computer Science,Computer Science,PhD,MI,30000,30000,5,3.80,,0.10,{20000 + i},90,2027-01-05,https://example.edu/p{i}"
            for i in range(35)]
    (folder / "programs.csv").write_text(PROGRAM_HEADER + "\n".join(many) + "\n")
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(folder))
    app = open_app()
    search_for(app, degree="PhD", gpa=3.9)
    go(app, PHD)
    assert len(phd_cards(app)) == 30
    assert "Showing the first 30 of 35 programs." in captions(app)


def test_scholarships_can_show_only_the_starred_ones(app):
    find_programs(app)
    go(app, SCHOLARSHIPS)
    app.radio(key="sch_show").set_value("Everything").run()
    app.button(key="star-scholarship:SCH2").click().run()
    app.radio(key="sch_show").set_value("Starred only").run()
    assert scholarship_names(app) == ["First-Gen Grant"]
