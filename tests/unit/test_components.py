"""Unit tests for components.py (the HTML building blocks of the new design).
"""
from datetime import date

import pytest

from gradmatch.components import (ACCENT, CHANCE_COLORS, CHANCE_MEANING, FUNDING_BAR_OTHER, PASSED,
                                  STAR, STAR_EMPTY, SURFACE_SOFT, TAG_COLORS, URGENT_BG, chance_badge,
                                  check_item, date_tile, face_svg, funding_bar, initials, official_link,
                                  progress_bar, school_tile, star_svg, stipend_box, tag, warning_banner)
from gradmatch.fit import MATCH, REACH, SAFETY, UNKNOWN
from gradmatch.funding import FULLY_FUNDED, FUNDING_UNKNOWN, PARTIALLY_FUNDED, SELF_FUNDED

pytestmark = pytest.mark.unit


# ---- Faces and chance badges: one class per label ----
# Why: the badge colour and face are what students read first, so each label must look right.

@pytest.mark.parametrize("label", [SAFETY, MATCH, REACH, PASSED, UNKNOWN])
def test_each_label_has_its_own_face_colour_and_badge_colours(label):
    face, background, text = CHANCE_COLORS[label]
    assert f'fill="{face}"' in face_svg(label)
    badge = chance_badge(label)
    assert f"background:{background};color:{text}" in badge
    assert f"<span>{label}</span>" in badge


def test_safety_has_happy_closed_eyes_and_the_others_have_open_eyes():
    assert "q2.5-3.5" in face_svg(SAFETY) and "<circle cx=\"11.5\"" not in face_svg(SAFETY)
    for label in (MATCH, REACH, PASSED, UNKNOWN):
        assert '<circle cx="11.5" cy="12.5" r="2"' in face_svg(label)


def test_reach_frowns_and_match_smiles():
    assert "M10.5 23q5.5-5 11 0" in face_svg(REACH)
    assert "M10.5 19.5q5.5 5 11 0" in face_svg(MATCH)


def test_an_unknown_label_is_drawn_like_unknown():
    assert face_svg("Something else") == face_svg(UNKNOWN)
    assert CHANCE_COLORS[UNKNOWN][1] in chance_badge("Something else")


def test_face_size_can_change_and_is_hidden_from_screen_readers():
    svg = face_svg(REACH, 44)
    assert 'width="44" height="44"' in svg and 'aria-hidden="true"' in svg


def test_badge_can_show_custom_text_and_escapes_it():
    assert "<span>9 days left</span>" in chance_badge(REACH, "9 days left")
    assert "&lt;b&gt;" in chance_badge(MATCH, "<b>")


def test_every_chance_label_has_a_meaning():
    assert set(CHANCE_MEANING) == {SAFETY, MATCH, REACH, UNKNOWN}


# ---- Tags ----

@pytest.mark.parametrize("kind", list(TAG_COLORS))
def test_each_tag_kind_has_its_colours(kind):
    background, color = TAG_COLORS[kind]
    assert tag("X", kind) == f'<span class="gm-tag" style="background:{background};color:{color}">X</span>'


def test_an_unknown_tag_kind_looks_optional_and_text_is_escaped():
    assert tag("<i>", "nope") == tag("<i>", "optional")
    assert "&lt;i&gt;" in tag("<i>", "nope")


# ---- School tiles: initials ----

@pytest.mark.parametrize("name, letters", [
    ("Example State University", "ESU"),
    ("University of Michigan-Ann Arbor", "UMA"),
    ("The University of Texas at Austin", "UTA"),
    ("Massachusetts Institute of Technology", "MIT"),
    ("Harvard University", "HU"),
    ("Grand Valley State University Extended", "GVS"),   # at most three letters
    ("of the", "?"),                                     # nothing left after small words
    ("", "?"),
    ("12th Street College", "1SC"),
    ("Winston-Salem State University", "WSS"),            # a hyphen splits two words
])
def test_initials(name, letters):
    assert initials(name) == letters


def test_school_tile_shows_the_initials_and_never_markup():
    assert school_tile("Example State University") == '<span class="gm-tile" aria-hidden="true">ESU</span>'
    assert school_tile("<script> College") == '<span class="gm-tile" aria-hidden="true">C</span>'


# ---- Official links ----

def test_official_link_opens_in_a_new_tab_safely():
    html = official_link("https://example.edu/apply")
    assert html == ('<a class="gm-link" href="https://example.edu/apply" target="_blank" '
                    'rel="noopener noreferrer">Official site ↗</a>')


@pytest.mark.parametrize("url", ["", "javascript:alert(1)", "example.edu", None])
def test_no_link_for_an_unsafe_or_missing_address(url):
    assert official_link(url) == ""


def test_a_quote_in_a_link_cannot_break_out():
    assert 'href="https://a.edu/&quot;x"' in official_link('https://a.edu/"x')


def test_official_link_label_can_change():
    assert ">View on official site ↗</a>" in official_link("https://a.edu", "View on official site ↗")


# ---- Stars ----

def test_filled_star_is_gold_and_empty_star_is_an_outline():
    assert f'fill="{STAR}"' in star_svg(True)
    empty = star_svg(False)
    assert f'stroke="{STAR_EMPTY}"' in empty and 'fill="none"' in empty
    assert 'width="24"' in star_svg(True, 24)


# ---- Funding bar and stipend box ----

@pytest.mark.parametrize("funding, color", [
    (FULLY_FUNDED, ACCENT), (PARTIALLY_FUNDED, "#9DB8AC"),
    (SELF_FUNDED, FUNDING_BAR_OTHER), (FUNDING_UNKNOWN, FUNDING_BAR_OTHER)])
def test_funding_bar_colour_follows_the_funding_level(funding, color):
    assert funding_bar(funding) == f'<div class="gm-fundbar" style="background:{color}"></div>'


def test_stipend_box_shows_label_amount_and_badge():
    html = stipend_box("$38,000", chance_badge(REACH))
    assert '<div class="gm-stipend-label">Annual stipend</div>' in html
    assert '<div class="gm-stipend-amount">$38,000</div>' in html
    assert chance_badge(REACH) in html
    assert "Yearly cost" in stipend_box("$1", "", "Yearly cost")


# ---- Date tiles and the warning banner ----

def test_date_tile_shows_month_and_day_and_tints_urgent_dates():
    urgent = date_tile(date(2026, 11, 7), True)
    assert "<span>Nov</span><b>7</b>" in urgent and URGENT_BG in urgent
    later = date_tile(date(2027, 1, 15), False)
    assert "<span>Jan</span><b>15</b>" in later and SURFACE_SOFT in later and URGENT_BG not in later


def test_warning_banner_is_an_alert_with_a_reach_face_and_escaped_text():
    html = warning_banner("2 deadlines soon", "A <b> and B")
    assert 'role="alert"' in html and face_svg(REACH, 44) in html
    assert "<b>2 deadlines soon</b>" in html and "A &lt;b&gt; and B" in html


# ---- Progress bar: boundary values ----

@pytest.mark.parametrize("done, total, width", [
    (0, 4, "0%"), (2, 4, "50%"), (4, 4, "100%"),
    (5, 4, "100%"),     # more done than total is capped
    (-1, 4, "0%"),      # never below zero
    (0, 0, "0%"),       # nothing to do: an empty bar, no division by zero
    (1, 1, "100%"),     # a single task, done
])
def test_progress_bar_width(done, total, width):
    html = progress_bar(done, total)
    assert f'style="width:{width}"' in html
    assert f'aria-valuenow="{done}" aria-valuemax="{total}"' in html


# ---- Checklist lines ----

def test_check_item_shows_a_tick_or_a_warning_and_escapes():
    assert check_item("Full tuition waiver", True) == '<li><span class="gm-ok">✓</span> Full tuition waiver</li>'
    assert check_item("<x>", False) == '<li><span class="gm-warn">!</span> &lt;x&gt;</li>'


# ---- Pieces that must use the right label and the default sizes ----

def test_a_badge_draws_the_face_of_its_own_label():
    for label in (SAFETY, MATCH, REACH, PASSED):
        assert face_svg(label) in chance_badge(label)


def test_default_sizes_of_the_face_and_the_star():
    assert 'width="26" height="26"' in face_svg(SAFETY)
    assert 'width="20" height="20"' in star_svg(True)
