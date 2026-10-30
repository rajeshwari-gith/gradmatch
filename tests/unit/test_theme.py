"""Unit tests for app/theme.py.

In plain words: the stylesheet is plain text, so we check it contains the design's colours, the
two fonts, the dot-grid background and the button effects. If someone deletes one by mistake, a
test fails.
"""
import pytest

from theme import BUTTON_HOVER_SHADOW, BUTTON_PRESSED_SHADOW, BUTTON_SHADOW, FONTS_URL, TOKENS, page_css

pytestmark = pytest.mark.unit


def test_the_stylesheet_is_one_style_block():
    css = page_css()
    assert css.strip().startswith("<style>") and css.strip().endswith("</style>")


@pytest.mark.parametrize("name, value", [("accent", "#5E7D63"), ("accent-dark", "#4A6450"),
                                         ("page", "#FBF8F1"), ("star", "#D9A441"), ("ink", "#2B2B26")])
def test_the_main_design_colours_are_defined(name, value):
    assert TOKENS[name] == value
    assert f"--{name}:{value};" in page_css()


def test_every_token_becomes_a_css_variable():
    css = page_css()
    for name, value in TOKENS.items():
        assert f"--{name}:{value};" in css


def test_the_two_fonts_are_loaded_and_used():
    css = page_css()
    assert f"@import url('{FONTS_URL}');" in css
    assert "DM+Sans" in FONTS_URL and "Fraunces" in FONTS_URL
    assert "font-family: 'DM Sans'" in css and "font-family: 'Fraunces'" in css


def test_the_page_has_the_cream_dot_grid_background():
    css = page_css()
    assert "background-color: var(--page);" in css
    assert "radial-gradient(rgba(94,80,60,0.06) 1px, transparent 1px)" in css
    assert "background-size: 22px 22px;" in css


def test_buttons_lift_on_hover_and_press_down_when_clicked():
    css = page_css()
    assert f"box-shadow: {BUTTON_SHADOW};" in css
    assert f"transform: translateY(-2px); box-shadow: {BUTTON_HOVER_SHADOW};" in css
    assert f"transform: translateY(1px) scale(.97); box-shadow: {BUTTON_PRESSED_SHADOW};" in css
    assert "min-height: 44px" in css      # touch targets at least 44px tall


def test_on_a_phone_the_table_becomes_labelled_cards():
    css = page_css()
    assert "@media (max-width: 640px)" in css
    assert ".gm-table-head { display:none; }" in css
    assert "content: attr(data-label);" in css
