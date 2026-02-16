def get_css():
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@300;400;600&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── FORCE LIGHT MODE EVERYWHERE ── */
:root {
    color-scheme: light !important;
    --cream:      #FAF7F2;
    --forest:     #2D5016;
    --sage:       #7A9E5F;
    --gold:       #C8952A;
    --gold-light: #F5E6C8;
    --charcoal:   #2C2C2C;
    --mid-gray:   #6B6B6B;
    --light-gray: #E8E4DE;
    --shadow:     rgba(44,44,44,0.08);
}

/* ── GLOBAL ── */
html, body {
    font-family: 'DM Sans', sans-serif !important;
    background-color: var(--cream) !important;
    color: var(--charcoal) !important;
    color-scheme: light !important;
}

/* Streamlit app container */
.stApp,
[data-testid="stAppViewContainer"],
section.main,
.main .block-container {
    background-color: var(--cream) !important;
    color: var(--charcoal) !important;
}

/* ── HIDE STREAMLIT CHROME (safe — does NOT hide sidebar toggle) ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.stDeployButton { display: none; }

/* ── SIDEBAR TOGGLE BUTTON — make it visible on mobile ── */
[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: flex !important;
    background-color: var(--forest) !important;
    border-radius: 0 8px 8px 0 !important;
    padding: 8px 6px !important;
}
[data-testid="collapsedControl"] svg,
[data-testid="collapsedControl"] span {
    color: white !important;
    fill: white !important;
}

/* ── INPUT LABELS — the text above form fields ── */
label,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stRadio label,
.stCheckbox label,
.stDateInput label,
.stFileUploader label,
.stTextArea label {
    color: var(--charcoal) !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    opacity: 1 !important;
    -webkit-text-fill-color: var(--charcoal) !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #F5F0E8 !important;
    border-right: 2px solid #E8E0D0 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--forest) !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: var(--charcoal) !important;
    -webkit-text-fill-color: var(--charcoal) !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: var(--forest) !important;
    color: white !important;
    -webkit-text-fill-color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    opacity: 1 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #3d6b1f !important;
    opacity: 1 !important;
}
[data-testid="stSidebar"] .stFormSubmitButton > button {
    background: var(--gold) !important;
    color: white !important;
    -webkit-text-fill-color: white !important;
    border: none !important;
    font-weight: 600 !important;
    opacity: 1 !important;
}

/* ── TYPOGRAPHY ── */
h1, h2, h3 {
    font-family: 'Fraunces', serif !important;
    color: var(--forest) !important;
    font-weight: 600 !important;
}
h1 { font-size: 2.2rem !important; letter-spacing: -0.02em; }
h2 { font-size: 1.6rem !important; }
h3 { font-size: 1.2rem !important; }

p, span, div {
    color: var(--charcoal);
}

/* ── MAIN CONTENT AREA ── */
.block-container {
    padding-top: 1.5rem !important;
    max-width: 1100px !important;
}

/* ── INPUTS ── */
input, textarea, select,
input[type="text"],
input[type="number"],
input[type="search"],
input[type="email"] {
    color-scheme: light !important;
    background-color: white !important;
    color: var(--charcoal) !important;
    -webkit-text-fill-color: var(--charcoal) !important;
    -webkit-box-shadow: 0 0 0px 1000px white inset !important;
    caret-color: var(--charcoal) !important;
    border-radius: 8px !important;
    border: 1.5px solid var(--light-gray) !important;
    opacity: 1 !important;
}

/* ── METRIC CARDS ── */
[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid var(--light-gray) !important;
    border-radius: 16px !important;
    padding: 1.2rem 1.4rem !important;
    box-shadow: 0 2px 12px var(--shadow) !important;
}
[data-testid="stMetricLabel"] p {
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    color: var(--mid-gray) !important;
    font-weight: 500 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Fraunces', serif !important;
    font-size: 1.9rem !important;
    color: var(--forest) !important;
    font-weight: 600 !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
    color: var(--sage) !important;
}

/* ── TABS ── */
[data-testid="stTabs"] [role="tablist"] {
    background: white !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid var(--light-gray) !important;
}
[data-testid="stTabs"] [role="tab"] {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: var(--mid-gray) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: var(--forest) !important;
    color: white !important;
    font-weight: 600 !important;
}

/* ── CARDS ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important;
    border: 1px solid var(--light-gray) !important;
    background: white !important;
    padding: 0.8rem 1rem !important;
    box-shadow: 0 2px 8px var(--shadow) !important;
    margin-bottom: 0.5rem !important;
}

/* ── BUTTONS ── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"] {
    background: var(--forest) !important;
    color: white !important;
    border: none !important;
}

/* ── PROGRESS BAR ── */
.stProgress > div > div {
    background: var(--sage) !important;
    border-radius: 99px !important;
}

/* ── SIDEBAR SECONDARY BUTTONS (e.g. inactive language toggle) ── */
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: white !important;
    color: var(--forest) !important;
    -webkit-text-fill-color: var(--forest) !important;
    border: 2px solid var(--forest) !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
    background: var(--gold-light) !important;
}

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    border: 1px solid var(--light-gray) !important;
    border-radius: 12px !important;
    background: white !important;
}

/* ── OVERRIDE DARK MODE — force light always ── */
@media (prefers-color-scheme: dark) {
    html, body, .stApp,
    [data-testid="stAppViewContainer"],
    section.main {
        background-color: var(--cream) !important;
        color: var(--charcoal) !important;
    }
    [data-testid="stSidebar"] {
        background: #F5F0E8 !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stMetric"],
    [data-testid="stExpander"] {
        background: white !important;
    }
    label,
    [data-testid="stWidgetLabel"] p {
        color: var(--charcoal) !important;
        -webkit-text-fill-color: var(--charcoal) !important;
    }
    input, textarea, select {
        background-color: white !important;
        color: var(--charcoal) !important;
        -webkit-text-fill-color: var(--charcoal) !important;
        -webkit-box-shadow: 0 0 0px 1000px white inset !important;
    }
}

/* ── SELECTED ITEM HIGHLIGHT ── */
/* Gold border on selected cards */
[data-testid="stVerticalBlockBorderWrapper"]:has(button[kind="secondary"][title="Tap to select"] ~ *) {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 2px var(--gold-light), 0 2px 8px var(--shadow) !important;
}

/* Tap select button — minimal, emoji only */
button[title="Tap to select"] {
    background: transparent !important;
    border: none !important;
    padding: 2px 6px !important;
    min-height: 32px !important;
    font-size: 1rem !important;
    box-shadow: none !important;
}

/* Category badge inline */
code {
    background: var(--gold-light) !important;
    color: var(--forest) !important;
    border-radius: 6px !important;
    padding: 1px 6px !important;
    font-size: 0.75rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
}

/* Move/action buttons in action bar */
.action-bar .stButton > button {
    padding: 4px 8px !important;
    font-size: 0.8rem !important;
    min-height: 36px !important;
}

/* ── FOOTER ── */
.footer-text {
    text-align: center;
    color: var(--mid-gray);
    font-size: 0.75rem;
    padding: 2rem 0 1rem;
    border-top: 1px solid var(--light-gray);
    margin-top: 2rem;
}

/* ── MOBILE ── */
@media (max-width: 768px) {
    .block-container { padding: 1rem 0.8rem !important; }
    h1 { font-size: 1.6rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    /* Bigger touch targets on mobile */
    .stButton > button { min-height: 44px !important; }
    label { font-size: 0.9rem !important; }
}
</style>
"""
