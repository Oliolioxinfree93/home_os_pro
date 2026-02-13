def get_css():
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@300;400;600&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --cream:     #FAF7F2;
    --forest:    #2D5016;
    --sage:      #7A9E5F;
    --gold:      #C8952A;
    --gold-light:#F5E6C8;
    --charcoal:  #2C2C2C;
    --mid-gray:  #6B6B6B;
    --light-gray:#E8E4DE;
    --shadow:    rgba(44,44,44,0.08);
}

/* ── GLOBAL ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: var(--cream) !important;
    color: var(--charcoal) !important;
}

/* ── HIDE ONLY SPECIFIC STREAMLIT CHROME ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.stDeployButton { display: none; }

/* ── TYPOGRAPHY ── */
h1, h2, h3 {
    font-family: 'Fraunces', serif !important;
    color: var(--forest) !important;
    font-weight: 600 !important;
}
h1 { font-size: 2.2rem !important; letter-spacing: -0.02em; }
h2 { font-size: 1.6rem !important; }
h3 { font-size: 1.2rem !important; }

/* ── MAIN CONTENT AREA ── */
.block-container {
    padding-top: 1.5rem !important;
    max-width: 1100px !important;
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
[data-testid="stSidebar"] .stButton > button {
    background: var(--forest) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stFormSubmitButton > button {
    background: var(--gold) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
}

/* ── METRIC CARDS ── */
[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid var(--light-gray) !important;
    border-radius: 16px !important;
    padding: 1.2rem 1.4rem !important;
    box-shadow: 0 2px 12px var(--shadow) !important;
}
[data-testid="stMetricLabel"] {
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
.stButton > button[kind="primary"]:hover {
    background: #3d6b1f !important;
    transform: translateY(-1px) !important;
}

/* ── INPUTS ── */
input[type="text"],
input[type="number"] {
    border-radius: 8px !important;
    border: 1.5px solid var(--light-gray) !important;
}

/* ── PROGRESS BAR ── */
.stProgress > div > div {
    background: var(--sage) !important;
    border-radius: 99px !important;
}

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    border: 1px solid var(--light-gray) !important;
    border-radius: 12px !important;
    background: white !important;
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
}
</style>
"""
