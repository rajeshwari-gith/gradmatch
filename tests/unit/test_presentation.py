"""Unit tests for presentation.py.

Techniques: boundary-value analysis on the deadline wording (closed, due
today, 1 day, 14, 15 days), equivalence partitioning on website links, and
checks that text from the data files can never break out into HTML.
"""
from datetime import date

import pytest

from conftest import make_program, make_scholarship
from gradmatch.deadlines import CLOSED, LATER, SOON, URGENT
from gradmatch.fit import MATCH, REACH, SAFETY, UNKNOWN
from gradmatch.funding import FULLY_FUNDED, FUNDING_UNKNOWN, PARTIALLY_FUNDED, SELF_FUNDED
from gradmatch.presentation import (DEADLINE_COLORS, ESTIMATE_NOTE, FIT_COLORS, FUNDING_COLORS,
                                    BLUE, GREEN, GREY, YELLOW, chip, deadline_item_html, deadline_label,
                                    eligibility_summary, format_date, money, percent,
                                    result_card_html, safe_link, scholarship_card_html,
                                    special_label, toefl_warning)
from gradmatch.search import ProgramResult

pytestmark = pytest.mark.unit

# In plain words: the cards are HTML text, so we test the text directly without opening a browser.
# We check the wording of deadlines, that colours follow the labels, that website links are safe,
# and that odd characters in the data can never break out of the page.

TODAY = date(2026, 10, 24)


def make_result(fit=MATCH, funding=SELF_FUNDED, **program_changes) -> ProgramResult:
    return ProgramResult(program=make_program(**program_changes), yearly_cost=27000.0,
                         total_cost=54000.0, fit=fit, funding=funding)


# ---- number and date formatting ----

@pytest.mark.parametrize("amount, text", [(0, "$0"), (999, "$999"), (27000, "$27,000"),
                                          (1234567.4, "$1,234,567")])
def test_money(amount, text):
    assert money(amount) == text


@pytest.mark.parametrize("rate, text", [(0, "0%"), (0.2, "20%"), (0.704, "70%"), (1, "100%")])
def test_percent(rate, text):
    assert percent(rate) == text


def test_format_date_has_no_leading_zero():
    assert format_date(date(2026, 12, 5)) == "Dec 5, 2026"
    assert format_date(date(2027, 2, 1)) == "Feb 1, 2027"


# ---- deadline wording: boundary-value analysis ----

@pytest.mark.parametrize("deadline, status, text", [
    (date(2026, 10, 23), CLOSED, "Closed Oct 23, 2026"),             # yesterday
    (date(2026, 10, 24), URGENT, "Oct 24, 2026 · due today"),        # 0 days
    (date(2026, 10, 25), URGENT, "Oct 25, 2026 · 1 day left"),       # 1 day
    (date(2026, 11, 7), URGENT, "Nov 7, 2026 · 14 days left"),       # 14 days
    (date(2026, 11, 8), SOON, "Nov 8, 2026 · 15 days left"),         # 15 days
    (date(2026, 11, 23), SOON, "Nov 23, 2026 · 30 days left"),       # 30 days
    (date(2026, 11, 24), LATER, "Nov 24, 2026 · 31 days left"),      # 31 days
])
def test_deadline_label(deadline, status, text):
    assert deadline_label(deadline, TODAY) == (status, text)


# ---- websites: only normal web addresses become links ----
# Why: a link like "javascript:..." could run code in the page. Only http(s) is allowed.

@pytest.mark.parametrize("url", ["https://example.edu/ms", "http://example.edu", "  https://a.edu  "])
def test_normal_web_addresses_are_links(url):
    assert safe_link(url) == url.strip()


@pytest.mark.parametrize("url", ["", "   ", "javascript:alert(1)", "ftp://example.edu", "example.edu", None])
def test_other_text_is_not_linked(url):
    assert safe_link(url) is None


# ---- colors ----

def test_every_label_has_a_color():
    assert set(FIT_COLORS) == {SAFETY, MATCH, REACH, UNKNOWN}
    assert set(FUNDING_COLORS) == {FULLY_FUNDED, PARTIALLY_FUNDED, SELF_FUNDED, FUNDING_UNKNOWN}
    assert set(DEADLINE_COLORS) == {URGENT, SOON, LATER, CLOSED}


def test_safety_is_green():
    assert FIT_COLORS[SAFETY] == GREEN


# ---- the result card ----

def test_card_shows_the_important_facts():
    html = result_card_html(make_result(fit=SAFETY, funding=FULLY_FUNDED), TODAY)
    for text in ["Test University – MS in Computer Science", "$27,000", "$54,000", "2 yr total",
                 "3.40", "40%", "Safety", "Fully Funded", "Jan 15, 2027 · 83 days left",
                 "MS · Computer Science · MI"]:
        assert text in html


def test_card_stripe_color_follows_the_fit():
    for fit, color in FIT_COLORS.items():
        assert f"border-left-color:{color}" in result_card_html(make_result(fit=fit), TODAY)


def test_card_links_to_the_official_website():
    html = result_card_html(make_result(), TODAY)
    assert 'href="https://example.edu/ms-cs"' in html
    assert 'rel="noopener noreferrer"' in html


def test_card_without_a_safe_website_has_no_link():
    html = result_card_html(make_result(website="javascript:alert(1)"), TODAY)
    assert "<a " not in html and "javascript" not in html


def test_text_from_the_data_cannot_inject_html():
    evil = '<script>alert("x")</script>'
    html = result_card_html(make_result(university=evil, program_name=evil, state=evil), TODAY)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_quote_in_a_website_cannot_break_out_of_the_link():
    html = result_card_html(make_result(website='https://a.edu/"onmouseover="x'), TODAY)
    assert 'href="https://a.edu/&quot;onmouseover=&quot;x"' in html


def test_chip_escapes_its_text():
    assert chip("<b>", GREEN) == f'<span class="gm-chip" style="--chip:{GREEN}">&lt;b&gt;</span>'


# ---- TOEFL warning: boundary-value analysis around the program's minimum ----

@pytest.mark.parametrize("student, text", [
    (84, "TOEFL min 85 · you 84"),    # one point below the minimum
    (0, "TOEFL min 85 · you 0"),
])
def test_toefl_below_the_minimum_gives_a_warning(student, text):
    assert toefl_warning(85, student) == text


@pytest.mark.parametrize("student", [85, 86, 120])
def test_toefl_at_or_above_the_minimum_gives_no_warning(student):
    assert toefl_warning(85, student) is None


def test_no_warning_when_the_student_has_no_toefl_score():
    assert toefl_warning(85, None) is None


def test_no_warning_when_the_program_has_no_minimum():
    assert toefl_warning(None, 60) is None


def test_card_shows_the_toefl_warning_chip_in_yellow():
    html = result_card_html(make_result(min_toefl=85), TODAY, student_toefl=80)
    assert chip("TOEFL min 85 · you 80", YELLOW) in html


@pytest.mark.parametrize("toefl", [None, 85, 100])
def test_card_has_no_toefl_chip_when_there_is_nothing_to_warn_about(toefl):
    assert "TOEFL" not in result_card_html(make_result(min_toefl=85), TODAY, student_toefl=toefl)


def test_card_without_a_toefl_argument_has_no_toefl_chip():
    assert "TOEFL" not in result_card_html(make_result(min_toefl=85), TODAY)


# ---- Estimates are labeled ----
# Why: our GPA and acceptance numbers are estimates, and the card must say so honestly.

def test_gpa_and_acceptance_rate_are_labeled_as_estimates():
    html = result_card_html(make_result(), TODAY)
    assert "avg GPA (est.)" in html
    assert "accepted (est.)" in html


def test_the_estimate_note_mentions_estimates_and_mandatory_fees():
    assert "estimates" in ESTIMATE_NOTE
    assert "mandatory student fees" in ESTIMATE_NOTE


# ---- Scholarship eligibility summary ----

def test_summary_of_a_simple_fellowship():
    assert eligibility_summary(make_scholarship()) == (
        "PhD · Any field · GPA 3.00+ · U.S. citizens / permanent residents · Any state")


def test_summary_with_no_minimum_gpa_leaves_the_gpa_out():
    assert "GPA" not in eligibility_summary(make_scholarship(min_gpa=0.0))


def test_summary_lists_fields_states_and_special_groups():
    s = make_scholarship(degree_levels=("MS", "PhD"), fields=("Computer Science", "Data Science"),
                         citizenship=("Any",), states=("MI", "OH"),
                         special=("first_gen", "women_stem"))
    assert eligibility_summary(s) == (
        "MS, PhD · Computer Science, Data Science · GPA 3.00+ · Any citizenship · "
        "Residents of MI, OH · For first-generation students, women in STEM")


@pytest.mark.parametrize("tag, label", [("first_gen", "first-generation students"),
                                        ("mcnair_scholar", "McNair Scholars"),
                                        ("some_new_tag", "some new tag")])
def test_special_labels(tag, label):
    assert special_label(tag) == label


# ---- Scholarship card ----

def test_scholarship_card_shows_the_important_facts():
    html = scholarship_card_html(make_scholarship(), TODAY)
    for text in ["Test Fellowship", "$30,000", "award", "Fellowship",
                 "Dec 5, 2026 · 42 days left", "PhD · Any field"]:
        assert text in html
    assert 'href="https://example.org/fellowship"' in html


def test_scholarship_with_no_money_says_non_monetary():
    html = scholarship_card_html(make_scholarship(amount=0, type="fee_waiver"), TODAY)
    assert "Non-monetary" in html and "$0" not in html
    assert "Fee Waiver" in html


@pytest.mark.parametrize("deadline, color", [
    (date(2026, 10, 1), "#8A94A6"),      # closed
    (date(2026, 10, 30), "#F0705F"),                   # urgent: 6 days
    (date(2026, 11, 15), "#F5C469"),                   # soon: 22 days
    (date(2027, 3, 1), BLUE),                          # later
])
def test_scholarship_stripe_color_follows_the_deadline(deadline, color):
    assert f"border-left-color:{color}" in scholarship_card_html(make_scholarship(deadline=deadline), TODAY)


def test_scholarship_text_cannot_inject_html():
    evil = "<img src=x onerror=alert(1)>"
    html = scholarship_card_html(make_scholarship(name=evil, fields=(evil,), states=(evil,)), TODAY)
    assert "<img" not in html and "&lt;img" in html


def test_scholarship_with_an_unsafe_website_is_not_linked():
    html = scholarship_card_html(make_scholarship(website="javascript:alert(1)"), TODAY)
    assert "<a " not in html


# ---- Deadline rows ----

def test_deadline_row_for_a_program():
    html = deadline_item_html(make_program(), TODAY)
    assert "Test University – MS in Computer Science" in html
    assert chip("Program", BLUE) in html
    assert "Jan 15, 2027 · 83 days left" in html


def test_deadline_row_for_a_scholarship():
    html = deadline_item_html(make_scholarship(), TODAY)
    assert "Test Fellowship" in html
    assert chip("Scholarship", BLUE) in html
    assert "Dec 5, 2026 · 42 days left" in html


def test_deadline_row_escapes_the_name():
    html = deadline_item_html(make_scholarship(name="<b>x</b>"), TODAY)
    assert "<b>" not in html


def test_scholarship_card_does_not_claim_the_award_is_per_year():
    """Some awards are one-time totals, so the card only says 'award'."""
    assert "per year" not in scholarship_card_html(make_scholarship(), TODAY)


# ---- Values that are not published (rows from official government data) ----
# Why: a missing number is shown as "n/a" and never as a made-up value.

UNPUBLISHED = dict(avg_gpa=None, acceptance_rate=None, stipend=None, application_deadline=None,
                   source="ipeds")


def test_unpublished_values_show_n_a_and_are_not_called_estimates():
    html = result_card_html(make_result(fit=UNKNOWN, funding=FUNDING_UNKNOWN, **UNPUBLISHED), TODAY)
    assert html.count(">n/a<") == 2
    assert "(est.)" not in html


def test_gpa_and_acceptance_rate_stay_estimates_even_on_a_verified_row():
    html = result_card_html(make_result(source="official-page"), TODAY)
    assert "avg GPA (est.)" in html and "accepted (est.)" in html


def test_a_missing_deadline_says_to_check_the_program_page():
    html = result_card_html(make_result(application_deadline=None), TODAY)
    assert chip("Deadline: check program page", GREY) in html
    assert "days left" not in html


def test_unknown_fit_and_funding_are_grey():
    html = result_card_html(make_result(fit=UNKNOWN, funding=FUNDING_UNKNOWN), TODAY)
    assert chip(UNKNOWN, GREY) in html and chip(FUNDING_UNKNOWN, GREY) in html
    assert f"border-left-color:{GREY}" in html


@pytest.mark.parametrize("source, text", [("ipeds", "Official school data"),
                                          ("official-page", "Verified on official page")])
def test_card_says_where_official_rows_come_from(source, text):
    assert text in result_card_html(make_result(source=source), TODAY)


def test_estimate_rows_have_no_source_chip():
    html = result_card_html(make_result(), TODAY)
    assert "Official school data" not in html and "Verified" not in html


def test_the_estimate_note_explains_n_a():
    assert "n/a" in ESTIMATE_NOTE


# ---- Test scores on a college card ----

def test_card_shows_the_middle_half_of_sat_and_act_when_published():
    html = result_card_html(make_result(sat_25=1110, sat_75=1350, act_25=24, act_75=31), TODAY)
    assert "1110–1350" in html and "SAT mid 50%" in html
    assert "24–31" in html and "ACT mid 50%" in html


def test_card_has_no_test_score_stats_when_not_published():
    html = result_card_html(make_result(), TODAY)
    assert "SAT" not in html and "ACT" not in html


# ---- Exact pieces of each card ----
# Why: found by mutation testing. The earlier checks looked for words anywhere in the card, so a
# changed label, a missing colour or text glued between pieces went unnoticed. These compare the
# exact HTML piece the card must contain.

from gradmatch.presentation import stat


def test_card_stats_are_exact_and_side_by_side():
    html = result_card_html(make_result(), TODAY)
    assert stat("$27,000", "per year") + stat("$54,000", "2 yr total") in html


def test_card_chips_are_exact_and_side_by_side():
    html = result_card_html(make_result(fit=SAFETY, funding=FULLY_FUNDED), TODAY)
    status, text = deadline_label(date(2027, 1, 15), TODAY)
    assert (chip(SAFETY, FIT_COLORS[SAFETY]) + chip(FULLY_FUNDED, FUNDING_COLORS[FULLY_FUNDED])
            + chip(text, DEADLINE_COLORS[status])) in html


def test_card_without_a_safe_link_shows_the_title_as_plain_text():
    html = result_card_html(make_result(website="not a link"), TODAY)
    assert '<span class="gm-title">Test University – MS in Computer Science</span>' in html


def test_test_score_stats_are_exact():
    html = result_card_html(make_result(sat_25=1110, sat_75=1350, act_25=24, act_75=31), TODAY)
    assert stat("1110–1350", "SAT mid 50%") + stat("24–31", "ACT mid 50%") in html


@pytest.mark.parametrize("changes", [dict(sat_25=1100), dict(sat_75=1300), dict(act_25=24), dict(act_75=31)])
def test_half_a_test_score_range_is_not_shown(changes):
    html = result_card_html(make_result(**changes), TODAY)
    assert "mid 50%" not in html and "None" not in html


def test_scholarship_card_pieces_are_exact():
    html = scholarship_card_html(make_scholarship(), TODAY)
    status, text = deadline_label(date(2026, 12, 5), TODAY)
    assert stat("$30,000", "award") in html
    assert chip("Fellowship", BLUE) + chip(text, DEADLINE_COLORS[status]) in html


@pytest.mark.parametrize("amount, shown", [(0, "Non-monetary"), (1, "$1")])
def test_scholarship_amount_boundary_at_zero(amount, shown):
    html = scholarship_card_html(make_scholarship(amount=amount), TODAY)
    assert stat(shown, "award") in html


def test_a_quote_in_a_scholarship_website_cannot_break_out_of_the_link():
    html = scholarship_card_html(make_scholarship(website='https://a.org/"x'), TODAY)
    assert 'href="https://a.org/&quot;x"' in html


def test_deadline_row_chips_are_exact_and_the_row_links_to_the_website():
    html = deadline_item_html(make_program(), TODAY)
    status, text = deadline_label(date(2027, 1, 15), TODAY)
    assert chip("Program", BLUE) + chip(text, DEADLINE_COLORS[status]) in html
    assert 'href="https://example.edu/ms-cs"' in html


@pytest.mark.parametrize("min_gpa, shown", [(0.0, False), (0.5, True), (1.0, True)])
def test_summary_shows_any_minimum_gpa_above_zero(min_gpa, shown):
    assert ("GPA" in eligibility_summary(make_scholarship(min_gpa=min_gpa))) is shown


def test_summary_keeps_a_citizenship_code_it_has_no_words_for():
    assert "Refugee" in eligibility_summary(make_scholarship(citizenship=("US", "Refugee")))
