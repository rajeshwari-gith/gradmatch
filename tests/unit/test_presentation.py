"""Unit tests for presentation.py.

Techniques: boundary-value analysis on money and on a scholarship's minimum GPA, equivalence
partitioning on website links and on TOEFL scores around a program's minimum.
"""
from datetime import date

import pytest

from conftest import make_scholarship
from gradmatch.presentation import (ESTIMATE_NOTE, eligibility_summary, format_date, money, safe_link,
                                    special_label, toefl_warning)

pytestmark = pytest.mark.unit


# ---- number and date formatting ----

@pytest.mark.parametrize("amount, text", [(0, "$0"), (999, "$999"), (27000, "$27,000"),
                                          (1234567.4, "$1,234,567")])
def test_money(amount, text):
    assert money(amount) == text


def test_format_date_has_no_leading_zero():
    assert format_date(date(2026, 12, 5)) == "Dec 5, 2026"
    assert format_date(date(2027, 2, 1)) == "Feb 1, 2027"


# ---- websites: only normal web addresses become links ----
# Why: a link like "javascript:..." could run code in the page. Only http(s) is allowed.

@pytest.mark.parametrize("url", ["https://example.edu/ms", "http://example.edu", "  https://a.edu  "])
def test_normal_web_addresses_are_links(url):
    assert safe_link(url) == url.strip()


@pytest.mark.parametrize("url", ["", "   ", "javascript:alert(1)", "ftp://example.edu", "example.edu", None])
def test_other_text_is_not_linked(url):
    assert safe_link(url) is None


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


# ---- The estimate note ----

def test_the_estimate_note_mentions_estimates_and_mandatory_fees():
    assert "estimates" in ESTIMATE_NOTE
    assert "mandatory student fees" in ESTIMATE_NOTE


def test_the_estimate_note_does_not_promise_a_value_the_school_does_not_publish():
    assert "does not publish a value, the page says so" in ESTIMATE_NOTE


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


@pytest.mark.parametrize("min_gpa, shown", [(0.0, False), (0.5, True), (1.0, True)])
def test_summary_shows_any_minimum_gpa_above_zero(min_gpa, shown):
    assert ("GPA" in eligibility_summary(make_scholarship(min_gpa=min_gpa))) is shown


def test_summary_keeps_a_citizenship_code_it_has_no_words_for():
    assert "Refugee" in eligibility_summary(make_scholarship(citizenship=("US", "Refugee")))
