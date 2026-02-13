# styles.py
# Professional CSS for Home OS Pro
# Warm, dignified aesthetic — fits the emotional tone of the product

def get_css():
    return """
<style>
/* ── IMPORT FONTS ── */
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,400;0,600;1,300&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── ROOT VARIABLES ── */
:root {
    --cream:     #FAF7F2;
    --warm-white:#FFFFFF;
    --forest:    #2D5016;
    --sage:      #7A9E5F;
    --gold:      #C8952A;
    --gold-light:#F5E6C8;
    --rust:      #C4572A;
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

/* ── HIDE STREAMLIT DEFAULTS ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── APP HEADER ── */
.block-container {
    padding-top: 1.5rem !important;
    max-width: 1100px !important;
}

/* ── HEADINGS ── */
h1, h2, h3 {
    font-family: 'Fraunces', serif !important;
    color: var(--forest) !important;
    font-weight: 600 !important;
}
h1 { font-size: 2.2rem !important; letter-spacing: -0.02em; }
h2 { font-size: 1.6rem !important; }
h3 { font-size: 1.2rem !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--forest) !important;
    border-right: none !important;
}
[data-testid="stSidebar"] * {
    color: var(--cream) !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--gold-light) !important;
    font-family: 'Fraunces', serif !important;
}
[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.12) !important;
    color: var(--cream) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,255,255,0.22) !important;
}

/* ── METRIC CARDS ── */
[data-testid="stMetric"] {
    background: var(--warm-white) !important;
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
    background: var(--warm-white) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid var(--light-gray) !important;
    gap: 2px !important;
}
[data-testid="stTabs"] [role="tab"] {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 6px 14px !important;
    color: var(--mid-gray) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: var(--forest) !important;
    color: var(--cream) !important;
    font-weight: 600 !important;
}

/* ── CONTAINERS / CARDS ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important;
    border: 1px solid var(--light-gray) !important;
    background: var(--warm-white) !important;
    padding: 0.8rem 1rem !important;
    box-shadow: 0 2px 8px var(--shadow) !important;
    margin-bottom: 0.5rem !important;
}

/* ── BUTTONS ── */
.stButton button {
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: all 0.2s ease !important;
    border: none !important;
}
.stButton button[kind="primary"] {
    background: var(--forest) !important;
    color: white !important;
}
.stButton button[kind="primary"]:hover {
    background: #3d6b1f !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(45,80,22,0.3) !important;
}
.stButton button[kind="secondary"] {
    background: var(--warm-white) !important;
    color: var(--charcoal) !important;
    border: 1px solid var(--light-gray) !important;
}

/* ── INPUTS ── */
/* Fix sidebar widget visibility */
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stNumberInput input {
    background: rgba(255,255,255,0.15) !important;
    color: white !important;
    border-color: rgba(255,255,255,0.25) !important;
}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stRadio div {
    color: var(--cream) !important;
}
[data-testid="stSidebar"] .stSelectbox > div {
    background: rgba(255,255,255,0.1) !important;
    color: white !important;
}
/* Fix sidebar form submit button */
[data-testid="stSidebar"] .stForm .stButton button {
    background: var(--gold) !important;
    color: white !important;
    font-weight: 600 !important;
}
/* Fix sidebar tabs */
[data-testid="stSidebar"] [role="tab"] {
    color: var(--cream) !important;
    background: rgba(255,255,255,0.08) !important;
}
[data-testid="stSidebar"] [role="tab"][aria-selected="true"] {
    background: rgba(200,149,42,0.4) !important;
    color: white !important;
}
/* Fix sidebar camera and file upload */
[data-testid="stSidebar"] .stCameraInput,
[data-testid="stSidebar"] .stFileUploader {
    background: rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
}
/* Fix number input spinners */
[data-testid="stSidebar"] .stNumberInput button {
    background: rgba(255,255,255,0.15) !important;
    color: white !important;
    border-color: rgba(255,255,255,0.2) !important;
}

.stTextInput input, .stNumberInput input, .stSelectbox select {
    border-radius: 8px !important;
    border: 1.5px solid var(--light-gray) !important;
    background: var(--warm-white) !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: border-color 0.2s ease !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: var(--sage) !important;
    box-shadow: 0 0 0 3px rgba(122,158,95,0.15) !important;
}

/* ── SUCCESS / INFO / WARNING BOXES ── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border-left-width: 4px !important;
}
.stSuccess {
    background: #f0f7eb !important;
    border-left-color: var(--sage) !important;
}
.stInfo {
    background: #f0f5ff !important;
}

/* ── PROGRESS BAR ── */
.stProgress > div > div {
    background: var(--sage) !important;
    border-radius: 99px !important;
}
.stProgress > div {
    border-radius: 99px !important;
    background: var(--light-gray) !important;
}

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    border: 1px solid var(--light-gray) !important;
    border-radius: 12px !important;
    background: var(--warm-white) !important;
}
[data-testid="stExpander"] summary {
    font-weight: 500 !important;
    color: var(--charcoal) !important;
}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid var(--light-gray) !important;
}

/* ── MOBILE RESPONSIVE ── */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem 0.8rem !important;
    }
    h1 { font-size: 1.6rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    [data-testid="stTabs"] [role="tab"] {
        font-size: 0.72rem !important;
        padding: 5px 8px !important;
    }
    /* Stack columns on mobile */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
    }
}

/* ── CAPTION / SMALL TEXT ── */
.stCaption, caption {
    color: var(--mid-gray) !important;
    font-size: 0.78rem !important;
}

/* ── TOAST ── */
[data-testid="stToast"] {
    background: var(--forest) !important;
    color: var(--cream) !important;
    border-radius: 12px !important;
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
</style>
"""
