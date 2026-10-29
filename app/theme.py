"""The look of the app: colours, fonts, background, cards and button effects (Sage & Cream).

In plain words: Streamlit draws its own widgets, so to match the design we add one block of CSS
at the top of every page. Everything visual lives here, in one place, so it is easy to change and
easy to test. It changes how things look, never what the app calculates.
"""

FONTS_URL = ("https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800"
             "&family=Fraunces:wght@500;600;700&display=swap")

# The design tokens from the handoff, as CSS variables, so every rule below can use the names.
TOKENS = {
    "accent": "#5E7D63", "accent-dark": "#4A6450", "accent-tint": "#EDF2EA",
    "ink": "#2B2B26", "muted": "#67645A", "nav-text": "#5C5A50",
    "page": "#FBF8F1", "surface": "rgba(255,255,255,0.94)", "surface-soft": "#F5F1E7",
    "tile": "#EEEADF", "border": "#E8E2D4", "row-line": "#F1ECE1", "table-head": "#FAF6EE",
    "input-border": "#D6D3CC", "star": "#D9A441", "star-empty": "#9AA0A6",
    "notice-bg": "#FDF1DC", "notice-text": "#8A5A00",
    "urgent-bg": "#FBE9E2", "urgent-text": "#8A3A22", "urgent-strong": "#9A3F22",
    "ok-text": "#17502A",
}

BUTTON_SHADOW = "0 1px 2px rgba(43,43,38,.12), 0 6px 14px rgba(74,100,80,.28)"
BUTTON_HOVER_SHADOW = "0 2px 4px rgba(43,43,38,.14), 0 12px 24px rgba(74,100,80,.34)"
BUTTON_PRESSED_SHADOW = "0 1px 2px rgba(43,43,38,.25)"
CARD_SHADOW = "0 10px 30px rgba(31,35,40,0.08)"


def _variables() -> str:
    return "".join(f"--{name}:{value};" for name, value in TOKENS.items())


def page_css() -> str:
    """The whole stylesheet, wrapped in <style>, ready for st.markdown(..., unsafe_allow_html=True)."""
    return f"""
<style>
@import url('{FONTS_URL}');
:root {{ {_variables()} }}

/* Page: cream with a faint dot grid; DM Sans everywhere, Fraunces for headings. */
[data-testid="stAppViewContainer"] {{
  background-color: var(--page);
  background-image: radial-gradient(rgba(94,80,60,0.06) 1px, transparent 1px);
  background-size: 22px 22px;
}}
html, body, [data-testid="stAppViewContainer"], button, input, select, textarea {{
  font-family: 'DM Sans', sans-serif; color: var(--ink);
}}
h1, h2, h3, .gm-serif {{ font-family: 'Fraunces', serif !important; font-weight: 600;
  letter-spacing: -0.01em; color: var(--ink); }}
.block-container {{ max-width: 1280px; padding-top: 1.2rem; }}
.gm-title-accent {{ color: var(--accent); }}
.gm-sub, .gm-muted {{ color: var(--muted); font-size: 0.9rem; }}
a, .gm-link {{ color: var(--accent); font-weight: 600; text-decoration: underline; }}
a:hover, .gm-link:hover {{ color: var(--accent-dark); }}

/* Header: logo, nav and the right-hand pills. */
.gm-logo {{ display:flex; align-items:center; gap:10px; font-weight:800; font-size:20px; }}
.gm-logo-mark {{ width:38px; height:38px; border-radius:10px; background:var(--accent);
  display:inline-flex; align-items:center; justify-content:center; }}
.gm-pill {{ display:inline-flex; align-items:center; gap:6px; padding:6px 12px; border-radius:999px;
  font-size:13px; font-weight:700; }}
.gm-pill-star {{ color: var(--nav-text); }}
.gm-pill-notice {{ background: var(--notice-bg); color: var(--notice-text); }}

/* Navigation (a horizontal radio) drawn as pills. */
div[data-testid="stRadio"].st-key-page div[role="radiogroup"] {{ gap: 6px; flex-wrap: wrap; }}
.st-key-page label {{ padding:10px 16px; border-radius:999px; min-height:44px; color:var(--nav-text);
  transition: background .15s ease, color .15s ease; }}
.st-key-page label:hover {{ background: rgba(94,125,99,.08); }}
.st-key-page label:has(input:checked) {{ background: var(--accent-tint); color: var(--accent-dark); font-weight:700; }}
.st-key-page label > div:first-child {{ display:none; }}

/* Cards, info boxes and tables. */
.gm-card {{ background: var(--surface); border:1px solid var(--border); border-radius:18px;
  box-shadow: {CARD_SHADOW}; padding:20px 22px; margin-bottom:14px; position:relative; overflow:hidden; }}
.gm-soft {{ background: var(--surface-soft); border:1px solid var(--border); border-radius:18px; padding:16px 18px; }}
.gm-label {{ font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); }}
.gm-table-head {{ background: var(--table-head); border-bottom:1px solid var(--border); font-size:12px;
  font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); }}
.gm-row {{ border-bottom:1px solid var(--row-line); }}
.gm-money {{ color: var(--accent); font-weight:800; }}

/* Small building blocks from gradmatch.components. */
.gm-badge {{ display:inline-flex; align-items:center; gap:6px; padding:3px 10px 3px 4px; border-radius:999px;
  font-size:13px; font-weight:800; white-space:nowrap; }}
.gm-tag {{ display:inline-block; padding:2px 9px; border-radius:999px; font-size:11.5px; font-weight:800;
  letter-spacing:.02em; }}
.gm-tile {{ width:46px; height:46px; border-radius:14px; background:var(--tile); color:var(--ink);
  display:inline-flex; align-items:center; justify-content:center; font-weight:800; font-size:14px; flex:0 0 46px; }}
.gm-fundbar {{ position:absolute; left:0; right:0; top:0; height:8px; }}
.gm-stipend {{ background:var(--surface-soft); border-radius:14px; padding:12px 14px; display:flex;
  align-items:center; justify-content:space-between; gap:10px; margin:10px 0; }}
.gm-stipend-label {{ font-size:12px; color:var(--muted); font-weight:600; }}
.gm-stipend-amount {{ font-size:32px; font-weight:800; color:var(--accent); line-height:1.1; }}
.gm-datetile {{ width:58px; height:58px; border-radius:14px; display:flex; flex-direction:column;
  align-items:center; justify-content:center; text-transform:uppercase; }}
.gm-datetile span {{ font-size:11px; font-weight:700; }} .gm-datetile b {{ font-size:22px; line-height:1; }}
.gm-banner {{ display:flex; gap:14px; align-items:center; border:1.5px solid; border-radius:18px;
  padding:14px 18px; color: var(--urgent-text); margin: 8px 0 16px; }}
.gm-progress {{ width:140px; height:6px; border-radius:999px; background:var(--accent-tint); overflow:hidden; }}
.gm-progress > div {{ height:100%; background:var(--accent); }}
.gm-check {{ list-style:none; padding:0; margin:8px 0; font-size:14px; }}
.gm-ok {{ color: var(--ok-text); font-weight:800; }} .gm-warn {{ color: var(--urgent-strong); font-weight:800; }}
.gm-urgent {{ color: var(--urgent-strong); font-weight:700; }}
.gm-passed {{ text-decoration: line-through; color: var(--muted); }}

/* Buttons: soft raised, lift on hover, press down when clicked. */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
  border-radius: 13px; min-height: 44px; box-shadow: {BUTTON_SHADOW};
  transition: background .15s ease, color .15s ease, box-shadow .15s ease, transform .1s ease; }}
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {{
  transform: translateY(-2px); box-shadow: {BUTTON_HOVER_SHADOW}; }}
.stButton > button:active, .stFormSubmitButton > button:active, .stDownloadButton > button:active {{
  transform: translateY(1px) scale(.97); box-shadow: {BUTTON_PRESSED_SHADOW}; }}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primaryFormSubmit"] {{
  background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 800; }}
.stButton > button[kind="primary"]:active {{ background: var(--accent-dark); }}

/* Star buttons are small round white buttons. */
[class*="st-key-star-"] button {{ border-radius:999px; background:#fff; width:44px; padding:0; font-size:18px; }}

/* Inputs: gold border and a soft ring when focused. */
input:focus, textarea:focus, [data-baseweb="select"] > div:focus-within {{
  border-color: var(--star) !important; box-shadow: 0 0 0 4px rgba(94,125,99,.18) !important; }}
</style>
"""
