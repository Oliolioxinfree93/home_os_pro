def get_css():
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=Manrope:wght@400;500;600;700&display=swap');

:root {
    color-scheme: light !important;
    --bg: #f6f2ea;
    --bg-soft: #fbf8f2;
    --surface: #ffffff;
    --surface-soft: #fffdf9;
    --line: #e7ddcf;
    --line-strong: #d8c7b2;
    --text: #2f2a24;
    --text-muted: #6f675d;
    --forest: #26481f;
    --forest-600: #315927;
    --sage: #7f9f65;
    --gold: #bb8229;
    --gold-soft: #f7e7c8;
    --shadow-sm: 0 2px 8px rgba(39, 30, 21, 0.06);
    --shadow-md: 0 10px 24px rgba(39, 30, 21, 0.1);
}

html,
body,
.stApp,
[data-testid="stAppViewContainer"],
section.main,
.main .block-container {
    font-family: 'Manrope', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

[data-testid="stAppViewContainer"] {
    background-image:
        radial-gradient(circle at 12% -8%, rgba(255, 255, 255, 0.85) 0, rgba(255, 255, 255, 0) 40%),
        radial-gradient(circle at 95% 4%, rgba(245, 221, 179, 0.28) 0, rgba(245, 221, 179, 0) 33%),
        linear-gradient(180deg, #f8f3e9 0%, #f6f2ea 100%) !important;
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.stDeployButton { display: none; }

[data-testid="stHeader"] {
    background: linear-gradient(180deg, rgba(246, 242, 234, 0.94) 0%, rgba(246, 242, 234, 0.62) 62%, rgba(246, 242, 234, 0.06) 100%) !important;
    backdrop-filter: blur(8px);
}

.block-container {
    max-width: 1120px !important;
    padding-top: 1.15rem !important;
    padding-bottom: 2.4rem !important;
}

h1, h2, h3 {
    font-family: 'Fraunces', serif !important;
    color: var(--forest) !important;
    letter-spacing: -0.01em;
}

h1 {
    font-size: clamp(1.8rem, 2.2vw, 2.35rem) !important;
    line-height: 1.1 !important;
    margin-bottom: 0.35rem !important;
}

h2 { font-size: clamp(1.3rem, 1.6vw, 1.7rem) !important; }
h3 { font-size: clamp(1.12rem, 1.3vw, 1.32rem) !important; }

p, li, label {
    color: var(--text) !important;
}

small,
.stCaption,
[data-testid="stMarkdownContainer"] small,
[data-testid="stMarkdownContainer"] p:has(> small) {
    color: var(--text-muted) !important;
}

[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: flex !important;
    align-items: center !important;
    background: linear-gradient(180deg, #2f5525 0%, #25431e 100%) !important;
    border-radius: 0 10px 10px 0 !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="collapsedControl"] svg,
[data-testid="collapsedControl"] span {
    color: #fff !important;
    fill: #fff !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f9f3e8 0%, #f2e7d7 100%) !important;
    border-right: 1px solid var(--line-strong) !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] span {
    color: #2f2a23 !important;
    -webkit-text-fill-color: #2f2a23 !important;
}

label,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em;
}

input, textarea, select,
[data-baseweb="select"] > div,
[data-testid="stDateInputField"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    border-radius: 12px !important;
    border: 1px solid var(--line) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.95) !important;
}

input:focus, textarea:focus, select:focus,
[data-baseweb="select"] > div:focus-within,
.stTextInput > div > div:focus-within,
.stNumberInput > div > div:focus-within,
.stTextArea > div > div:focus-within {
    border-color: #729958 !important;
    box-shadow: 0 0 0 4px rgba(129, 161, 104, 0.2) !important;
}

.stButton > button,
.stFormSubmitButton > button {
    border-radius: 12px !important;
    font-weight: 700 !important;
    border: 1px solid transparent !important;
    transition: transform 150ms ease, box-shadow 150ms ease, background-color 150ms ease !important;
    box-shadow: var(--shadow-sm) !important;
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button {
    background: linear-gradient(180deg, var(--forest-600) 0%, var(--forest) 100%) !important;
    color: #fff !important;
}

.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 10px 18px rgba(37, 67, 31, 0.28) !important;
}

.stButton > button[kind="secondary"] {
    background: var(--surface-soft) !important;
    color: var(--forest) !important;
    border-color: var(--line-strong) !important;
}

.stButton > button[kind="secondary"]:hover {
    background: #f8f2e5 !important;
}

.stButton > button:focus-visible,
.stFormSubmitButton > button:focus-visible {
    outline: 3px solid rgba(126, 161, 99, 0.45) !important;
    outline-offset: 2px !important;
}

[data-testid="stMetric"] {
    background:
        radial-gradient(circle at 100% 0%, rgba(245, 228, 197, 0.35) 0, rgba(245, 228, 197, 0) 44%),
        linear-gradient(180deg, #ffffff 0%, #fffdf8 100%) !important;
    border: 1px solid var(--line) !important;
    border-radius: 16px !important;
    padding: 1rem 1.15rem !important;
    box-shadow: var(--shadow-sm) !important;
}

[data-testid="stMetricLabel"] p {
    color: var(--text-muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-size: 0.73rem !important;
    font-weight: 700 !important;
}

[data-testid="stMetricValue"] {
    font-family: 'Fraunces', serif !important;
    color: var(--forest) !important;
    font-size: clamp(1.35rem, 2vw, 2rem) !important;
}

[data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
}

[data-testid="stTabs"] [role="tablist"] {
    background: rgba(255, 255, 255, 0.74) !important;
    border: 1px solid var(--line) !important;
    border-radius: 13px !important;
    padding: 0.3rem !important;
}

[data-testid="stTabs"] [role="tab"] {
    border-radius: 10px !important;
    color: var(--text-muted) !important;
    font-weight: 600 !important;
    padding: 0.45rem 0.9rem !important;
}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: linear-gradient(180deg, #37642a 0%, #27491f 100%) !important;
    color: #fff !important;
    box-shadow: 0 8px 14px rgba(39, 73, 31, 0.22) !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.97) 0%, rgba(255, 251, 244, 0.99) 100%) !important;
    border: 1px solid var(--line) !important;
    border-radius: 16px !important;
    padding: 0.9rem 1rem !important;
    box-shadow: var(--shadow-sm) !important;
    margin-bottom: 0.65rem !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: var(--shadow-md) !important;
}

[data-testid="stDataFrame"],
[data-testid="stTable"] {
    border-radius: 14px !important;
    border: 1px solid var(--line) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-sm) !important;
    background: var(--surface) !important;
}

[data-testid="stExpander"] {
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
    background: linear-gradient(180deg, #fff 0%, #fffcf7 100%) !important;
}

[data-testid="stExpander"] details summary p {
    color: var(--forest) !important;
    font-weight: 700 !important;
}

.stProgress > div {
    background: #e8eddc !important;
    border-radius: 999px !important;
}

.stProgress > div > div {
    background: linear-gradient(90deg, #7ea35f 0%, #5f8847 100%) !important;
    border-radius: 999px !important;
}

code {
    background: var(--gold-soft) !important;
    color: #5b4219 !important;
    border-radius: 7px !important;
    padding: 0.1rem 0.4rem !important;
    font-size: 0.76rem !important;
    border: 1px solid rgba(187, 130, 41, 0.24) !important;
}

div[data-testid="stMarkdownContainer"] hr {
    border: none !important;
    border-top: 1px solid var(--line) !important;
    margin: 1rem 0 !important;
}

.footer-text {
    text-align: center;
    color: var(--text-muted) !important;
    font-size: 0.74rem;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid var(--line);
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation: none !important;
        transition: none !important;
    }
}

@media (max-width: 768px) {
    .block-container {
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }

    [data-testid="stMetric"] {
        min-height: auto !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        min-height: 44px !important;
    }
}
</style>
"""
