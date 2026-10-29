"""Unit tests for screens.py (rows and cards of the new design).

In plain words: each function builds the HTML for one row or card. We give it small made-up
programs and scholarships and check the exact words, numbers and badges it shows.
Techniques: boundary values (days left at -1, 0, 1, 14, 15, 90, 91; stipend None / 0 / above
the living cost), equivalence classes (program, scholarship, other dated item) and a decision
table for the PhD checklist.
"""
from datetime import date

import pytest

from conftest import make_profile, make_program, make_scholarship
from gradmatch.components import PASSED, chance_badge, check_item, date_tile, funding_bar, official_link, tag
from gradmatch.fit import MATCH, REACH, SAFETY, UNKNOWN
from gradmatch.funding import FULLY_FUNDED, FUNDING_UNKNOWN, PARTIALLY_FUNDED, SELF_FUNDED
from gradmatch.screens import (DISCLAIMER, RESULTS_COLUMNS, cost_info_html, count_deadlines, days_left_text, deadline_face,
                               deadline_row_html, due_text, faces_info_html, funding_legend_html,
                               glance_html, header_pills_html, item_kind, item_name, page_title_html,
                               phd_card_html, phd_checklist, profile_summary_html, program_row_html,
                               rate_note, results_header_html, scholarship_amount_html,
                               scholarship_info_html)
from gradmatch.search import ProgramResult

pytestmark = pytest.mark.unit

TODAY = date(2026, 10, 29)


def result(fit=MATCH, funding=SELF_FUNDED, yearly=27000.0, **changes):
    return ProgramResult(program=make_program(**changes), yearly_cost=yearly, total_cost=yearly * 2,
                         fit=fit, funding=funding)


# ---- Header and titles ----

@pytest.mark.parametrize("urgent, text", [(0, "0 deadlines"), (1, "1 deadline"), (2, "2 deadlines")])
def test_header_pills(urgent, text):
    html = header_pills_html(6, urgent)
    assert "★ Starred 6" in html and f"⏰ {text} in 14 days" in html


def test_header_pills_show_the_chosen_window():
    assert "in 7 days" in header_pills_html(0, 0, 7)


def test_page_title_has_one_accent_word_and_escapes():
    html = page_title_html("Master's programs that", "fit you")
    assert html == ('<h1 class="gm-serif">Master&#x27;s programs that '
                    '<span class="gm-title-accent">fit you</span></h1>')
    assert "&lt;b&gt;" in page_title_html("<b>", "x")


# ---- Results table ----

def test_results_header_has_the_six_columns_in_order():
    html = results_header_html()
    assert "".join(f"<div>{c}</div>" for c in RESULTS_COLUMNS) in html
    assert RESULTS_COLUMNS == ("Program", "State", "Tuition", "Living", "Est. yearly", "Chance")


@pytest.mark.parametrize("home, note", [("MI", "in-state"), ("OH", "out-of-state"), (None, "out-of-state")])
def test_rate_note(home, note):
    assert rate_note(make_program(state="MI"), home) == note


def test_program_row_shows_every_column():
    html = program_row_html(result(fit=SAFETY), "MI", 12000)
    for text in ["Test University", "MS in Computer Science", "Official site ↗", ">MI <",
                 "in-state", "$15,000", "$12,000", '<div class="gm-money">$27,000</div>',
                 chance_badge(SAFETY)]:
        assert text in html


def test_program_row_uses_the_out_of_state_rate_for_another_state():
    html = program_row_html(result(), "OH", 12000)
    assert "out-of-state" in html and "<div>$30,000</div>" in html


def test_program_row_shows_a_toefl_warning_only_when_below_the_minimum():
    assert tag("TOEFL min 80 · you 70", "pending") in program_row_html(result(), "MI", 1, 70)
    assert "TOEFL" not in program_row_html(result(), "MI", 1, 100)
    assert "TOEFL" not in program_row_html(result(), "MI", 1)


def test_program_row_without_a_safe_website_has_no_link_and_escapes_names():
    html = program_row_html(result(website="javascript:x", university="<b>U</b>"), "MI", 1)
    assert "Official site" not in html and "&lt;b&gt;U&lt;/b&gt;" in html


def test_info_cards_and_disclaimer():
    assert "international students always pay out-of-state" in cost_info_html()
    faces = faces_info_html()
    for label in (SAFETY, MATCH, REACH, UNKNOWN):
        assert f"<b>{label}</b>" in faces
    assert "not a promise of admission" in DISCLAIMER


# ---- PhD cards: decision table for the checklist ----
# stipend   | funding      | waiver line | living line
# None      | unknown      | not published (!) | not published (!)
# 0         | self-funded  | tuition charged (!) | none listed (!)
# > 0       | partly       | waived (✓) | below living (!)
# > 0       | fully        | waived (✓) | covers living (✓)

@pytest.mark.parametrize("stipend, funding, waiver, living", [
    (None, FUNDING_UNKNOWN, ("Tuition waiver not published", False), ("Stipend not published", False)),
    (0, SELF_FUNDED, ("No stipend listed, so tuition is charged", False), ("No stipend listed", False)),
    (10000, PARTIALLY_FUNDED, ("Tuition waived with funding", True), ("Stipend below living costs", False)),
    (40000, FULLY_FUNDED, ("Tuition waived with funding", True), ("Stipend covers living costs", True)),
])
def test_phd_checklist(stipend, funding, waiver, living):
    lines = phd_checklist(make_program(degree="PhD", stipend=stipend), funding)
    assert lines == [waiver, living, ("Health insurance: see program page", False)]


def test_phd_card_shows_bar_school_stipend_badge_and_checklist():
    html = phd_card_html(result(fit=REACH, funding=FULLY_FUNDED, degree="PhD", stipend=38000))
    assert html.startswith(funding_bar(FULLY_FUNDED))
    assert "Test University" in html and official_link("https://example.edu/ms-cs") in html
    assert '<div class="gm-stipend-amount">$38,000</div>' in html and chance_badge(REACH) in html
    assert check_item("Stipend covers living costs", True) in html


def test_phd_card_with_no_published_stipend_says_so():
    html = phd_card_html(result(fit=UNKNOWN, funding=FUNDING_UNKNOWN, degree="PhD", stipend=None))
    assert '<div class="gm-stipend-amount">Not published</div>' in html


def test_funding_legend_has_three_levels():
    html = funding_legend_html()
    assert "Fully funded" in html and "Partly funded" in html and "Not funded or not published" in html


# ---- Scholarship cards ----

def test_scholarship_info_shows_type_qualify_name_eligibility_and_link():
    html = scholarship_info_html(make_scholarship(), True)
    assert tag("FELLOWSHIP", "fellowship") in html and tag("✓ You qualify", "qualify") in html
    assert "Test Fellowship" in html and "PhD · Any field" in html
    assert official_link("https://example.org/fellowship") in html


def test_scholarship_info_without_qualifying_and_with_an_unusual_type():
    html = scholarship_info_html(make_scholarship(type="fee_waiver"), False)
    assert tag("FEE WAIVER", "optional") in html and "You qualify" not in html


@pytest.mark.parametrize("deadline, text", [
    (date(2026, 10, 28), "Closed Oct 28, 2026"),     # yesterday
    (date(2026, 10, 29), "Due today"),               # 0 days
    (date(2026, 10, 30), "Due in 1 day"),            # 1 day
    (date(2026, 11, 12), "Due in 14 days"),          # 14 days: still urgent
    (date(2026, 11, 13), "Due Nov 13, 2026"),        # 15 days: not urgent
])
def test_due_text_boundaries(deadline, text):
    assert text in due_text(deadline, TODAY)


def test_due_text_urgency_follows_the_window_and_is_highlighted():
    assert "gm-urgent" in due_text(date(2026, 11, 3), TODAY, 7)       # 5 days, 7-day window
    assert "gm-urgent" not in due_text(date(2026, 11, 13), TODAY, 7)  # 15 days


@pytest.mark.parametrize("amount, shown", [(30000, "$30,000"), (0, "Non-monetary")])
def test_scholarship_amount(amount, shown):
    html = scholarship_amount_html(make_scholarship(amount=amount), TODAY)
    assert f'<div class="gm-money gm-big">{shown}</div>' in html and "Due Dec 5, 2026" in html


def test_profile_summary():
    html = profile_summary_html(make_profile())
    assert "GPA 3.50 · MS · Computer Science · MI resident" in html


# ---- Deadline rows: boundary values on days left ----

@pytest.mark.parametrize("days, face", [(-1, PASSED), (0, REACH), (14, REACH), (15, MATCH),
                                        (90, MATCH), (91, SAFETY)])
def test_deadline_face_boundaries(days, face):
    assert deadline_face(days) == face


def test_deadline_face_follows_the_window():
    assert deadline_face(10, 7) == MATCH and deadline_face(7, 7) == REACH


@pytest.mark.parametrize("days, text", [(-3, "Passed"), (0, "Due today"), (1, "1 day left"), (9, "9 days left")])
def test_days_left_text(days, text):
    assert days_left_text(days) == text


class Custom:
    """Any other dated item, like a deadline the student adds: a name, a date and a link."""
    name = "My own reminder"
    deadline = date(2026, 11, 2)
    website = ""


def test_names_and_kinds_for_each_kind_of_item():
    assert item_name(make_program()) == "Test University – MS in Computer Science"
    assert item_kind(make_program()) == "MS Computer Science"
    assert item_name(make_scholarship()) == "Test Fellowship"
    assert item_kind(make_scholarship()) == "Fellowship application"
    assert item_name(Custom()) == "My own reminder" and item_kind(Custom()) == "Your own deadline"


def test_deadline_row_for_an_urgent_scholarship():
    html = deadline_row_html(make_scholarship(deadline=date(2026, 11, 7)), TODAY)
    assert date_tile(date(2026, 11, 7), True) in html
    assert chance_badge(REACH, "9 days left") in html
    assert official_link("https://example.org/fellowship") in html


def test_deadline_row_for_a_later_program_and_a_passed_one():
    later = deadline_row_html(make_program(application_deadline=date(2027, 1, 15)), TODAY)
    assert date_tile(date(2027, 1, 15), False) in later and chance_badge(MATCH, "78 days left") in later
    passed = deadline_row_html(make_program(application_deadline=date(2026, 10, 15)), TODAY)
    assert 'class="gm-name gm-passed"' in passed and chance_badge(PASSED, "Passed") in passed


def test_deadline_row_without_a_link():
    html = deadline_row_html(Custom(), TODAY)
    assert "Your own deadline</div>" in html and "Official site" not in html


def test_glance_card():
    html = glance_html({"within_window": 2, "within_90": 4, "later": 1, "passed": 1})
    assert '<span>Within 14 days</span><b class="gm-urgent">2</b>' in html
    assert '<span>Within 90 days</span><b class="">4</b>' in html
    assert '<span>Passed</span><b class="gm-sub">1</b>' in html
    assert "Within 7 days" in glance_html({"within_window": 0, "within_90": 0, "later": 0, "passed": 0}, 7)


# ---- 'At a glance' counts: boundary values ----

def dated(day):
    item = Custom()
    item.deadline = day
    return item


def test_count_deadlines_boundaries():
    days = [-1, 0, 14, 15, 90, 91]
    items = [dated(date.fromordinal(TODAY.toordinal() + d)) for d in days]
    assert count_deadlines(items, TODAY) == {"within_window": 2, "within_90": 4, "later": 1, "passed": 1}


def test_count_deadlines_follows_the_window_and_handles_nothing():
    items = [dated(date.fromordinal(TODAY.toordinal() + d)) for d in (5, 10)]
    assert count_deadlines(items, TODAY, 7)["within_window"] == 1
    assert count_deadlines([], TODAY) == {"within_window": 0, "within_90": 0, "later": 0, "passed": 0}
