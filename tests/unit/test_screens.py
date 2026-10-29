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
from gradmatch.deadlines import CustomDeadline
from gradmatch.components import face_svg
from gradmatch.components import PASSED, URGENT_BG, chance_badge, check_item, date_tile, funding_bar, official_link, tag
from gradmatch.fit import MATCH, REACH, SAFETY, UNKNOWN
from gradmatch.funding import FULLY_FUNDED, FUNDING_UNKNOWN, PARTIALLY_FUNDED, SELF_FUNDED
from gradmatch.screens import (DISCLAIMER, RESULTS_COLUMNS, cost_info_html, days_left_text, deadline_face,
                               deadline_row_html, due_text, faces_info_html, fellowships_note, funding_legend_html,
                               glance_html, header_pills_html, item_kind, item_name, page_title_html,
                               phd_card_html, phd_checklist, profile_summary_html, program_row_html,
                               rate_note, results_header_html, score_ranges, scholarship_amount_html,
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
                 "in-state", "$15,000", "$12,000", '<div class="gm-money" data-label="Est. yearly">$27,000</div>',
                 chance_badge(SAFETY)]:
        assert text in html


def test_program_row_uses_the_out_of_state_rate_for_another_state():
    html = program_row_html(result(), "OH", 12000)
    assert "out-of-state" in html and '<div data-label="Tuition">$30,000</div>' in html


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


def test_a_fee_waiver_is_shown_as_a_scholarship_and_not_qualifying_has_no_tick():
    html = scholarship_info_html(make_scholarship(type="fee_waiver"), False)
    assert tag("SCHOLARSHIP", "scholarship") in html and "You qualify" not in html


def test_an_assistantship_has_its_own_tag():
    html = scholarship_info_html(make_scholarship(type="assistantship"), True)
    assert tag("ASSISTANTSHIP", "assistantship") in html


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


CUSTOM = CustomDeadline("My own reminder", date(2026, 11, 2))


def test_names_and_kinds_for_each_kind_of_item():
    assert item_name(make_program()) == "Test University – MS in Computer Science"
    assert item_kind(make_program()) == "MS Computer Science"
    assert item_name(make_scholarship()) == "Test Fellowship"
    assert item_kind(make_scholarship()) == "Fellowship application"
    assert item_name(CUSTOM) == "My own reminder" and item_kind(CUSTOM) == "Your own deadline"


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
    html = deadline_row_html(CUSTOM, TODAY)
    assert "Your own deadline</div>" in html and "Official site" not in html


def test_glance_card():
    html = glance_html({"within_window": 2, "within_90": 4, "later": 1, "passed": 1})
    assert '<span>Within 14 days</span><b class="gm-urgent">2</b>' in html
    assert '<span>Within 90 days</span><b class="">4</b>' in html
    assert '<span>Passed</span><b class="gm-sub">1</b>' in html
    assert "Within 7 days" in glance_html({"within_window": 0, "within_90": 0, "later": 0, "passed": 0}, 7)


def test_a_custom_deadline_shows_its_note_as_the_kind():
    assert item_kind(CustomDeadline("Letters", date(2026, 11, 2), note="Ask Prof. Lee")) == "Ask Prof. Lee"


# ---- The fellowships line on the PhD screen: 0, 1 and many ----

@pytest.mark.parametrize("count, text", [
    (0, "No fellowships or assistantships match your profile yet"),
    (1, "1 fellowship or assistantship you can apply for →"),
    (4, "4 fellowships and assistantships you can apply for →"),
])
def test_fellowships_note(count, text):
    assert fellowships_note(count) == text


# ---- SAT and ACT on a college row: both ends of a range are needed ----

def test_a_college_row_shows_the_middle_half_of_sat_and_act():
    scores = dict(degree="BS", sat_25=1100, sat_75=1300, act_25=24, act_75=31)
    assert score_ranges(make_program(**scores)) == "SAT 1100–1300 · ACT 24–31"
    row = program_row_html(result(**scores), "MI", 15000)
    assert "SAT 1100–1300 · ACT 24–31 (mid 50%) · " in row


@pytest.mark.parametrize("changes", [dict(sat_25=1100), dict(sat_75=1300), dict(act_25=24), dict(act_75=31)])
def test_half_a_test_score_range_is_not_shown(changes):
    assert score_ranges(make_program(**changes)) == ""


def test_only_the_published_test_is_shown():
    assert score_ranges(make_program(act_25=24, act_75=31)) == "ACT 24–31"
    assert "mid 50%" not in program_row_html(result(), "MI", 15000)


# ---- Exact text of the fixed info cards ----
# Why: these explain the numbers to the student, so a changed or lost sentence should fail a test.

def test_cost_info_card_is_exact():
    assert cost_info_html() == (
        '<div class="gm-soft"><div class="gm-label">How cost is worked out</div>'
        "<p>In-state or out-of-state tuition (international students always pay out-of-state), "
        "plus the living cost of the school's state, minus any stipend. A funded PhD is assumed "
        "to waive tuition.</p></div>")


def test_faces_card_is_exact():
    rows = "".join(f'<div class="gm-face-row">{face_svg(label)}<div><b>{label}</b> '
                   f'<span class="gm-sub">{meaning}</span></div></div>'
                   for label, meaning in ((SAFETY, "above the program's typical range"),
                                          (MATCH, "within the typical range"),
                                          (REACH, "below the typical range"),
                                          (UNKNOWN, "the school does not publish the numbers")))
    assert faces_info_html() == f'<div class="gm-card"><div class="gm-label">What the faces mean</div>{rows}</div>'


def test_funding_legend_is_exact():
    assert funding_legend_html() == (
        '<div class="gm-legend"><b>Funding level</b>'
        '<span><i style="background:#5E7D63"></i> Fully funded: stipend covers living costs</span>'
        '<span><i style="background:#9DB8AC"></i> Partly funded</span>'
        '<span><i style="background:#E2DDD0"></i> Not funded or not published</span></div>')


def test_glance_card_is_exact():
    assert glance_html({"within_window": 1, "within_90": 2, "later": 3, "passed": 4}) == (
        '<div class="gm-soft"><div class="gm-serif gm-name">At a glance</div>'
        '<div class="gm-glance-row"><span>Within 14 days</span><b class="gm-urgent">1</b></div>'
        '<div class="gm-glance-row"><span>Within 90 days</span><b class="">2</b></div>'
        '<div class="gm-glance-row"><span>Later</span><b class="">3</b></div>'
        '<div class="gm-glance-row"><span>Passed</span><b class="gm-sub">4</b></div></div>')


# ---- Deadline rows: boundary values on the warning window ----

def due_in(days):
    return CustomDeadline("Item", date.fromordinal(TODAY.toordinal() + days))


@pytest.mark.parametrize("days, urgent", [(-1, False), (0, True), (14, True), (15, False)])
def test_deadline_row_tints_dates_inside_the_window(days, urgent):
    html = deadline_row_html(due_in(days), TODAY)
    assert (URGENT_BG in html) is urgent


@pytest.mark.parametrize("days", [0, 15])
def test_only_passed_rows_are_struck_through(days):
    assert '<div class="gm-name">Item</div>' in deadline_row_html(due_in(days), TODAY)


def test_deadline_row_uses_the_chosen_window_for_the_face():
    html = deadline_row_html(due_in(10), TODAY, 7)
    assert chance_badge(MATCH, "10 days left") in html and URGENT_BG not in html


# ---- Due text and amounts: more boundaries ----

@pytest.mark.parametrize("days, text", [(0, "Due today"), (1, "Due in 1 day"), (2, "Due in 2 days")])
def test_due_text_near_today(days, text):
    assert due_text(date.fromordinal(TODAY.toordinal() + days), TODAY) == f'<span class="gm-urgent">{text}</span>'


def test_scholarship_amount_follows_the_default_and_the_chosen_window():
    in_15 = make_scholarship(deadline=date(2026, 11, 13), amount=1)
    assert '<div class="gm-money gm-big">$1</div>' in scholarship_amount_html(in_15, TODAY)
    assert "Due Nov 13, 2026" in scholarship_amount_html(in_15, TODAY)
    in_10 = make_scholarship(deadline=date(2026, 11, 8))
    assert "Due Nov 8, 2026" in scholarship_amount_html(in_10, TODAY, 7)


def test_scholarship_tags_are_side_by_side():
    html = scholarship_info_html(make_scholarship(), True)
    assert f'<div>{tag("FELLOWSHIP", "fellowship")} {tag("✓ You qualify", "qualify")}</div>' in html


# ---- PhD cards and program rows: exact joins ----

def test_a_one_dollar_stipend_still_counts_as_a_stipend():
    lines = phd_checklist(make_program(degree="PhD", stipend=1), PARTIALLY_FUNDED)
    assert lines[0] == ("Tuition waived with funding", True)


def test_phd_checklist_lines_are_side_by_side():
    html = phd_card_html(result(degree="PhD", stipend=40000.0, funding=FULLY_FUNDED))
    assert "</li><li>" in html and "</li>XX" not in html


def test_toefl_warning_sits_after_the_link():
    row = program_row_html(result(min_toefl=100), "MI", 15000, student_toefl=80)
    assert f'{official_link("https://example.edu/ms-cs")} {tag("TOEFL min 100 · you 80", "pending")}' in row


def test_row_cells_are_side_by_side():
    row = program_row_html(result(), "MI", 15000)
    assert '<div class="gm-money" data-label="Est. yearly">$27,000</div><div><span class="gm-badge"' in row


def test_each_number_in_a_row_is_labelled_for_phones():
    row = program_row_html(result(), "MI", 15000)
    for label in ("State", "Tuition", "Living", "Est. yearly"):
        assert f'data-label="{label}"' in row
