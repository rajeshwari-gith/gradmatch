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

UNPUBLISHED = dict(avg_gpa=None, acceptance_rate=None, stipend=None, application_deadline=None,
                   source="ipeds")


def test_unpublished_values_show_n_a_and_are_not_called_estimates():
    html = result_card_html(make_result(fit=UNKNOWN, funding=FUNDING_UNKNOWN, **UNPUBLISHED), TODAY)
    assert html.count(">n/a<") == 2
    assert "(est.)" not in html


def test_published_values_from_official_data_are_not_called_estimates():
    html = result_card_html(make_result(source="official-page"), TODAY)
    assert "3.40" in html and "40%" in html
    assert "(est.)" not in html


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
