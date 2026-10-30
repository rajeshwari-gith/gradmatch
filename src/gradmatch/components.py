"""Small HTML building blocks for the GradMatch screens (Sage & Cream design).

In plain words: every piece of the new design that is drawn the same way everywhere (a chance
badge with a face, a tag, a school's initials tile, a date tile, a warning banner, a progress bar,
the funding bar on a PhD card, a star) is one small function here that returns HTML text. They
are plain Python with no Streamlit, so each one has unit tests. All text that comes from data is
escaped, and only http(s) links become clickable (see presentation.safe_link).
"""
from datetime import date
from html import escape

from gradmatch.fit import MATCH, REACH, SAFETY, UNKNOWN
from gradmatch.funding import FULLY_FUNDED, PARTIALLY_FUNDED
from gradmatch.presentation import safe_link

PASSED = "Passed"      # used only for deadlines that are over

# ---- Design tokens (the colours from the design handoff) ----
ACCENT, ACCENT_DARK, ACCENT_TINT = "#5E7D63", "#4A6450", "#EDF2EA"
INK, MUTED = "#2B2B26", "#67645A"
STAR, STAR_EMPTY = "#D9A441", "#9AA0A6"
URGENT_BG, URGENT_TEXT, URGENT_BORDER = "#FBE9E2", "#8A3A22", "#EBC2B2"
SURFACE_SOFT, TILE = "#F5F1E7", "#EEEADF"

# Each chance label: (face colour, badge background, badge text colour). Only these are bright.
CHANCE_COLORS = {
    SAFETY: ("#3A9D55", "#E3F4E7", "#17502A"),
    MATCH: ("#A6D94F", "#EEF8DC", "#3B5A0F"),
    REACH: ("#F0943A", "#FFEBD9", "#8A3B00"),
    PASSED: ("#F6CF4A", "#FDF6D8", "#6B4E00"),
    UNKNOWN: ("#C9C4B8", "#EEEAE0", MUTED),
}
CHANCE_MEANING = {
    SAFETY: "above the program's typical range",
    MATCH: "within the typical range",
    REACH: "below the typical range",
    UNKNOWN: "the school does not publish the numbers",
}

# The mouth of each face (a 32 x 32 drawing). Safety has closed, happy eyes.
_MOUTHS = {
    SAFETY: '<path d="M10 19q6 6.5 12 0" stroke="#111" stroke-width="2.2" fill="none" stroke-linecap="round"/>',
    MATCH: '<path d="M10.5 19.5q5.5 5 11 0" stroke="#111" stroke-width="2.2" fill="none" stroke-linecap="round"/>',
    REACH: '<path d="M10.5 23q5.5-5 11 0" stroke="#111" stroke-width="2.2" fill="none" stroke-linecap="round"/>',
    PASSED: '<path d="M11 21h10" stroke="#111" stroke-width="2.2" fill="none" stroke-linecap="round"/>',
    UNKNOWN: '<path d="M11 21h10" stroke="#111" stroke-width="2.2" fill="none" stroke-linecap="round"/>',
}
_OPEN_EYES = ('<circle cx="11.5" cy="12.5" r="2" fill="#111"/>'
              '<circle cx="20.5" cy="12.5" r="2" fill="#111"/>')
_HAPPY_EYES = ('<path d="M8.5 13.5q2.5-3.5 5 0M18.5 13.5q2.5-3.5 5 0" stroke="#111" '
               'stroke-width="2" fill="none" stroke-linecap="round"/>')

STAR_PATH = ("M12 3l2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.8 6.6 19.7l1.1-6.1L3.2 9.4l6.1-.8z")

# Kinds of tag and their (background, text) colours.
TAG_COLORS = {
    "required": (ACCENT_TINT, ACCENT_DARK),
    "optional": ("#EEEAE0", MUTED),
    "fellowship": ("#E3F4E7", "#17502A"),
    "scholarship": ("#FDF1DC", "#8A5A00"),
    "assistantship": ("#6E5640", "#FFFFFF"),
    "qualify": ("#E3F4E7", "#17502A"),
    "pending": ("#FFEBD2", "#7A3E00"),
}

# Funding bar colours on top of each PhD card.
FUNDING_BAR = {FULLY_FUNDED: ACCENT, PARTIALLY_FUNDED: "#9DB8AC"}
FUNDING_BAR_OTHER = "#E2DDD0"      # self-funded, or not stated

_SMALL_WORDS = {"of", "the", "and", "at", "in", "for", "a", "an", "&"}


def face_svg(label: str, size: int = 26) -> str:
    """The round face drawn for a chance label (Safety, Match, Reach, Passed or Unknown)."""
    color = CHANCE_COLORS.get(label, CHANCE_COLORS[UNKNOWN])[0]
    eyes = _HAPPY_EYES if label == SAFETY else _OPEN_EYES
    mouth = _MOUTHS.get(label, _MOUTHS[UNKNOWN])
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 32 32" aria-hidden="true">'
            f'<circle cx="16" cy="16" r="15" fill="{color}"/>{eyes}{mouth}</svg>')


def chance_badge(label: str, text: str | None = None) -> str:
    """A pill with a face on the left and the label (or custom text, e.g. '9 days left')."""
    _, background, color = CHANCE_COLORS.get(label, CHANCE_COLORS[UNKNOWN])
    return (f'<span class="gm-badge" style="background:{background};color:{color}">'
            f'{face_svg(label)}<span>{escape(text or label)}</span></span>')


def tag(text: str, kind: str) -> str:
    """A small rounded label such as 'Fellowship', 'Required' or '✓ You qualify'."""
    background, color = TAG_COLORS.get(kind, TAG_COLORS["optional"])
    return f'<span class="gm-tag" style="background:{background};color:{color}">{escape(text)}</span>'


def initials(name: str) -> str:
    """Up to three initials for a school's tile, skipping small words: 'University of X' -> 'UX'."""
    words = [w for w in name.replace("-", " ").split() if w.lower() not in _SMALL_WORDS]
    letters = "".join(w[0] for w in words if w[0].isalnum())[:3]
    return letters.upper() or "?"


def school_tile(name: str) -> str:
    """A rounded square with the school's initials. We never copy university logos."""
    return f'<span class="gm-tile" aria-hidden="true">{escape(initials(name))}</span>'


def official_link(url: str, label: str = "Official site ↗") -> str:
    """A link to the official page, or nothing if the address is not a normal web link."""
    link = safe_link(url)
    if not link:
        return ""
    return (f'<a class="gm-link" href="{escape(link, quote=True)}" target="_blank" '
            f'rel="noopener noreferrer">{escape(label)}</a>')


def star_svg(filled: bool, size: int = 20) -> str:
    """A star: filled gold when starred, grey outline when not."""
    if filled:
        return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" aria-hidden="true">'
                f'<path d="{STAR_PATH}" fill="{STAR}"/></svg>')
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" aria-hidden="true">'
            f'<path d="{STAR_PATH}" fill="none" stroke="{STAR_EMPTY}" stroke-width="1.6"/></svg>')


def funding_bar(funding: str) -> str:
    """The coloured strip across the top of a PhD card: dark sage = fully funded."""
    color = FUNDING_BAR.get(funding, FUNDING_BAR_OTHER)
    return f'<div class="gm-fundbar" style="background:{color}"></div>'


def stipend_box(amount_text: str, badge_html: str, label: str = "Annual stipend") -> str:
    """The soft box with a big amount (e.g. '$38,000') and the chance badge on the right."""
    return (f'<div class="gm-stipend"><div><div class="gm-stipend-label">{escape(label)}</div>'
            f'<div class="gm-stipend-amount">{escape(amount_text)}</div></div>{badge_html}</div>')


def date_tile(day: date, urgent: bool) -> str:
    """A small square with the month and the day; urgent dates are tinted."""
    style = f"background:{URGENT_BG};color:{URGENT_TEXT}" if urgent else f"background:{SURFACE_SOFT}"
    return (f'<div class="gm-datetile" style="{style}"><span>{day:%b}</span>'
            f'<b>{day.day}</b></div>')


def warning_banner(title: str, detail: str) -> str:
    """The banner shown when deadlines are close. role="alert" lets screen readers announce it."""
    return (f'<div class="gm-banner" role="alert" style="background:{URGENT_BG};'
            f'border-color:{URGENT_BORDER}">{face_svg(REACH, 44)}<div><b>{escape(title)}</b>'
            f'<div>{escape(detail)}</div></div></div>')


def progress_bar(done: int, total: int) -> str:
    """A thin bar: how much of something is done (e.g. 2 of 4 required items)."""
    share = 0 if total <= 0 else max(0, min(done, total)) / total
    return (f'<div class="gm-progress" role="progressbar" aria-valuenow="{done}" '
            f'aria-valuemax="{total}"><div style="width:{share * 100:.0f}%"></div></div>')


def check_item(text: str, ok: bool) -> str:
    """One line of a checklist: a green tick when true, an orange '!' when not."""
    mark = '<span class="gm-ok">✓</span>' if ok else '<span class="gm-warn">!</span>'
    return f'<li>{mark} {escape(text)}</li>'
